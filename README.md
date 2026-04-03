# 🇮🇳 SchemeMatch Bharat

> **AI-powered civic platform** to help Indian citizens discover government schemes, scholarships, and welfare programs they are eligible for — powered by semantic search over 1500+ official government documents.

---

## 📁 Project Structure

```
Schematch-bharat/
├── data/
│   ├── schemes.json          ← Small hand-crafted scheme dataset (10 schemes)
│   ├── archive.zip           ← Full Kaggle dataset (1500+ schemes from all states)
│   └── chroma_db/            ← ChromaDB vector database (auto-created on load)
│
├── scripts/
│   ├── pdf_extractor.py      ← Extracts scheme data from PDF files → schemes.json
│   ├── db_loader.py          ← Loads schemes.json → ChromaDB
│   └── dataset_loader.py     ← Loads archive.zip (full Kaggle dataset) → ChromaDB
│
├── backend/
│   ├── main.py               ← FastAPI application (search API)
│   ├── requirements.txt      ← Python dependencies
│   └── .env.example          ← Backend environment config template
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
│   │       └── api.js        ← Points to backend at http://localhost:8000
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
└── README.md
```

---

## ⚙️ Prerequisites

| Tool    | Version | Install |
|---------|---------|---------|
| Python  | ≥ 3.9   | https://python.org (use the **official installer**, NOT the Windows Store version) |
| Node.js | ≥ 18    | https://nodejs.org |
| npm     | ≥ 9     | Included with Node.js |

> **Windows users:** Always use `py` instead of `python` in your terminal to avoid the Windows Store Python issue.

---

## 🚀 Setup & Run (Step-by-Step)

You need **two terminals open at the same time** — one for the backend, one for the frontend.

---

### Step 1 — Install Python dependencies

Open a terminal in your project root (`Schematch-bharat/`) and run:

```bash
pip install -r backend/requirements.txt
```

> If `pip` doesn't work, try `py -m pip install -r backend/requirements.txt`

---

### Step 2 — Load schemes into ChromaDB

This step populates the vector database. **You only need to do this once.**

**Option A — Full dataset (recommended, 1500+ schemes):**
```bash
py scripts/dataset_loader.py --zip_path ./data/archive.zip --db_path ./data/chroma_db --reset
```

**Option B — Small dataset (10 schemes, faster):**
```bash
py scripts/db_loader.py --schemes ./data/schemes.json --db_path ./data/chroma_db
```

Wait for it to finish. You should see:
```
[INFO] ChromaDB ready. Collection 'schemes' has 1520 records.
```

> The first run downloads the embedding model (~90 MB). Subsequent runs are instant.

---

### Step 3 — Start the backend (Terminal 1)

```bash
cd backend
py -m uvicorn main:app --reload --port 8000
```

You should see:
```
[INFO] Embedding model ready.
[INFO] ChromaDB ready. Collection 'schemes' has 1520 records.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Keep this terminal open.** The backend must stay running for the site to work.

Test it by visiting: http://localhost:8000/health

---

### Step 4 — Start the frontend (Terminal 2)

Open a **new terminal** in the project root:

```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE v8.x  ready in Xms
➜  Local:   http://localhost:3000/
```

---

### Step 5 — Open the website

Go to **http://localhost:3000** in your browser.

Type your situation in the search box, for example:
> *"I am a girl from Nagaland pursuing BTech. My family income is 5 lakhs per year."*

Click **Check Eligibility** and matching government schemes will appear.

---

## 🌐 How It Works

```
User types their situation
        │
        ▼
React Frontend (localhost:3000)
        │  POST /search { "query": "..." }
        ▼
FastAPI Backend (localhost:8000)
        │  1. Embeds query using SentenceTransformer (all-MiniLM-L6-v2)
        │  2. Runs cosine similarity search against ChromaDB
        │  3. Returns top-K matching schemes with relevance scores
        ▼
ChromaDB (local, persistent)
        │  Stores 384-dimensional vectors + scheme metadata
        ▼
Scheme cards rendered in the browser
```

---

## 🔍 API Reference

### `POST /search`
Find schemes matching a user's profile.

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
Returns API status and record count.

### `GET /schemes`
Returns all schemes stored in the database.

### Interactive API Docs
Visit http://localhost:8000/docs while the backend is running.

---

## ➕ Adding More Schemes

**Option A — Load from PDFs:**
```bash
# Place your PDF files in ./pdfs/
python scripts/pdf_extractor.py --pdf_dir ./pdfs --output ./data/schemes.json

# Reload the database
py scripts/db_loader.py --schemes ./data/schemes.json --db_path ./data/chroma_db --reset
```

**Option B — Edit `schemes.json` directly:**

Add a new entry in this format:
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

## 🛠️ Tech Stack

| Layer      | Technology |
|------------|------------|
| Frontend   | React 18 + Vite + Tailwind CSS |
| Backend    | FastAPI + Uvicorn |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector DB  | ChromaDB (persistent, local) |
| PDF Parse  | pdfplumber / PyMuPDF |

---

## 🔧 Troubleshooting

### "Could not reach the backend / Failed to fetch"
The backend is not running. Open a terminal and run:
```bash
cd backend
py -m uvicorn main:app --reload --port 8000
```
Keep this terminal open — **never close it while using the site.**

### "No module named uvicorn"
You're using the Windows Store Python. Use `py` instead of `python`:
```bash
py -m uvicorn main:app --reload --port 8000
```

### "Collection has 0 records"
The database was never loaded. Run from the project root:
```bash
py scripts/dataset_loader.py --zip_path ./data/archive.zip --db_path ./data/chroma_db --reset
```

### "Error loading ASGI app. Could not import module 'main'"
You're running uvicorn from the wrong folder. Make sure you `cd backend` first:
```bash
cd backend
py -m uvicorn main:app --reload --port 8000
```

### npm errors during `npm install`
Make sure you're in the `frontend/` folder, not `backend/`:
```bash
cd frontend
npm install
npm run dev
```

### Slow first search
Normal behaviour. The embedding model loads into memory on first startup (~5–10 seconds).

### Port already in use
```bash
# Windows — find and kill the process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📜 Data Sources

Scheme data is sourced from official Government of India documents across all states:

- Ministry of Social Justice & Empowerment (DEPwD)
- University Grants Commission (UGC)
- All India Council for Technical Education (AICTE)
- Ministry of Education, Government of India
- State government portals (all 28 states + UTs)

---

*Built for Indian citizens · Data from official government sources · Not affiliated with the Government of India*
