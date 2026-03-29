"""
dataset_loader.py
-----------------
Reads the Kaggle Indian Government Schemes dataset (archive.zip),
parses each text file, builds structured scheme records, and stores
them in ChromaDB for semantic search.

The dataset is organized as:
  archive.zip/
    central/central_doc_1.txt   ← Central government schemes
    andhra-pradesh/state_andhra-pradesh_doc_1.txt
    maharashtra/...
    ...

Each .txt file describes one or more schemes as a scraped article.

Usage:
    python scripts/dataset_loader.py \\
        --zip_path ./data/archive.zip \\
        --db_path ./data/chroma_db \\
        [--export_json ./data/schemes_kaggle.json] \\
        [--reset]
"""

import argparse
import json
import re
import zipfile
from pathlib import Path

try:
    import chromadb
except ImportError:
    raise ImportError("Install ChromaDB: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("Install sentence-transformers: pip install sentence-transformers")


# ────────────────────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "schemes"

# Known Indian state folder names in the dataset
STATE_MAP = {
    "andhra-pradesh": "Andhra Pradesh",
    "arunachal-pradesh": "Arunachal Pradesh",
    "assam": "Assam",
    "bihar": "Bihar",
    "chandigarh": "Chandigarh",
    "chhattisgarh": "Chhattisgarh",
    "delhi": "Delhi",
    "goa": "Goa",
    "gujarat": "Gujarat",
    "haryana": "Haryana",
    "himachal-pradesh": "Himachal Pradesh",
    "jammu-kashmir": "Jammu & Kashmir",
    "jharkhand": "Jharkhand",
    "karnataka": "Karnataka",
    "kerala": "Kerala",
    "madhya-pradesh": "Madhya Pradesh",
    "maharashtra": "Maharashtra",
    "manipur": "Manipur",
    "meghalaya": "Meghalaya",
    "mizoram": "Mizoram",
    "odisha": "Odisha",
    "punjab": "Punjab",
    "rajasthan": "Rajasthan",
    "tamilnadu": "Tamil Nadu",
    "telangana": "Telangana",
    "tripura": "Tripura",
    "uttar-pradesh": "Uttar Pradesh",
    "uttarakhand": "Uttarakhand",
    "west-bengal": "West Bengal",
    "central": "Central Government",
}


# ────────────────────────────────────────────────────────────────
# TEXT PARSING HELPERS
# ────────────────────────────────────────────────────────────────

def clean_text(raw: str) -> str:
    """Strip HTML artifacts, ad tags, and normalise whitespace."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    # Remove JS ad-push lines
    text = re.sub(r"\(adsbygoogle.*?\)\.push\(\{.*?\}\);?", "", text, flags=re.DOTALL)
    # Remove URLs (keep the scheme name, not the link)
    text = re.sub(r"https?://\S+", "", text)
    # Remove "SAVE AS PDF" footer
    text = re.sub(r"SAVE AS PDF", "", text, flags=re.IGNORECASE)
    # Remove isolated numbers (page numbers like "1\n")
    text = re.sub(r"^\d+\s*$", "", text, flags=re.MULTILINE)
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_scheme_name(lines: list[str]) -> str:
    """
    The scheme name is typically the first non-empty line of the document.
    Many files have the scheme name in the first 1-3 lines.
    """
    for line in lines:
        line = line.strip()
        if len(line) > 10 and not line.startswith("(") and not line.isdigit():
            # Remove common suffixes like "2020", "2021" in scheme names
            return line
    return "Unknown Scheme"


def extract_state_scope(folder: str) -> tuple[str, str]:
    """Return (state_label, issuing_body) for a folder name."""
    state = STATE_MAP.get(folder.lower(), folder.title())
    if folder.lower() == "central":
        issuing_body = "Central Government of India"
    else:
        issuing_body = f"{state} State Government"
    return state, issuing_body


def infer_category(text: str) -> str:
    """
    Guess a broad category from keywords in the document text.
    Returns one of a fixed set of categories.
    """
    text_lower = text.lower()
    category_keywords = {
        "Agriculture": ["farmer", "kisan", "crop", "agriculture", "agri", "shetkari",
                        "irrigation", "soil", "horticulture", "fisheries", "animal husbandry"],
        "Education": ["scholarship", "student", "school", "education", "tuition",
                      "college", "university", "vidya", "siksha", "book grant"],
        "Women & Children": ["women", "girl", "beti", "mahila", "child", "maternity",
                             "pregnant", "widow", "self-help group", "shg"],
        "Health": ["health", "hospital", "medical", "ayushman", "treatment",
                   "medicine", "disability", "pwd", "divyang"],
        "Housing": ["housing", "house", "ghar", "awas", "pucca", "shelter",
                    "pradhan mantri awas"],
        "Employment & Skill": ["employment", "job", "skill", "training", "apprentice",
                               "rozgar", "mudra", "startup", "entrepreneur", "msme"],
        "Social Welfare": ["pension", "old age", "senior citizen", "widow pension",
                           "bpl", "below poverty", "ration", "food security", "antyodaya"],
        "Finance & Banking": ["loan", "credit", "bank", "insurance", "kisan credit",
                              "mudra loan", "subsidy", "guarantee"],
        "Energy": ["solar", "energy", "electricity", "power", "ujjwala", "gas",
                   "lpg", "bio gas", "ujala"],
        "Infrastructure": ["road", "water", "sanitation", "toilet", "swachh",
                           "drinking water", "village", "panchayat"],
        "Disability": ["disability", "divyang", "pwd", "handicap", "blind",
                       "deaf", "differently abled", "udid"],
        "Minority & SC/ST": ["sc", "st", "obc", "scheduled caste", "scheduled tribe",
                             "minority", "dalit", "tribal", "adivasi"],
    }
    scores = {cat: 0 for cat in category_keywords}
    for cat, keywords in category_keywords.items():
        for kw in keywords:
            if kw in text_lower:
                scores[cat] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "General"


def extract_eligibility(text: str) -> list[str]:
    """
    Try to pull eligibility bullet points from the text.
    Looks for lists near 'eligib', 'criteria', 'who can'.
    Falls back to a generic sentence from the text.
    """
    lines = text.split("\n")
    in_eligibility = False
    conditions = []

    for i, line in enumerate(lines):
        line = line.strip()
        lower = line.lower()

        # Detect eligibility section header
        if any(k in lower for k in ["eligib", "who can", "criteria", "who is", "beneficiar"]):
            in_eligibility = True
            continue

        if in_eligibility:
            # Bullet-like or numbered lines become conditions
            if re.match(r"^[\-•✓*◆\d\.]", line) or (len(line) > 15 and len(line) < 200):
                clean = re.sub(r"^[\-•✓*◆\d\.]+\s*", "", line).strip()
                if clean:
                    conditions.append(clean)
            # Stop after 10 conditions or at a new section
            if len(conditions) >= 10 or (len(line) == 0 and len(conditions) > 0):
                if len(conditions) >= 2:
                    break

    if not conditions:
        # Fallback: first paragraph that looks like a description
        for line in lines:
            line = line.strip()
            if len(line) > 50:
                conditions = [line[:300]]
                break

    return conditions[:10] if conditions else ["See official scheme details"]


def parse_txt_file(content: str, folder: str, filename: str, doc_index: int) -> dict:
    """
    Parse a single .txt file into a structured scheme dict.
    """
    text = clean_text(content)
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    scheme_name = extract_scheme_name(lines)
    state, issuing_body = extract_state_scope(folder)
    category = infer_category(text)
    eligibility = extract_eligibility(text)

    # Build a unique scheme ID
    scheme_id = f"{folder.upper()[:3]}_{doc_index:04d}"

    # Full text for embedding (first 800 chars is usually enough)
    full_text = text[:800] if len(text) > 800 else text

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme_name,
        "state": state,
        "category": category,
        "issuing_body": issuing_body,
        "eligibility_conditions": eligibility,
        "required_documents": [],         # Not reliably extractable from this dataset
        "financial_assistance": {},       # Not reliably extractable
        "office_to_visit": f"{state} Government / Concerned Department",
        "application_link": "",
        "description": full_text,        # Full cleaned text for embedding
        "source_file": filename,
    }


# ────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ────────────────────────────────────────────────────────────────

def load_from_zip(zip_path: str) -> list[dict]:
    """
    Open archive.zip, iterate every .txt file, parse and return
    a list of scheme dicts.
    """
    schemes = []
    doc_counts: dict[str, int] = {}

    with zipfile.ZipFile(zip_path, "r") as zf:
        all_files = sorted(zf.namelist())
        txt_files = [f for f in all_files if f.endswith(".txt")]
        print(f"[INFO] Found {len(txt_files)} .txt files in {zip_path}")

        for filepath in txt_files:
            # filepath looks like  "andhra-pradesh/state_andhra-pradesh_doc_1.txt"
            parts = filepath.split("/")
            if len(parts) < 2:
                continue
            folder = parts[0]       # "andhra-pradesh"
            filename = parts[-1]    # "state_andhra-pradesh_doc_1.txt"

            try:
                raw_bytes = zf.read(filepath)
                content = raw_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                print(f"[WARN] Could not read {filepath}: {e}")
                continue

            # Skip very short files (< 100 chars) – likely empty or junk
            if len(content.strip()) < 100:
                continue

            doc_counts[folder] = doc_counts.get(folder, 0) + 1
            scheme = parse_txt_file(content, folder, filename, doc_counts[folder])
            schemes.append(scheme)

    print(f"[INFO] Parsed {len(schemes)} schemes across {len(doc_counts)} state/category folders")
    for folder, count in sorted(doc_counts.items()):
        print(f"       {folder}: {count} schemes")

    return schemes


def build_embedding_text(scheme: dict) -> str:
    """
    Create a rich semantic text for embedding.
    Combines name + category + state + description.
    """
    parts = [
        f"Scheme: {scheme.get('scheme_name', '')}",
        f"State: {scheme.get('state', '')}",
        f"Category: {scheme.get('category', '')}",
        f"Issuing Body: {scheme.get('issuing_body', '')}",
    ]

    eligibility = scheme.get("eligibility_conditions", [])
    if eligibility:
        parts.append("Eligibility: " + " | ".join(eligibility[:5]))

    description = scheme.get("description", "")
    if description:
        parts.append(description[:400])

    return " ".join(parts)


def prepare_metadata(scheme: dict) -> dict:
    """
    Flatten scheme dict for ChromaDB metadata storage.
    All values must be str, int, float, or bool.
    """
    return {
        "scheme_id": scheme.get("scheme_id", ""),
        "scheme_name": scheme.get("scheme_name", ""),
        "state": scheme.get("state", ""),
        "category": scheme.get("category", "General"),
        "issuing_body": scheme.get("issuing_body", ""),
        "eligibility_conditions": json.dumps(scheme.get("eligibility_conditions", [])),
        "required_documents": json.dumps(scheme.get("required_documents", [])),
        "financial_assistance": json.dumps(scheme.get("financial_assistance", {})),
        "office_to_visit": scheme.get("office_to_visit", ""),
        "application_link": scheme.get("application_link", ""),
        "description": scheme.get("description", "")[:500],  # cap at 500 chars
        "source_file": scheme.get("source_file", ""),
    }


def load_into_chromadb(schemes: list[dict], db_path: str, reset: bool = False):
    """Embed all schemes and store in ChromaDB."""
    Path(db_path).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(Path(db_path).resolve()))
    print(f"[INFO] ChromaDB at: {db_path}")

    if reset:
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"[INFO] Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL} ...")
    model = SentenceTransformer(EMBEDDING_MODEL)
    print("[INFO] Model loaded.")

    # Build texts, metadata, ids
    doc_texts, metadatas, ids = [], [], []
    seen_ids: set[str] = set()

    for scheme in schemes:
        sid = scheme.get("scheme_id", f"SCH_{len(ids)}")
        # Ensure unique IDs (de-dup)
        base_sid = sid
        suffix = 1
        while sid in seen_ids:
            sid = f"{base_sid}_{suffix}"
            suffix += 1
        seen_ids.add(sid)

        doc_texts.append(build_embedding_text(scheme))
        metadatas.append(prepare_metadata(scheme))
        ids.append(sid)

    print(f"[INFO] Embedding {len(doc_texts)} documents ...")
    # Batch in chunks of 256 to avoid memory issues
    batch_size = 256
    all_embeddings = []
    for i in range(0, len(doc_texts), batch_size):
        batch = doc_texts[i : i + batch_size]
        embs = model.encode(batch, show_progress_bar=True)
        all_embeddings.extend(embs.tolist())
        print(f"[INFO] Embedded {min(i + batch_size, len(doc_texts))} / {len(doc_texts)}")

    print("[INFO] Upserting into ChromaDB ...")
    # Upsert in batches
    for i in range(0, len(ids), batch_size):
        collection.upsert(
            ids=ids[i : i + batch_size],
            embeddings=all_embeddings[i : i + batch_size],
            documents=doc_texts[i : i + batch_size],
            metadatas=metadatas[i : i + batch_size],
        )

    count = collection.count()
    print(f"\n[DONE] ChromaDB collection '{COLLECTION_NAME}' now has {count} records.")


def main():
    parser = argparse.ArgumentParser(
        description="Load Kaggle Indian Gov Schemes dataset into ChromaDB"
    )
    parser.add_argument(
        "--zip_path",
        default="./data/archive.zip",
        help="Path to the Kaggle archive.zip file",
    )
    parser.add_argument(
        "--db_path",
        default="./data/chroma_db",
        help="ChromaDB persistent directory",
    )
    parser.add_argument(
        "--export_json",
        default="",
        help="(Optional) Also export parsed schemes to a JSON file",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing ChromaDB collection before loading",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Only load first N schemes (0 = all, useful for testing)",
    )
    args = parser.parse_args()

    # 1. Parse the zip
    schemes = load_from_zip(args.zip_path)

    if args.limit > 0:
        schemes = schemes[: args.limit]
        print(f"[INFO] Limiting to {len(schemes)} schemes (--limit flag)")

    # 2. Optionally export JSON
    if args.export_json:
        out_path = Path(args.export_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(schemes, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Exported {len(schemes)} schemes to {out_path}")

    # 3. Load into ChromaDB
    load_into_chromadb(schemes, args.db_path, reset=args.reset)


if __name__ == "__main__":
    main()
