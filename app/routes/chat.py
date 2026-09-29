"""
Chat route
  POST /api/chat
"""

from fastapi import APIRouter, HTTPException, status

from app import store
from app.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question about a policy",
)
def chat(request: ChatRequest):
    """
    Accept a natural-language question about an uploaded policy.

    Currently returns a canned stub response.
    Replace the body of `_generate_answer()` with an actual RAG pipeline later.
    """
    from app.services import rag_service
    from app.models import Citation

    policy = store.get_policy(request.policy_id)
    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Policy '{request.policy_id}' not found.",
        )

    if not rag_service.is_indexed(request.policy_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Policy '{request.policy_id}' is not indexed yet.",
        )

    result = rag_service.query(question=request.question, policy_id=request.policy_id)
    
    citations = [
        Citation(
            text=c.get("text", ""),
            page_number=int(c.get("page", 1)),
            chunk_index=i,
        )
        for i, c in enumerate(result.get("citations", []))
    ]

    return ChatResponse(
        policy_id=request.policy_id,
        question=request.question,
        answer=result.get("answer", ""),
        citations=citations,
        disclaimer=f"Confidence: {result.get('confidence', 'Medium')}. Grounded directly in policy document."
    )
