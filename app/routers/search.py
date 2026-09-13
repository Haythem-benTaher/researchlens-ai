from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import SearchResponse, SearchResultOut
from app.services import retrieval_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
def semantic_search(
    q: str = Query(..., min_length=1, description="Natural-language search query"),
    top_k: int = Query(5, ge=1, le=50),
    paper_id: str | None = Query(None, description="Restrict search to a single paper"),
    db: Session = Depends(get_db),
):
    """Semantic search over all indexed paper chunks. This is the retrieval
    step that Milestone 3's chat endpoint will call internally to gather
    context before asking the LLM to answer."""
    results = retrieval_service.search(db, q, top_k=top_k, paper_id=paper_id)
    return SearchResponse(
        query=q,
        results=[SearchResultOut(**r.__dict__) for r in results],
    )
