"""
Policy RAG routes:
  POST /api/policy/upload
  POST /api/policy/ask
  GET  /api/policy/active
"""

from datetime import datetime, timezone
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app import store
from app.models import (
    CitationItem,
    PolicyAskRequest,
    PolicyAskResponse,
    PolicyRecord,
    PolicyUploadResponse,
)
from app.services import pdf_service, rag_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/policy", tags=["Policy Engine"])

ALLOWED_CONTENT_TYPES = {"application/pdf", "application/octet-stream"}
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@router.post(
    "/upload",
    response_model=PolicyUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and index insurance policy PDF",
)
async def upload_policy(file: UploadFile = File(...)):
    """
    1. Accept PDF file upload.
    2. Extract text from every PDF page using PyMuPDF.
    3. Preserve page number, section/heading if detectable, text.
    4. Split into chunks:
       { 'text': '...', 'page': 7, 'section': 'Hospitalisation', 'chunk_id': '...' }
    5. Embed and store in FAISS vector store.
    """
    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Only PDF files are accepted. Received: {file.content_type}",
            )

    data = await file.read()
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_MB} MB.",
        )

    policy_id = store.new_id()
    file_path = store.save_upload(policy_id, file.filename, data)

    # 1. Extract and chunk text preserving page and section
    chunks = pdf_service.extract_and_chunk(file_path)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not extract readable text from the uploaded PDF.",
        )

    page_count = max(c["page"] for c in chunks) if chunks else 1

    # Extract deterministic policy config (sum_insured, deductible, copay, sublimits)
    from app.services import coverage_service
    policy_config = coverage_service.extract_policy_config_from_chunks(chunks)

    # 2. Embed and build FAISS index
    rag_service.build_index(
        policy_id=policy_id,
        chunks=chunks,
        filename=file.filename,
        page_count=page_count,
        policy_config=policy_config,
    )

    # Save to store for persistence across endpoints
    record = PolicyRecord(
        policy_id=policy_id,
        filename=file.filename,
        file_path=file_path,
        uploaded_at=datetime.now(timezone.utc),
        page_count=page_count,
        chunks_count=len(chunks),
        is_indexed=True,
    )
    store.save_policy(record)

    return PolicyUploadResponse(
        message="Policy uploaded and indexed successfully.",
        policy_id=policy_id,
        filename=file.filename,
        page_count=page_count,
        chunks_count=len(chunks),
    )


@router.post(
    "/ask",
    response_model=PolicyAskResponse,
    summary="Ask a question about the uploaded insurance policy",
)
def ask_policy(request: PolicyAskRequest):
    """
    1. Retrieve relevant policy chunks for question.
    2. Send ONLY retrieved evidence to LLM.
    3. Return cited answer with confidence and page/section citations.
    """
    if not rag_service.is_indexed(request.policy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No policy uploaded or indexed yet. Please upload a policy PDF first.",
        )

    try:
        result = rag_service.query(
            question=request.question,
            policy_id=request.policy_id,
            top_k=4,
        )

        citations = [
            CitationItem(
                page=int(c.get("page", 1)),
                section=str(c.get("section", "General")),
                text=str(c.get("text", "")),
            )
            for c in result.get("citations", [])
        ]

        return PolicyAskResponse(
            answer=result.get("answer", "No answer could be generated."),
            confidence=result.get("confidence", "Medium"),
            citations=citations,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.exception("Error processing policy question: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while querying the policy: {str(e)}",
        )


@router.get(
    "/active",
    summary="Get active policy status",
)
def get_active_policy():
    """Return status of currently active uploaded policy."""
    info = rag_service.get_active_policy_info()
    if not info:
        return {"is_uploaded": False}
    return {
        "is_uploaded": True,
        **info,
    }
