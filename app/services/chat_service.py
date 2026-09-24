from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.services import llm_service, retrieval_service


@dataclass
class Citation:
    paper_id: str
    paper_title: str
    page_number: int
    snippet: str


@dataclass
class ChatAnswer:
    answer: str
    citations: list[Citation]


def _format_context_block(index: int, result: retrieval_service.SearchResult) -> str:
    """One retrieved chunk, formatted so the LLM can see exactly which
    paper/page it came from — this labeling is what lets the model (and us)
    tie a claim back to a citation."""
    return f"[{index}] Source: {result.paper_title}, page {result.page_number}\n{result.text}"


def answer_question(
    db: Session, question: str, *, paper_id: str | None = None, top_k: int | None = None
) -> ChatAnswer:
    """Full RAG chat flow: retrieve relevant chunks, ask the local LLM to
    answer using only that context, and return the answer with citations
    pointing back to the source paper/page for each chunk actually used."""
    k = top_k or settings.chat_top_k

    results = retrieval_service.search(db, question, top_k=k, paper_id=paper_id)

    if not results:
        return ChatAnswer(
            answer=(
                "I couldn't find anything relevant in your papers to answer that. "
                "Try uploading a paper on this topic, or rephrasing the question."
            ),
            citations=[],
        )

    context_blocks = [_format_context_block(i + 1, r) for i, r in enumerate(results)]
    answer_text = llm_service.generate_answer(question, context_blocks)

    citations = [
        Citation(
            paper_id=r.paper_id,
            paper_title=r.paper_title,
            page_number=r.page_number,
            snippet=r.text[:300],
        )
        for r in results
    ]

    return ChatAnswer(answer=answer_text, citations=citations)
