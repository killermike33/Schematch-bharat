"""
main.py  –  SchemeMatch Bharat API
------------------------------------
FastAPI backend that:
  1. Accepts a POST /search with a user query string
  2. Extracts state / gender / category signals from the query
  3. Embeds the query with Sentence Transformers
  4. Searches ChromaDB for the top matching schemes
  5. Re-ranks results by boosting state-matched and central schemes
  6. Returns structured JSON results

Usage:
    cd backend
    uvicorn main:app --reload --port 8000
"""

import json
import os
import re
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    import chromadb
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(f"Missing dependency: {e}. Run: pip install -r requirements.txt")


# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
DB_PATH     = os.getenv("CHROMA_DB_PATH", str(Path(__file__).parent.parent / "data" / "chroma_db"))
COLLECTION  = "schemes"
EMBED_MODEL = "all-MiniLM-L6-v2"
TOP_K       = int(os.getenv("TOP_K", "5"))

# How many extra candidates to fetch before re-ranking
FETCH_MULTIPLIER = 4


# ──────────────────────────────────────────────────────────────
# STATE DETECTION MAP
# All Indian states + common alternate spellings / abbreviations
# ──────────────────────────────────────────────────────────────
STATE_ALIASES: dict[str, str] = {
    # Andhra Pradesh
    "andhra pradesh": "Andhra Pradesh", "andhra": "Andhra Pradesh", "ap": "Andhra Pradesh",
    # Arunachal Pradesh
    "arunachal pradesh": "Arunachal Pradesh", "arunachal": "Arunachal Pradesh",
    # Assam
    "assam": "Assam",
    # Bihar
    "bihar": "Bihar",
    # Chandigarh
    "chandigarh": "Chandigarh",
    # Chhattisgarh
    "chhattisgarh": "Chhattisgarh", "chattisgarh": "Chhattisgarh",
    # Delhi
    "delhi": "Delhi", "new delhi": "Delhi",
    # Goa
    "goa": "Goa",
    # Gujarat
    "gujarat": "Gujarat",
    # Haryana
    "haryana": "Haryana",
    # Himachal Pradesh
    "himachal pradesh": "Himachal Pradesh", "himachal": "Himachal Pradesh", "hp": "Himachal Pradesh",
    # Jammu & Kashmir
    "jammu and kashmir": "Jammu & Kashmir", "jammu kashmir": "Jammu & Kashmir",
    "jammu": "Jammu & Kashmir", "kashmir": "Jammu & Kashmir", "j&k": "Jammu & Kashmir",
    # Jharkhand
    "jharkhand": "Jharkhand",
    # Karnataka
    "karnataka": "Karnataka", "bangalore": "Karnataka", "bengaluru": "Karnataka",
    # Kerala
    "kerala": "Kerala",
    # Madhya Pradesh
    "madhya pradesh": "Madhya Pradesh", "mp": "Madhya Pradesh",
    # Maharashtra
    "maharashtra": "Maharashtra", "mumbai": "Maharashtra", "pune": "Maharashtra",
    "nagpur": "Maharashtra",
    # Manipur
    "manipur": "Manipur",
    # Meghalaya
    "meghalaya": "Meghalaya",
    # Mizoram
    "mizoram": "Mizoram",
    # Nagaland
    "nagaland": "Nagaland",
    # Odisha
    "odisha": "Odisha", "orissa": "Odisha",
    # Punjab
    "punjab": "Punjab",
    # Rajasthan
    "rajasthan": "Rajasthan",
    # Sikkim
    "sikkim": "Sikkim",
    # Tamil Nadu
    "tamil nadu": "Tamil Nadu", "tamilnadu": "Tamil Nadu", "tamil": "Tamil Nadu",
    "chennai": "Tamil Nadu",
    # Telangana
    "telangana": "Telangana", "hyderabad": "Telangana",
    # Tripura
    "tripura": "Tripura",
    # Uttar Pradesh
    "uttar pradesh": "Uttar Pradesh", "up": "Uttar Pradesh",
    # Uttarakhand
    "uttarakhand": "Uttarakhand", "uttaranchal": "Uttarakhand",
    # West Bengal
    "west bengal": "West Bengal", "bengal": "West Bengal", "kolkata": "West Bengal",
}

# Keywords that signal central/national schemes should be included
CENTRAL_KEYWORDS = {"central government", "central", "national", "india", "indian"}

# Gender keywords
FEMALE_KEYWORDS = {"girl", "woman", "women", "female", "lady", "ladies", "she", "her"}
MALE_KEYWORDS   = {"boy", "man", "men", "male", "he", "his"}

# Category keywords → category values stored in ChromaDB
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "scholarship":  ["scholarship", "scholarships", "study", "student", "education", "college", "university", "btech", "mbbs", "degree"],
    "disability":   ["disabled", "disability", "handicapped", "differently abled", "divyang"],
    "agriculture":  ["farmer", "farming", "agriculture", "kisan", "crop"],
    "health":       ["health", "hospital", "medical", "treatment", "medicine", "disease"],
    "housing":      ["house", "housing", "home", "shelter", "flat", "apartment"],
    "employment":   ["job", "employment", "unemployed", "work", "skill", "training", "apprentice"],
    "women":        ["women", "girl", "female", "maternity", "self help group", "shg"],
}


# ──────────────────────────────────────────────────────────────
# APP SETUP
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="SchemeMatch Bharat API",
    description="Find government schemes matching a citizen's profile",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# STARTUP
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


class SchemeResult(BaseModel):
    scheme_id: str
    scheme_name: str
    state: str = ""
    category: str
    issuing_body: str
    eligibility_conditions: List[str]
    required_documents: List[str]
    financial_assistance: dict
    office_to_visit: str
    application_link: str
    description: str = ""
    relevance_score: float


class SearchResponse(BaseModel):
    query: str
    total_results: int
    detected_state: Optional[str]
    results: List[SchemeResult]


# ──────────────────────────────────────────────────────────────
# QUERY ANALYSIS
# ──────────────────────────────────────────────────────────────
def extract_signals(query: str) -> dict:
    """
    Extract state, gender, and category signals from a free-text query.
    Returns a dict with keys: state, gender, categories
    """
    q = query.lower()

    # ── Detect state (try multi-word first, then single word) ──
    detected_state = None
    # Sort by length descending so "madhya pradesh" matches before "pradesh"
    for alias in sorted(STATE_ALIASES.keys(), key=len, reverse=True):
        if re.search(r'\b' + re.escape(alias) + r'\b', q):
            detected_state = STATE_ALIASES[alias]
            break

    # ── Detect gender ──
    words = set(q.split())
    gender = None
    if words & FEMALE_KEYWORDS:
        gender = "female"
    elif words & MALE_KEYWORDS:
        gender = "male"

    # ── Detect categories ──
    detected_categories = []
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            detected_categories.append(category)

    return {
        "state": detected_state,
        "gender": gender,
        "categories": detected_categories,
    }


def score_result(meta: dict, distance: float, signals: dict) -> float:
    """
    Compute a final relevance score combining:
    - Semantic similarity (from ChromaDB distance)
    - State match bonus
    - Central government bonus
    - Gender relevance bonus
    """
    # Base score: convert cosine distance to 0-1 similarity
    base_score = max(0.0, 1.0 - distance / 2.0)

    bonus = 0.0
    scheme_state = (meta.get("state") or "").lower()
    scheme_name  = (meta.get("scheme_name") or "").lower()
    scheme_cat   = (meta.get("category") or "").lower()

    detected_state = signals.get("state")
    gender         = signals.get("gender")

    # ── State match bonus ──
    if detected_state:
        if detected_state.lower() in scheme_state:
            bonus += 0.35          # strong boost for exact state match
        elif "central" in scheme_state or "central government" in scheme_state:
            bonus += 0.15          # moderate boost for central schemes (apply anywhere)

    # ── Gender bonus ──
    if gender == "female":
        female_signals = ["women", "girl", "female", "mahila", "pragati", "lady"]
        if any(sig in scheme_name or sig in scheme_cat for sig in female_signals):
            bonus += 0.10
    elif gender == "male":
        # Most schemes are gender-neutral, no specific boost needed
        pass

    # ── Category bonus ──
    for cat in signals.get("categories", []):
        if cat in scheme_cat or cat in scheme_name:
            bonus += 0.05

    return round(min(1.0, base_score + bonus), 4)


# ──────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────
def parse_json_field(value: str, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return fallback
    
def get_default_link(state: str) -> str:
    state_links = {
    "Rajasthan": "https://rajssp.raj.nic.in",
    "Maharashtra": "https://aaplesarkar.mahaonline.gov.in",
    "Karnataka": "https://sevasindhu.karnataka.gov.in",
    "Delhi": "https://edistrict.delhigovt.nic.in",
    "Central Government": "https://www.india.gov.in",
    }
    return state_links.get(state, "https://www.india.gov.in")


def metadata_to_result(meta: dict, final_score: float) -> SchemeResult:
    return SchemeResult(
        scheme_id=meta.get("scheme_id", ""),
        scheme_name=meta.get("scheme_name", ""),
        state=meta.get("state", ""),
        category=meta.get("category", "General"),
        issuing_body=meta.get("issuing_body", ""),
        eligibility_conditions=parse_json_field(meta.get("eligibility_conditions", ""), []),
        required_documents=parse_json_field(meta.get("required_documents", ""), []),
        financial_assistance=parse_json_field(meta.get("financial_assistance", ""), {}),
        office_to_visit=meta.get("office_to_visit", ""),
        application_link=meta.get("application_link") or get_default_link(meta.get("state")),
        description=meta.get("description", ""),
        relevance_score=final_score,
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
    Detects state/gender/category from the query, fetches extra candidates,
    re-ranks with bonuses, and returns top-K results.
    """
    if not request.query or len(request.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters")

    if model is None or collection is None:
        raise HTTPException(status_code=503, detail="Service not ready. Please try again shortly.")

    top_k = min(max(1, request.top_k or TOP_K), 10)

    # ── Analyse the query ────────────────────
    signals = extract_signals(request.query)
    print(f"[INFO] Detected signals: {signals}")

    # ── Embed the query ──────────────────────
    query_embedding = model.encode(request.query.strip()).tolist()

    # Fetch more candidates than needed so re-ranking has room to work
    fetch_k = min(top_k * FETCH_MULTIPLIER, collection.count())

    # ── Search ChromaDB ──────────────────────
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        include=["metadatas", "distances"],
    )

    metadatas = results.get("metadatas", [[]])[0]
    distances  = results.get("distances", [[]])[0]

    # ── Re-rank with signal bonuses ──────────
    scored = []
    for meta, dist in zip(metadatas, distances):
        final_score = score_result(meta, dist, signals)
        scored.append((meta, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top_results = scored[:top_k]

    scheme_results = [metadata_to_result(meta, score) for meta, score in top_results]

    return SearchResponse(
        query=request.query,
        total_results=len(scheme_results),
        detected_state=signals.get("state"),
        results=scheme_results,
    )


@app.get("/schemes", response_model=List[dict])
def list_all_schemes():
    if collection is None:
        raise HTTPException(status_code=503, detail="Database not ready")

    results = collection.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])

    return [
        {
            "scheme_id": meta.get("scheme_id", ""),
            "scheme_name": meta.get("scheme_name", ""),
            "category": meta.get("category", ""),
            "issuing_body": meta.get("issuing_body", ""),
            "application_link": meta.get("application_link", ""),
        }
        for meta in metadatas
    ]