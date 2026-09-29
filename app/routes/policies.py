"""
Policy routes
  POST /api/policies/upload
  GET  /api/policies
  GET  /api/policies/{policy_id}
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app import store
from app.models import (
    PolicyDetail,
    PolicyRecord,
    PolicySummary,
    UploadResponse,
)

router = APIRouter(prefix="/api/policies", tags=["Policies"])

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


# ── Upload ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a policy PDF",
)
async def upload_policy(file: UploadFile = File(...)):
    """
    Accept a PDF file upload and register a new policy entry.

    * Validates the content-type and file size.
    * Saves the file to the `uploads/` directory.
    * Stores metadata in the in-memory store.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Got: {file.content_type}",
        )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {MAX_FILE_SIZE_MB} MB limit.",
        )

    policy_id = store.new_id()
    file_path = store.save_upload(policy_id, file.filename, data)

    from app.services import pdf_service, rag_service
    chunks = pdf_service.extract_and_chunk(file_path)
    page_count = max([c.get("page", 1) for c in chunks]) if chunks else 1
    rag_service.build_index(policy_id, chunks, filename=file.filename, page_count=page_count)

    record = PolicyRecord(
        policy_id=policy_id,
        filename=file.filename,
        file_path=file_path,
        uploaded_at=datetime.now(timezone.utc),
        page_count=page_count,
        chunks_count=len(chunks),
        is_indexed=True
    )
    store.save_policy(record)

    return UploadResponse(
        policy_id=policy_id,
        filename=file.filename,
        message="Policy uploaded and indexed successfully.",
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=list[PolicySummary],
    summary="List all uploaded policies",
)
def list_policies():
    """Return a lightweight summary list of every uploaded policy."""
    return [
        PolicySummary(
            policy_id=p.policy_id,
            filename=p.filename,
            uploaded_at=p.uploaded_at,
            holder_name=p.holder_name,
            coverage_type=p.coverage_type,
        )
        for p in store.all_policies()
    ]


# ── Detail ────────────────────────────────────────────────────────────────────

@router.get(
    "/{policy_id}",
    response_model=PolicyDetail,
    summary="Get full details for a policy",
)
def get_policy(policy_id: str):
    """Return the full record for a single policy, identified by its UUID."""
    record = store.get_policy(policy_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{policy_id}' not found.",
        )
    return record
