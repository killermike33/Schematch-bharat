"""
main.py  –  SchemeMatch Bharat API
------------------------------------
FastAPI backend that:
  1. Accepts a POST /search with a user query string
  2. Embeds the query with Sentence Transformers
  3. Searches ChromaDB for the top matching schemes
  4. Returns structured JSON results

Usage:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Lazy-import heavy libraries so startup is fast ──
try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}. Run: pip install -r requirements.txt")


# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
DB_PATH        = os.getenv("CHROMA_DB_PATH", str(Path(__file__).parent.parent / "data" / "chroma_db"))
COLLECTION     = "schemes"
EMBED_MODEL    = "all-MiniLM-L6-v2"
TOP_K          = int(os.getenv("TOP_K", "5"))   # how many results to return

# ──────────────────────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="SchemeMatch Bharat API",
    description="Find government schemes matching a citizen's profile",
    version="1.0.0",
)

# Allow React dev-server and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# STARTUP: load model + DB once
# ──────────────────────────────────────────────────────────────
model: Optional[SentenceTransformer] = None
collection = None

@app.on_event("startup")
def startup():
    global model, collection

    print("[INFO] Loading embedding model...")
    model = SentenceTransformer(EMBED_MODEL)
    print("[INFO] Embedding model ready.")

    print(f"[INFO] Connecting to ChromaDB at {DB_PATH} ...")
    client = chromadb.PersistentClient(path=DB_PATH)
    collection = client.get_or_create_collection(COLLECTION)
    count = collection.count()
    print(f"[INFO] ChromaDB ready. Collection '{COLLECTION}' has {count} records.")


# ──────────────────────────────────────────────────────────────
# PYDANTIC MODELS
# ──────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = TOP_K


class FinancialAssistance(BaseModel):
    key: str
    value: str


class SchemeResult(BaseModel):
    scheme_id: str
    scheme_name: str
    category: str
    issuing_body: str
    eligibility_conditions: List[str]
    required_documents: List[str]
    financial_assistance: dict
    office_to_visit: str
    application_link: str
    relevance_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SchemeResult]


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def parse_json_field(value: str, fallback):
    """Safely parse a JSON-serialized string field from ChromaDB metadata."""
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback


def metadata_to_result(meta: dict, distance: float) -> SchemeResult:
    """Convert ChromaDB metadata dict → SchemeResult."""
    # ChromaDB returns cosine distance (0=identical, 2=opposite)
    # Convert to a 0–1 relevance score
    relevance = round(max(0.0, 1.0 - distance / 2.0), 4)

    return SchemeResult(
        scheme_id=meta.get("scheme_id", ""),
        scheme_name=meta.get("scheme_name", ""),
        category=meta.get("category", "General"),
        issuing_body=meta.get("issuing_body", ""),
        eligibility_conditions=parse_json_field(
            meta.get("eligibility_conditions", ""), []
        ),
        required_documents=parse_json_field(
            meta.get("required_documents", ""), []
        ),
        financial_assistance=parse_json_field(
            meta.get("financial_assistance", ""), {}
        ),
        office_to_visit=meta.get("office_to_visit", ""),
        application_link=meta.get("application_link", ""),
        relevance_score=relevance,
    )


# ──────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "SchemeMatch Bharat API is running",
        "docs": "/docs",
        "search_endpoint": "POST /search",
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "db_connected": collection is not None,
        "scheme_count": collection.count() if collection else 0,
    }


@app.post("/search", response_model=SearchResponse)
def search_schemes(request: SearchRequest):
    """
    Main search endpoint.
    Accepts a natural-language user query, returns ranked matching schemes.
    """
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")

    if model is None or collection is None:
        raise HTTPException(status_code=503, detail="Service not ready. Please try again shortly.")

    top_k = min(max(1, request.top_k or TOP_K), 10)  # clamp 1–10

    # ── Embed the query ──────────────────────
    query_embedding = model.encode(request.query.strip()).tolist()

    # ── Search ChromaDB ──────────────────────
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "distances"],
    )

    # ── Parse results ────────────────────────
    metadatas = results.get("metadatas", [[]])[0]
    distances  = results.get("distances", [[]])[0]

    scheme_results = []
    for meta, dist in zip(metadatas, distances):
        scheme_results.append(metadata_to_result(meta, dist))

    return SearchResponse(
        query=request.query,
        total_results=len(scheme_results),
        results=scheme_results,
    )


@app.get("/schemes", response_model=List[dict])
def list_all_schemes():
    """
    Return all schemes stored in the database (without embeddings).
    Useful for browsing all available schemes.
    """
    if collection is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])

    schemes = []
    for meta in metadatas:
        schemes.append({
            "scheme_id": meta.get("scheme_id", ""),
            "scheme_name": meta.get("scheme_name", ""),
            "category": meta.get("category", ""),
            "issuing_body": meta.get("issuing_body", ""),
            "application_link": meta.get("application_link", ""),
        })

    return schemes
