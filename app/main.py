"""
FastAPI application factory.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models import HealthResponse
from app.routes import policies, chat, treatment, policy

from dotenv import load_dotenv
load_dotenv()

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Insurance Policy Intelligence Assistant",
    description=(
        "REST API for uploading insurance policy PDFs, querying coverage details, "
        "chatting with an AI assistant, and estimating treatment costs."
    ),
    version="0.1.0",
)

# ── CORS (allow all origins for local development) ────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────

app.include_router(policy.router)
app.include_router(policies.router)
app.include_router(chat.router)
app.include_router(treatment.router)



# ── Health check ──────────────────────────────────────────────────────────────

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Service health check",
)
def health():
    """Returns 200 OK when the service is running."""
    return HealthResponse(timestamp=datetime.now(timezone.utc))
