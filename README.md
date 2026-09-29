# AI-Driven Policy-to-Patient Intelligence & Treatment Cost Estimation Engine

A hackathon MVP demonstrating an end-to-end flow from **insurance policy PDF upload** → **RAG-powered Q&A with citations** → **treatment cost estimation**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (:3000)                        │
│  (Vite + Tailwind CSS)                                          │
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐    │
│  │ Upload   │  │ Policy Q&A   │  │ Treatment Cost         │    │
│  │ PDF      │  │ (Chat + RAG) │  │ Estimator              │    │
│  └────┬─────┘  └──────┬───────┘  └───────────┬────────────┘    │
└───────┼───────────────┼──────────────────────┼──────────────────┘
        │ Vite proxy    │                      │
        ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FASTAPI BACKEND (:8000)                      │
│                                                                  │
│  POST /api/policies/upload  → PyMuPDF extract → FAISS index     │
│  GET  /api/policies         → list policies                      │
│  GET  /api/policies/{id}    → policy detail                      │
│  POST /api/chat             → FAISS search → Gemini LLM → ans  │
│  POST /api/treatment/est.   → JSON lookup → cost breakdown      │
│  GET  /api/treatment/catalog→ list treatments                    │
│                                                                  │
│  services/                                                       │
│    pdf_service.py   – PyMuPDF page-aware text extraction         │
│    rag_service.py   – FAISS + sentence-transformers + Gemini     │
│    cost_service.py  – JSON lookup + simple insurance math        │
│  data/                                                           │
│    treatment_costs.json – synthetic cost catalog (18 procedures) │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
insurance-backend/
├── main.py                        # Entry point (python main.py)
├── requirements.txt
├── .env.example                   # GEMINI_API_KEY placeholder
├── uploads/                       # Uploaded PDFs (auto-created)
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory + /health
│   ├── models.py                  # Pydantic request/response models
│   ├── store.py                   # In-memory data store
│   ├── routes/
│   │   ├── policies.py            # Upload, list, detail
│   │   ├── chat.py                # RAG-powered Q&A
│   │   └── treatment.py           # Cost estimation + catalog
│   ├── services/
│   │   ├── pdf_service.py         # PyMuPDF text extraction + chunking
│   │   ├── rag_service.py         # FAISS index + Gemini LLM
│   │   └── cost_service.py        # Treatment cost lookup & estimation
│   └── data/
│       └── treatment_costs.json   # Synthetic treatment costs
└── frontend/
    ├── package.json
    ├── vite.config.js             # Dev server + proxy to backend
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── index.css
        ├── App.jsx                # Tab-based layout
        ├── services/
        │   └── api.js             # Axios API client
        └── components/
            ├── PolicyUpload.jsx   # Upload + policy selection
            ├── PolicyChat.jsx     # Q&A chat with citations
            └── CostEstimator.jsx  # Treatment cost breakdown
```

---

## Quick Start

### 1. Backend

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Set up Gemini API key for LLM answers
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
# Without it, RAG still works but returns retrieved chunks without LLM synthesis

# Run the backend
uvicorn app.main:app --reload
```

Backend runs at **http://localhost:8000** (Swagger docs at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:3000** (proxies API calls to backend).

---

## Primary Policy RAG API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/policy/upload` | Upload PDF → PyMuPDF extract (page + section) → chunk → FAISS index |
| `POST` | `/api/policy/ask` | Ask question (`{"question": "..."}`) → retrieve evidence → LLM grounded answer with page/section citations |
| `GET` | `/api/policy/active` | Get active policy status & metadata |

## Full Endpoints List

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/policy/upload` | Upload and index policy PDF (active document) |
| `POST` | `/api/policy/ask` | Query active policy with citations and confidence |
| `GET` | `/api/policy/active` | Current active policy status |
| `POST` | `/api/policies/upload` | Multi-policy upload (compatible) |
| `GET` | `/api/policies` | List all uploaded policies |
| `GET` | `/api/policies/{policy_id}` | Policy detail |
| `POST` | `/api/chat` | Ask policy question (compatible) |
| `POST` | `/api/treatment/estimate` | Treatment cost → coverage breakdown |
| `GET` | `/api/treatment/catalog` | List all treatments in catalog |

---

## How It Works

1. **Upload** a PDF insurance policy → PyMuPDF extracts text page-by-page → text is split into ~500-char chunks with overlap
2. **Index** — chunks are embedded with `all-MiniLM-L6-v2` (sentence-transformers) and stored in a FAISS vector index
3. **Ask a question** → question is embedded → top-3 similar chunks retrieved from FAISS → context + question sent to Google Gemini → answer returned with page-number citations
4. **Estimate cost** → select a treatment from the catalog → system looks up average cost from synthetic data → applies simple deductible/copay/max-OOP rules → shows insurance vs. out-of-pocket breakdown

---

## Notes

- **Hackathon MVP** — in-memory store, no persistence across restarts
- **No API key needed** to demo — without `GEMINI_API_KEY`, the chat endpoint still returns retrieved context chunks (just no LLM synthesis)
- **18 synthetic treatments** in the cost catalog with realistic CPT codes and price ranges
- **CORS** is wide-open for local development
