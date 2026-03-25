"""
db_loader.py
------------
Loads schemes.json, creates sentence embeddings for eligibility conditions,
and stores them in a persistent ChromaDB vector database.

Usage:
    python scripts/db_loader.py --schemes ./data/schemes.json --db_path ./data/chroma_db
"""

import json
import argparse
from pathlib import Path

# ChromaDB and sentence transformers
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    raise ImportError("Install ChromaDB: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("Install sentence-transformers: pip install sentence-transformers")


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"   # Fast, lightweight, good quality
COLLECTION_NAME = "schemes"


def load_schemes(path: str) -> list:
    """Load schemes from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        schemes = json.load(f)
    print(f"[INFO] Loaded {len(schemes)} schemes from {path}")
    return schemes


def build_document_text(scheme: dict) -> str:
    """
    Create a rich text string from a scheme for embedding.
    Combines scheme name + eligibility conditions for best semantic search.
    """
    parts = [f"Scheme: {scheme.get('scheme_name', '')}"]

    category = scheme.get("category", "")
    if category:
        parts.append(f"Category: {category}")

    eligibility = scheme.get("eligibility_conditions", [])
    if eligibility:
        parts.append("Eligibility: " + " | ".join(eligibility))

    return " ".join(parts)


def prepare_metadata(scheme: dict) -> dict:
    """
    Prepare metadata dict for ChromaDB storage.
    ChromaDB metadata values must be str, int, float, or bool.
    """
    docs = scheme.get("required_documents", [])
    financial = scheme.get("financial_assistance", {})

    # Serialize lists/dicts as JSON strings for ChromaDB
    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": scheme.get("scheme_name", ""),
        "category": scheme.get("category", "General"),
        "issuing_body": scheme.get("issuing_body", ""),
        "required_documents": json.dumps(docs),           # stored as JSON string
        "office_to_visit": scheme.get("office_to_visit", ""),
        "application_link": scheme.get("application_link", ""),
        "financial_assistance": json.dumps(financial),    # stored as JSON string
        "eligibility_conditions": json.dumps(
            scheme.get("eligibility_conditions", [])
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Load schemes into ChromaDB")
    parser.add_argument("--schemes", default="./data/schemes.json", help="Path to schemes.json")
    parser.add_argument("--db_path", default="./data/chroma_db", help="ChromaDB persistent directory")
    parser.add_argument("--reset", action="store_true", help="Reset the collection before loading")
    args = parser.parse_args()

    # ── Load schemes ──────────────────────────
    schemes = load_schemes(args.schemes)

    # ── Init ChromaDB (persistent) ────────────
    db_path = str(Path(args.db_path).resolve())
    Path(db_path).mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=db_path)
    print(f"[INFO] ChromaDB initialized at: {db_path}")

    # Reset collection if requested
    if args.reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[INFO] Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
    )

    # ── Load embedding model ──────────────────
    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL} ...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("[INFO] Model loaded.")

    # ── Build documents, embeddings, metadata ─
    doc_texts = []
    metadatas = []
    ids = []

    for scheme in schemes:
        scheme_id = scheme.get("scheme_id", f"scheme_{len(ids)}")
        doc_text = build_document_text(scheme)
        meta = prepare_metadata(scheme)

        doc_texts.append(doc_text)
        metadatas.append(meta)
        ids.append(scheme_id)

    # ── Create embeddings ─────────────────────
    print(f"[INFO] Creating embeddings for {len(doc_texts)} schemes...")
    embeddings = model.encode(doc_texts, show_progress_bar=True).tolist()

    # ── Upsert into ChromaDB ──────────────────
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=doc_texts,
        metadatas=metadatas,
    )

    print(f"\n[DONE] Stored {len(ids)} schemes in ChromaDB collection '{COLLECTION_NAME}'")
    print(f"[INFO] DB path: {db_path}")

    # ── Quick verification ────────────────────
    count = collection.count()
    print(f"[VERIFY] Collection now contains {count} records.")


if __name__ == "__main__":
    main()
