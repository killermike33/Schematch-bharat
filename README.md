# 🇮🇳 SchemeMatch Bharat

> **AI-powered civic platform** to help Indian citizens find government schemes, scholarships, and fellowships they are eligible for.

---

## 📁 Folder Structure

```
schematch-bharat/
├── data/
│   ├── schemes.json          ← Extracted scheme data (pre-filled from PDFs)
│   └── chroma_db/            ← ChromaDB vector database (auto-created)
│
├── scripts/
│   ├── pdf_extractor.py      ← Reads PDFs → produces schemes.json
│   └── db_loader.py          ← Loads schemes.json → ChromaDB
│
├── backend/
│   ├── main.py               ← FastAPI application
│   ├── requirements.txt      ← Python dependencies
│   └── .env.example          ← Backend config template
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── Hero.jsx
│   │   │   ├── SearchBox.jsx
│   │   │   ├── SchemeCard.jsx
│   │   │   ├── ResultsPanel.jsx
│   │   │   └── Footer.jsx
│   │   └── services/
│   │       └── api.js
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── .env.example
│
└── README.md
```

---

## 🚀 Quick Start (Step-by-Step)

### Prerequisites

| Tool    | Version   | Install                          |
|---------|-----------|----------------------------------|
| Python  | ≥ 3.9     | https://python.org               |
| Node.js | ≥ 18      | https://nodejs.org               |
| npm     | ≥ 9       | Included with Node.js            |

---

### Step 1 — Clone / Extract the project

```bash
# Navigate to the project folder
cd schematch-bharat
```

---

### Step 2 — Set up the Python backend

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install all Python dependencies
pip install -r backend/requirements.txt
```

---

### Step 3 — (Optional) Extract your own PDFs

> **Skip this step** if you want to use the pre-filled `data/schemes.json`.

```bash
# Place your PDF files in a folder, e.g. ./pdfs/
mkdir pdfs
# Copy your PDF files there...

# Run the extractor
python scripts/pdf_extractor.py --pdf_dir ./pdfs --output ./data/schemes.json
```

---

### Step 4 — Load schemes into ChromaDB

This creates the vector database used for semantic search.

```bash
 \
  --schemes ./data/schemes.json \
  --db_path ./data/chroma_db
```

Expected output:
```
[INFO] Loaded 10 schemes from ./data/schemes.json
[INFO] ChromaDB initialized at: .../data/chroma_db
[INFO] Loading embedding model: all-MiniLM-L6-v2 ...
[INFO] Model loaded.
[INFO] Creating embeddings for 10 schemes...
[DONE] Stored 10 schemes in ChromaDB collection 'schemes'
[VERIFY] Collection now contains 10 records.
```

> **Note:** The first run downloads the embedding model (~90 MB). Subsequent runs are instant.

---

### Step 5 — Start the FastAPI backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Test it:
```bash
curl http://localhost:8000/health
# → {"status":"ok","model_loaded":true,"db_connected":true,"scheme_count":10}
```

Interactive API docs: http://localhost:8000/docs

---

### Step 6 — Start the React frontend

Open a **new terminal**:

```bash
cd frontend

# Install npm packages
npm install

# Start development server
npm run dev
```

Open your browser: **http://localhost:3000**

---

## 🌐 How It Works

```
User Query
    │
    ▼
React Frontend (port 3000)
    │  POST /api/search  { "query": "..." }
    ▼
FastAPI Backend (port 8000)
    │  1. Embed query with SentenceTransformer
    │  2. Query ChromaDB (cosine similarity)
    │  3. Return top-K matched schemes
    ▼
ChromaDB (local)
    │  Stores 384-dim vectors + metadata
    ▼
JSON Response → SchemeCards rendered
```

---

## 🔍 API Reference

### `POST /search`

Find matching schemes for a user's situation.

**Request:**
```json
{
  "query": "I am a girl student from Nagaland pursuing BTech. Family income 3 lakh.",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "...",
  "total_results": 5,
  "results": [
    {
      "scheme_id": "SCH009",
      "scheme_name": "AICTE Pragati Scholarship for Girl Students",
      "category": "Women/Girls",
      "issuing_body": "AICTE",
      "eligibility_conditions": ["..."],
      "required_documents": ["..."],
      "financial_assistance": { "scholarship": "Rs. 50,000/year" },
      "office_to_visit": "...",
      "application_link": "https://www.scholarships.gov.in",
      "relevance_score": 0.87
    }
  ]
}
```

### `GET /health`
Returns API and database status.

### `GET /schemes`
Returns all schemes in the database.

---

## ➕ Adding More Schemes

**Option A — Add PDFs** (automatic extraction):
```bash
# Add new PDFs to ./pdfs/
python scripts/pdf_extractor.py --pdf_dir ./pdfs --output ./data/schemes.json

# Reload the database (use --reset to clear old data)
python scripts/db_loader.py --schemes ./data/schemes.json --db_path ./data/chroma_db --reset
```

**Option B — Edit `schemes.json` directly:**
Add a new entry following this structure:
```json
{
  "scheme_id": "SCH011",
  "scheme_name": "Name of Scheme",
  "category": "Category",
  "issuing_body": "Ministry / Department",
  "eligibility_conditions": ["Condition 1", "Condition 2"],
  "required_documents": ["Document 1", "Document 2"],
  "financial_assistance": { "amount": "Rs. X per year" },
  "office_to_visit": "Office address",
  "application_link": "https://..."
}
```
Then re-run `db_loader.py`.

---

## 🏗️ Schemes Included (v1.0)

| # | Scheme Name | Category |
|---|-------------|----------|
| 1 | Pre-Matric Scholarship for Students with Disabilities | Disability |
| 2 | Post-Matric Scholarship for Students with Disabilities | Disability |
| 3 | Top Class Education Scholarship (Disability) | Disability |
| 4 | National Overseas Scholarship (Disability) | Disability |
| 5 | National Fellowship for Persons with Disabilities | Disability |
| 6 | Free Coaching Scholarship (Disability) | Disability |
| 7 | Top Class Education – OBC/EBC/DNT Students | OBC/EBC/DNT |
| 8 | Ishan Uday – North Eastern Region | NER Students |
| 9 | AICTE Pragati Scholarship for Girl Students | Women/Girls |
| 10 | PM-USP Central Sector Scheme (CSSS) | Merit-Based |

---

## 🛠️ Tech Stack

| Layer     | Technology                        |
|-----------|-----------------------------------|
| Frontend  | React 18 + Vite + Tailwind CSS    |
| Backend   | FastAPI + Uvicorn                 |
| Embeddings| Sentence Transformers (MiniLM)    |
| Vector DB | ChromaDB (persistent, local)      |
| PDF Parse | pdfplumber / PyMuPDF              |

---

## 🔧 Troubleshooting

**"Cannot connect to server"**
→ Make sure `uvicorn main:app --reload --port 8000` is running in the `backend/` folder.

**"Collection has 0 records"**
→ Run `db_loader.py` again. Check that `data/schemes.json` exists and has entries.

**Slow first search**
→ Normal. The embedding model is loaded into memory on first startup.

**CORS errors in browser**
→ The Vite proxy (`/api` → `localhost:8000`) handles this. Do not call port 8000 directly from the frontend.

**Port 3000 or 8000 already in use**
```bash
# Kill whatever is on that port (macOS/Linux)
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

---

## 📜 Data Sources

All scheme data is extracted from **official Government of India documents**:

- Ministry of Social Justice & Empowerment (DEPwD)
- University Grants Commission (UGC)
- All India Council for Technical Education (AICTE)
- Ministry of Education, Government of India

---

*Built for Indian citizens · Data from official government sources · Not affiliated with the Government of India*
