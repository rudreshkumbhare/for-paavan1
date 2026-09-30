# AI-Driven Policy-to-Patient Intelligence & Treatment Cost Estimation Engine

A hackathon MVP demonstrating an end-to-end flow from **insurance policy PDF upload → RAG-powered Q&A with citations → treatment cost estimation**.

---

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                    REACT FRONTEND (:3000)                       │
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
│                     FASTAPI BACKEND (:8000)                     │
│                                                                 │
│  POST /api/policies/upload  → PyMuPDF extract → FAISS index    │
│  GET  /api/policies         → list policies                    │
│  GET  /api/policies/{id}    → policy detail                    │
│  POST /api/chat             → FAISS search → Gemini LLM → ans  │
│  POST /api/treatment/est.   → JSON lookup → cost breakdown      │
│  GET  /api/treatment/catalog→ list treatments                  │
│                                                                 │
│  services/                                                       │
│    pdf_service.py   – PyMuPDF page-aware text extraction        │
│    rag_service.py   – FAISS + sentence-transformers + Gemini    │
│    cost_service.py  – JSON lookup + simple insurance math       │
│                                                                 │
│  data/                                                           │
│    treatment_costs.json – synthetic cost catalog (18 procedures)│
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

Before running the project, make sure you have the following installed:

- **Python:** 3.12 or newer
- **Node.js:** 18.0 or newer
- **Git**
- A **64-bit Python installation** is recommended

Python 3.14 has been tested with the current dependency configuration.

You can verify your installed versions with:

```bash
python --version
node --version
npm --version
```

---

# Step-by-Step Setup Guide

## 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

---

# Backend Setup

## Windows

Open PowerShell or Command Prompt in the project directory.

### 1. Create a virtual environment

```powershell
python -m venv .venv
```

### 2. Activate the virtual environment

**PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Command Prompt:**

```cmd
.venv\Scripts\activate.bat
```

If PowerShell blocks script execution, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again.

### 3. Verify Python

```powershell
python --version
```

Python 3.12 or newer should be displayed.

### 4. Upgrade pip and build tools

```powershell
python -m pip install --upgrade pip setuptools wheel
```

### 5. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 6. Configure Gemini API key (Optional)

The application can run without a Gemini API key. Without it, the RAG system can still return retrieved context, but Gemini will not generate the final synthesized answer.

Copy the example environment file:

```powershell
copy .env.example .env
```

Then edit `.env` and add:

```env
GEMINI_API_KEY=your_api_key_here
```

> Do not commit your `.env` file to Git.

### 7. Start the backend

If `main.py` is the application entry point:

```powershell
python main.py
```

Alternatively:

```powershell
python -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

Interactive Swagger API documentation:

```text
http://localhost:8000/docs
```

---

## macOS / Linux

### 1. Create a virtual environment

```bash
python3 -m venv .venv
```

### 2. Activate the environment

```bash
source .venv/bin/activate
```

### 3. Verify Python

```bash
python --version
```

Python 3.12 or newer should be displayed.

### 4. Upgrade pip and build tools

```bash
python -m pip install --upgrade pip setuptools wheel
```

### 5. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Configure Gemini API key (Optional)

```bash
cp .env.example .env
```

Then add your API key to `.env`:

```env
GEMINI_API_KEY=your_api_key_here
```

### 7. Start the backend

```bash
python -m uvicorn app.main:app --reload
```

The backend will run at:

```text
http://localhost:8000
```

Interactive Swagger API documentation:

```text
http://localhost:8000/docs
```

---

# Frontend Setup

Open a new terminal window while keeping the backend running.

Navigate to the frontend directory:

```bash
cd frontend
```

Install the Node.js dependencies:

```bash
npm install
```

Start the Vite development server:

```bash
npm run dev
```

The frontend will run at:

```text
http://localhost:3000
```

The Vite development server automatically proxies API requests to the FastAPI backend running on port 8000.

---

# Verify Backend Installation

Make sure the backend virtual environment is activated, then run:

```bash
python -c "import fitz, fastapi, uvicorn, faiss, numpy, sentence_transformers, dotenv; print('All dependencies loaded successfully!')"
```

Expected output:

```text
All dependencies loaded successfully!
```

You can also check the installed NumPy version:

```bash
python -c "import numpy; print('NumPy:', numpy.__version__)"
```

---

# Primary Policy RAG API

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/policy/upload` | Upload PDF → extract text → chunk → create FAISS index |
| `POST` | `/api/policy/ask` | Ask a question → retrieve evidence → generate grounded answer with citations |
| `GET` | `/api/policy/active` | Get active policy status and metadata |

---

# Full API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/policy/upload` | Upload and index policy PDF |
| `POST` | `/api/policy/ask` | Query active policy with citations and confidence |
| `GET` | `/api/policy/active` | Get current active policy status |
| `POST` | `/api/policies/upload` | Multi-policy upload |
| `GET` | `/api/policies` | List all uploaded policies |
| `GET` | `/api/policies/{policy_id}` | Get policy details |
| `POST` | `/api/chat` | Ask policy questions |
| `POST` | `/api/treatment/estimate` | Estimate treatment cost and coverage |
| `GET` | `/api/treatment/catalog` | List available treatments |

---

# How It Works

## 1. Upload Policy

A user uploads an insurance policy PDF.

PyMuPDF extracts the text page-by-page while preserving page information.

The extracted text is divided into approximately **500-character chunks with overlap**.

---

## 2. Create Vector Index

Each text chunk is converted into an embedding using:

```text
all-MiniLM-L6-v2
```

The resulting embeddings are stored in a FAISS vector index for semantic search.

---

## 3. Ask a Policy Question

When a user asks a question:

1. The question is converted into an embedding.
2. FAISS searches for the most relevant policy chunks.
3. The top relevant chunks are retrieved.
4. The retrieved context and question are sent to Google Gemini when an API key is configured.
5. Gemini generates a grounded answer.
6. The response includes page/section citations where available.

---

## 4. Estimate Treatment Cost

The treatment estimator:

- Receives a selected treatment.
- Looks up its cost in the synthetic treatment catalog.
- Applies simplified insurance rules such as:
  - Deductible
  - Copay
  - Maximum out-of-pocket
- Produces an estimated insurance-covered amount and patient out-of-pocket amount.

> **Important:** The treatment prices and insurance calculations are synthetic and intended only for demonstration purposes.

---

# Environment Variables

Create a `.env` file in the project root if you want to enable Gemini-generated answers.

```env
GEMINI_API_KEY=your_api_key_here
```

The Gemini API key is optional.

Without a key, the application can still demonstrate document retrieval and return relevant policy context.

---

# Project Notes

- **Hackathon MVP** — designed for demonstration rather than production use.
- **In-memory storage** — uploaded policies and FAISS indexes are not persisted across application restarts unless persistence is implemented separately.
- **Synthetic treatment data** — the treatment cost catalog contains 18 synthetic procedures.
- **No Gemini API key required for basic RAG retrieval** — Gemini is only required for LLM-generated responses.
- **CORS** is intentionally wide-open for local development.
- The project uses **NumPy 2.x** to support the current Python environment.
- **Python 3.14** has been tested with the current dependency configuration.

---

# Troubleshooting

## NumPy Installation Fails

If NumPy installation fails during dependency installation, first verify your Python version:

```bash
python --version
```

Then make sure pip is up to date:

```bash
python -m pip install --upgrade pip setuptools wheel
```

Recreate the virtual environment if necessary.

### Windows

```powershell
deactivate
Remove-Item -Recurse -Force .venv

python -m venv .venv
.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### macOS / Linux

```bash
deactivate
rm -rf .venv

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

---

## PowerShell Cannot Activate the Virtual Environment

Run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then:

```powershell
.venv\Scripts\Activate.ps1
```

---

## Check That the Virtual Environment Is Active

Your terminal should normally show:

```text
(.venv)
```

You can also check the Python executable:

```bash
python -c "import sys; print(sys.executable)"
```

The output should point to the project's `.venv` directory.

---

# Development Status

This project is a **hackathon MVP** demonstrating the concept of combining:

- Insurance policy document processing
- Retrieval-Augmented Generation (RAG)
- Semantic search
- Large Language Models
- Policy citations
- Treatment cost estimation
- Insurance coverage calculations

It is not intended to provide real medical, insurance, financial, or legal advice.