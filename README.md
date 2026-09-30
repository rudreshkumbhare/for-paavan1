# AI-Driven Policy-to-Patient Intelligence & Treatment Cost Estimation Engine

A hackathon MVP demonstrating an end-to-end flow from **insurance policy PDF upload → semantic retrieval → grounded AI-powered policy Q&A with citations → treatment cost estimation → coverage and out-of-pocket analysis**.

The system combines:

- PDF document processing
- Page-aware text extraction
- Semantic search with embeddings
- FAISS vector retrieval
- Gemini as the primary LLM
- Groq as an LLM fallback
- Grounded policy answers with citations
- Deterministic treatment-cost and coverage calculations
- Synthetic treatment-cost data

> **Hackathon MVP:** This project is designed for demonstration and prototyping, not production insurance claim processing or real-world medical/financial decision-making.

---

## Architecture

    ┌────────────────────────────────────────────────────────────────────┐
    │                     REACT FRONTEND (:3000)                         │
    │                    Vite + Tailwind CSS                             │
    │                                                                    │
    │  ┌────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
    │  │ Policy PDF │  │ Policy Q&A     │  │ Treatment Cost         │   │
    │  │ Upload     │  │ Chat + RAG     │  │ Estimator              │   │
    │  └─────┬──────┘  └───────┬────────┘  └───────────┬────────────┘   │
    └────────┼──────────────────┼───────────────────────┼────────────────┘
             │                  │                       │
             ▼                  ▼                       ▼
    ┌────────────────────────────────────────────────────────────────────┐
    │                      FASTAPI BACKEND (:8000)                       │
    │                                                                    │
    │  Policy Processing                                                 │
    │  ─────────────────                                                 │
    │  PDF Upload → PyMuPDF → Page-Aware Chunks → Embeddings → FAISS   │
    │                                                                    │
    │  Policy Q&A / RAG                                                  │
    │  ─────────────────                                                 │
    │  User Question → FAISS Retrieval → Relevant Policy Evidence       │
    │                                      │                             │
    │                         ┌────────────┴────────────┐                │
    │                         ▼                         ▼                │
    │                   Gemini LLM                Groq Fallback          │
    │                         │                         │                │
    │                         └────────────┬────────────┘                │
    │                                      ▼                             │
    │                         Grounded Answer +                           │
    │                         Citations + Confidence                      │
    │                                                                    │
    │  Treatment Cost Intelligence                                      │
    │  ────────────────────────────                                      │
    │  Treatment + City + Hospital Type → Synthetic Cost Catalog        │
    │                                      │                             │
    │                                      ▼                             │
    │                           Deterministic Coverage Engine            │
    │                                      │                             │
    │                                      ▼                             │
    │                         Coverage + Out-of-Pocket Cost              │
    │                                                                    │
    │  services/                                                         │
    │    pdf_service.py   – PDF text extraction and page-aware chunks   │
    │    rag_service.py   – FAISS retrieval + Gemini/Groq LLMs          │
    │    cost_service.py  – Treatment lookup + deterministic math       │
    │                                                                    │
    │  data/                                                             │
    │    treatment_costs.json – Synthetic treatment cost catalog         │
    └────────────────────────────────────────────────────────────────────┘

---

## Prerequisites

Before running the project, make sure you have the following installed:

- **Python:** 3.12 or newer
- **Node.js:** 18.0 or newer
- **Git**
- A **64-bit Python installation** is recommended

Python 3.14 has been tested with the current dependency configuration.

You can verify your installed versions with:

    python --version
    node --version
    npm --version

---

# Step-by-Step Setup Guide

## 1. Clone the Repository

    git clone <repository-url>
    cd <repository-directory>

---

# Backend Setup

## Windows

Open PowerShell or Command Prompt in the project directory.

### 1. Create a virtual environment

    python -m venv .venv

### 2. Activate the virtual environment

**PowerShell:**

    .venv\Scripts\Activate.ps1

**Command Prompt:**

    .venv\Scripts\activate.bat

If PowerShell blocks script execution, run:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Then activate the environment again.

### 3. Verify Python

    python --version

Python 3.12 or newer should be displayed.

### 4. Upgrade pip and build tools

    python -m pip install --upgrade pip setuptools wheel

### 5. Install dependencies

    python -m pip install -r requirements.txt

### 6. Configure environment variables

Copy the example environment file:

    copy .env.example .env

Then edit `.env` and add your API keys:

    GEMINI_API_KEY=your_gemini_api_key_here
    GROQ_API_KEY=your_groq_api_key_here

Both keys are optional individually.

The application uses:

    Gemini → primary LLM
    Groq   → fallback LLM

If Gemini is unavailable or fails, the application can use Groq when a Groq API key is configured.

> **Security:** Never commit `.env` or API keys to Git.

### 7. Start the backend

    python -m uvicorn app.main:app --reload

The backend will run at:

    http://localhost:8000

Interactive Swagger API documentation:

    http://localhost:8000/docs

---

## macOS / Linux

### 1. Create a virtual environment

    python3 -m venv .venv

### 2. Activate the environment

    source .venv/bin/activate

### 3. Verify Python

    python --version

Python 3.12 or newer should be displayed.

### 4. Upgrade pip and build tools

    python -m pip install --upgrade pip setuptools wheel

### 5. Install dependencies

    python -m pip install -r requirements.txt

### 6. Configure environment variables

Copy the example environment file:

    cp .env.example .env

Then add your API keys to `.env`:

    GEMINI_API_KEY=your_gemini_api_key_here
    GROQ_API_KEY=your_groq_api_key_here

### 7. Start the backend

    python -m uvicorn app.main:app --reload

The backend will run at:

    http://localhost:8000

Interactive Swagger API documentation:

    http://localhost:8000/docs

---

# Frontend Setup

Open a new terminal window while keeping the backend running.

Navigate to the frontend directory:

    cd frontend

Install the Node.js dependencies:

    npm install

Start the Vite development server:

    npm run dev

The frontend will run at:

    http://localhost:3000

The Vite development server automatically proxies API requests to the FastAPI backend running on port 8000.

---

# Verify Backend Installation

Make sure the backend virtual environment is activated, then run:

    python -c "import fitz, fastapi, uvicorn, faiss, numpy, sentence_transformers, dotenv; print('All dependencies loaded successfully!')"

Expected output:

    All dependencies loaded successfully!

You can also check the installed NumPy version:

    python -c "import numpy; print('NumPy:', numpy.__version__)"

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

Page information is retained so that retrieved evidence can be associated with the relevant policy page.

---

## 2. Create Vector Index

Each text chunk is converted into an embedding using:

    all-MiniLM-L6-v2

The resulting embeddings are stored in a FAISS vector index for semantic search.

This allows the system to retrieve policy sections based on meaning rather than relying only on exact keyword matches.

---

## 3. Ask a Policy Question

When a user asks a question:

1. The question is converted into an embedding.
2. FAISS searches for the most relevant policy chunks.
3. The top relevant chunks are retrieved.
4. The retrieved evidence and question are sent to Gemini when a Gemini API key is configured.
5. Gemini generates a grounded answer using the retrieved evidence.
6. If Gemini is unavailable or fails, Groq is used as the fallback LLM when a Groq API key is configured.
7. Both LLM paths use the same policy-grounding rules and response structure.
8. The response includes confidence and page/section citations where available.
9. If the LLM providers are unavailable, the existing local retrieval fallback can still provide policy context.

The LLM is instructed to:

- Use only retrieved policy evidence.
- Avoid inventing policy conditions.
- Distinguish explicit information from missing information.
- Preserve policy terminology.
- Avoid unsupported assumptions.
- Avoid performing financial calculations.
- Provide relevant citations.
- Return structured JSON for reliable backend processing.

---

## 4. Gemini and Groq Fallback

The policy Q&A system follows this flow:

    User Question
          ↓
    FAISS Retrieval
          ↓
    Relevant Policy Evidence
          ↓
    Gemini LLM
          ↓
    ┌───────────────────────┐
    │ Gemini succeeds?      │
    └───────────┬───────────┘
                │
          Yes   │   No
           ↓    │    ↓
        Answer  │  Groq LLM
                │    ↓
                │  Answer
                │
                └───────────────
                        ↓
                 Local Fallback

Gemini is the primary LLM provider.

Groq acts as a fallback when Gemini is unavailable or the Gemini response cannot be processed successfully.

Both providers receive the same retrieved policy evidence and follow the same `CRITICAL_RULES`, helping maintain consistent behavior between the primary and fallback paths.

---

# Grounded Policy Intelligence

The system uses a shared set of policy-grounding rules for both Gemini and Groq.

The rules require the model to:

- Ground answers strictly in retrieved policy evidence.
- Never invent policy values or conditions.
- Distinguish explicit policy statements from missing information.
- Handle partial answers carefully.
- Preserve policy terminology such as "subject to", "up to", "after", "excluded", and "not specified".
- Assign confidence based on the quality of retrieved evidence.
- Provide relevant citations.
- Avoid financial calculations.

For example, if a policy states a general pre-existing disease waiting period but does not provide a separate waiting period for a particular procedure, the system should report both facts without inventing a procedure-specific duration.

---

# 5. Estimate Treatment Cost

The treatment estimator:

- Receives a selected treatment.
- Looks up its cost in the synthetic treatment catalog.
- Considers the selected city and hospital type where supported by the dataset.
- Applies simplified insurance rules through the deterministic coverage engine.
- Produces an estimated coverage and patient out-of-pocket result.

The deterministic coverage engine can consider policy-related factors such as:

- Sum insured
- Deductible
- Co-payment
- Treatment sub-limit
- Waiting period
- Patient information

The LLM is **not responsible for financial arithmetic**.

Financial calculations are handled separately by deterministic backend logic to make the result more predictable and reproducible.

> **Important:** The treatment prices and insurance calculations are synthetic and intended only for demonstration purposes.

---

# Environment Variables

Create a `.env` file in the project root.

Example:

    GEMINI_API_KEY=your_gemini_api_key_here
    GROQ_API_KEY=your_groq_api_key_here

### Gemini

Gemini is the primary LLM provider for policy Q&A.

### Groq

Groq is used as the fallback LLM provider when Gemini is unavailable or fails.

At least one LLM provider should be configured to generate AI-synthesized policy answers.

The application can still demonstrate document processing and retrieval without an LLM API key.

> **Security:** Never commit `.env` to Git.

---

# Project Structure

    project-root/
    │
    ├── app/
    │   ├── main.py
    │   ├── services/
    │   │   ├── pdf_service.py
    │   │   ├── rag_service.py
    │   │   └── cost_service.py
    │   │
    │   └── data/
    │       └── treatment_costs.json
    │
    ├── frontend/
    │   ├── src/
    │   ├── package.json
    │   └── ...
    │
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    └── README.md

---

# Technology Stack

## Frontend

- React
- Vite
- Tailwind CSS

## Backend

- FastAPI
- Python
- Pydantic
- Uvicorn

## Document Processing

- PyMuPDF

## Semantic Retrieval

- Sentence Transformers
- `all-MiniLM-L6-v2`
- FAISS

## LLM Providers

- Google Gemini
- Groq fallback

## Treatment Cost Intelligence

- JSON-based synthetic treatment catalog
- Deterministic coverage calculations

---

# API Flow

## Policy Upload

    Frontend
        ↓
    POST /api/policy/upload
        ↓
    PyMuPDF
        ↓
    Page-aware chunks
        ↓
    Sentence Transformers
        ↓
    FAISS index

## Policy Question

    Frontend
        ↓
    POST /api/policy/ask
        ↓
    Question embedding
        ↓
    FAISS semantic retrieval
        ↓
    Relevant policy evidence
        ↓
    Gemini
        ↓
    Groq fallback if required
        ↓
    Answer + Confidence + Citations

## Treatment Estimate

    Frontend
        ↓
    POST /api/treatment/estimate
        ↓
    Treatment catalog lookup
        ↓
    Deterministic coverage engine
        ↓
    Estimated treatment cost
        ↓
    Potential coverage
        ↓
    Estimated patient out-of-pocket cost

---

# Verify the Application

After starting the backend, open:

    http://localhost:8000/docs

After starting the frontend, open:

    http://localhost:3000

Recommended demo flow:

1. Upload a sample insurance policy PDF.
2. Wait for the policy to be indexed.
3. Ask a policy question.
4. Verify the answer and policy citation.
5. Ask a question where information is missing from the policy.
6. Verify that the system does not invent an answer.
7. Open the treatment cost estimator.
8. Select a treatment, city, and hospital type.
9. Review the estimated treatment cost.
10. Review the deterministic coverage and out-of-pocket calculation.

---

# Example Policy Questions

The following questions can be used to test the policy RAG system:

- What is the co-payment percentage for eligible claims?
- What is the deductible per claim?
- What is the waiting period for pre-existing diseases?
- Does the policy specify a separate waiting period for knee replacement?
- What is the maximum coverage for knee replacement?
- Is cosmetic surgery covered?
- What is the room-rent limit?
- Does the policy cover hospitalization expenses?

The system should answer only from the uploaded policy evidence.

---

# Troubleshooting

## NumPy Installation Fails

If NumPy installation fails during dependency installation, first verify your Python version:

    python --version

Then make sure pip is up to date:

    python -m pip install --upgrade pip setuptools wheel

Recreate the virtual environment if necessary.

### Windows

    deactivate
    Remove-Item -Recurse -Force .venv

    python -m venv .venv
    .venv\Scripts\Activate.ps1

    python -m pip install --upgrade pip setuptools wheel
    python -m pip install -r requirements.txt

### macOS / Linux

    deactivate
    rm -rf .venv

    python3 -m venv .venv
    source .venv/bin/activate

    python -m pip install --upgrade pip setuptools wheel
    python -m pip install -r requirements.txt

---

## PowerShell Cannot Activate the Virtual Environment

Run:

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

Then:

    .venv\Scripts\Activate.ps1

---

## Check That the Virtual Environment Is Active

Your terminal should normally show:

    (.venv)

You can also check the Python executable:

    python -c "import sys; print(sys.executable)"

The output should point to the project's `.venv` directory.

---

## Gemini Is Unavailable

If Gemini fails, verify:

1. `GEMINI_API_KEY` is present in `.env`.
2. The backend was restarted after changing `.env`.
3. The API key is valid.
4. The configured Gemini model is available.

If Groq is configured, the application can automatically attempt the Groq fallback.

---

## Groq Fallback Is Not Working

Verify that:

    GROQ_API_KEY=your_groq_api_key_here

is present in `.env`.

Then restart the backend.

The backend logs should indicate when the Groq fallback is called.

---

## No AI Provider Is Configured

The application can still demonstrate:

- PDF processing
- Text extraction
- Chunking
- Semantic retrieval
- Retrieved policy evidence

However, an LLM provider is required for the final synthesized AI answer.

---

# Development Notes

- **Hackathon MVP** — designed for demonstration rather than production.
- **In-memory storage** — uploaded policies and FAISS indexes are not persisted across application restarts unless persistence is implemented separately.
- **Synthetic treatment data** — treatment costs are demonstration data and should not be treated as real hospital pricing.
- **Synthetic policy data** — sample policy documents are for demonstration and testing.
- **Deterministic financial calculations** — monetary calculations are handled separately from the LLM.
- **Grounded LLM responses** — Gemini and Groq receive retrieved policy evidence rather than relying on general insurance knowledge.
- **LLM fallback** — Groq provides a secondary generation path when Gemini is unavailable.
- **CORS** is intentionally wide-open for local development.
- **Python 3.14** has been tested with the current dependency configuration.

---

# Limitations

This project is a prototype and has several intentional limitations:

- Treatment costs are synthetic.
- Policy documents used for demonstration are synthetic or sample documents.
- Coverage calculations are simplified.
- Real insurance claim settlement involves additional rules and verification.
- The system does not connect to real insurance company claim systems.
- The system does not guarantee claim approval.
- Policy interpretation should be verified against the actual policy and insurer.
- The current storage approach is intended for a hackathon environment.
- The system should not be used as a substitute for professional insurance, medical, financial, or legal advice.

---

# Development Status

This project is a **hackathon MVP** demonstrating the concept of combining:

- Insurance policy document processing
- Page-aware document retrieval
- Retrieval-Augmented Generation (RAG)
- Semantic search
- Large Language Models
- Gemini primary generation
- Groq fallback generation
- Grounded policy answers
- Policy citations
- Confidence information
- Treatment cost estimation
- Deterministic insurance coverage calculations
- Patient out-of-pocket estimation

The core idea is to connect **policy rules, treatment information, and cost information** into a single patient-facing intelligence workflow.

---

# Team

**Team git commit & pray**

**Pimpri Chinchwad College of Engineering, Pune**

Project:

**Policy-to-Patient: Insurance Coverage & Treatment Cost Intelligence**

---

# Disclaimer

This project is a hackathon prototype created for demonstration and educational purposes.

It does not provide real insurance coverage decisions, medical advice, financial advice, legal advice, or guaranteed claim outcomes.

Treatment costs, policy documents, and calculated results used in the prototype may be synthetic and should not be treated as real-world insurance or healthcare information.