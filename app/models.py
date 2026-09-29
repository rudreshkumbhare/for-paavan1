"""
Pydantic models — request bodies and response shapes.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ── Policy (internal record + API response) ───────────────────────────────────

class PolicyRecord(BaseModel):
    """Internal record stored in memory after a PDF upload."""
    policy_id: str
    filename: str
    file_path: str
    uploaded_at: datetime
    policy_number: Optional[str] = None
    holder_name: Optional[str] = None
    insurer: Optional[str] = None
    coverage_type: Optional[str] = None
    # Stub: real extraction would populate these from an AI pipeline
    raw_text_preview: str = "PDF uploaded. Text extraction not yet implemented."
    page_count: int = 0
    chunks_count: int = 0
    is_indexed: bool = False


class PolicySummary(BaseModel):
    """Lightweight listing item."""
    policy_id: str
    filename: str
    uploaded_at: datetime
    holder_name: Optional[str] = None
    coverage_type: Optional[str] = None


class PolicyDetail(PolicyRecord):
    """Full detail view (same shape as the internal record for now)."""
    pass


# ── Upload ────────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    policy_id: str
    filename: str
    message: str


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    policy_id: str = Field(..., description="ID of the policy to query")
    question: str = Field(..., min_length=1, description="User's question about the policy")


class Citation(BaseModel):
    text: str
    page_number: int
    chunk_index: int


class ChatResponse(BaseModel):
    policy_id: str
    question: str
    answer: str
    citations: List[Citation] = []
    disclaimer: str = "AI-generated answer based on policy document. Verify with your insurer."


# ── Treatment cost estimate ───────────────────────────────────────────────────

class TreatmentEstimateRequest(BaseModel):
    policy_id: str = Field(..., description="Policy to check coverage against")
    treatment_name: str = Field(..., min_length=1, description="Name of the treatment / procedure")
    estimated_cost: Optional[float] = Field(None, ge=0, description="Estimated total cost in USD")
    provider_name: Optional[str] = Field(None, description="Healthcare provider / hospital name")


class CoverageBreakdown(BaseModel):
    covered_amount: Optional[float] = None
    out_of_pocket: Optional[float] = None
    deductible_applied: Optional[float] = None
    copay: Optional[float] = None
    notes: str = "Coverage breakdown will be calculated once AI extraction is implemented."


class TreatmentEstimateResponse(BaseModel):
    policy_id: str
    treatment_name: str
    estimated_cost: Optional[float]
    coverage: CoverageBreakdown
    disclaimer: str = (
        "This is a stub response. Actual coverage calculations require AI-extracted policy data."
    )


class TreatmentCatalogItem(BaseModel):
    name: str
    category: str
    average_cost: float
    min_cost: float
    max_cost: float
    cpt_code: str


class CostEstimateResult(BaseModel):
    treatment_name: str
    average_cost: float
    insurance_covers: float
    out_of_pocket: float
    deductible_applied: float
    copay_amount: float
    notes: str


# ── Generic helpers ───────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str


# ── Direct Policy RAG Models (matches /api/policy/upload and /api/policy/ask) ─

class CitationItem(BaseModel):
    page: int
    section: str
    text: str


class PolicyAskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question about the uploaded policy")
    policy_id: Optional[str] = Field(None, description="Optional policy ID; defaults to active uploaded policy")


class PolicyAskResponse(BaseModel):
    answer: str
    confidence: str = Field(..., description="High, Medium, or Low")
    citations: List[CitationItem] = []


class PolicyUploadResponse(BaseModel):
    message: str = "Policy uploaded and indexed successfully."
    policy_id: str
    filename: str
    page_count: int
    chunks_count: int

