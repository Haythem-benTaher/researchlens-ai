from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import ChatRequest, ChatResponse, CitationOut
from app.services import chat_service
from app.services.llm_service import LLMError

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Ask a question about your papers. Retrieves relevant chunks via
    semantic search, then asks a local LLM (Ollama) to answer using only
    that retrieved context. Optionally scope to one paper via `paper_id`.
    """
    if not payload.question.strip():
        raise HTTPException(400, "question cannot be empty")

    try:
        result = chat_service.answer_question(
            db, payload.question, paper_id=payload.paper_id, top_k=payload.top_k
        )
    except LLMError as exc:
        # 503: the request itself was fine, but the local LLM dependency
        # isn't reachable/ready — distinct from a client error.
        raise HTTPException(503, str(exc)) from exc

    return ChatResponse(
        answer=result.answer,
        citations=[CitationOut(**c.__dict__) for c in result.citations],
    )
