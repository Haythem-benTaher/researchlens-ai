from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.paper import Chunk, Page
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_query, embed_texts
from app.services import vector_store


def index_paper(db: Session, paper_id: str) -> int:
    """Chunk every page of a paper, embed the chunks, and add them to the
    vector index. Returns the number of chunks created.

    Safe to call on a paper with no extractable pages (e.g. a "failed"
    upload) — it just indexes nothing.
    """
    pages = db.scalars(
        select(Page).where(Page.paper_id == paper_id).order_by(Page.page_number)
    ).all()

    next_vector_id = (db.scalar(select(func.max(Chunk.vector_id))) or 0) + 1

    chunk_rows: list[Chunk] = []
    texts: list[str] = []
    for page in pages:
        for tc in chunk_text(page.text):
            if not tc.text.strip():
                continue
            chunk_rows.append(
                Chunk(
                    vector_id=next_vector_id,
                    paper_id=paper_id,
                    page_number=page.page_number,
                    chunk_index=tc.chunk_index,
                    text=tc.text,
                    char_count=len(tc.text),
                )
            )
            texts.append(tc.text)
            next_vector_id += 1

    if not chunk_rows:
        return 0

    vectors = embed_texts(texts)
    vector_store.add(vectors, [c.vector_id for c in chunk_rows])

    db.add_all(chunk_rows)
    db.commit()
    return len(chunk_rows)


def deindex_paper(db: Session, paper_id: str) -> None:
    """Remove a paper's chunks from the vector index. Call this before
    deleting the Paper row (the Chunk rows themselves cascade-delete)."""
    vector_ids = db.scalars(
        select(Chunk.vector_id).where(Chunk.paper_id == paper_id)
    ).all()
    vector_store.remove(list(vector_ids))


@dataclass
class SearchResult:
    chunk_id: str
    paper_id: str
    paper_title: str
    page_number: int
    text: str
    score: float


def search(db: Session, query: str, *, top_k: int = 5, paper_id: str | None = None) -> list[SearchResult]:
    """Semantic search across chunks. If paper_id is given, restricts to
    that paper's chunks (over-fetches from FAISS then filters, since FAISS
    itself has no per-paper scoping)."""
    query_vector = embed_query(query)

    fetch_k = top_k * 5 if paper_id else top_k
    vector_ids, scores = vector_store.search(query_vector, fetch_k)
    if not vector_ids:
        return []

    score_by_vector_id = dict(zip(vector_ids, scores))

    stmt = select(Chunk).where(Chunk.vector_id.in_(vector_ids))
    if paper_id:
        stmt = stmt.where(Chunk.paper_id == paper_id)
    chunks = db.scalars(stmt).all()

    results = [
        SearchResult(
            chunk_id=c.id,
            paper_id=c.paper_id,
            paper_title=c.paper.title,
            page_number=c.page_number,
            text=c.text,
            score=score_by_vector_id[c.vector_id],
        )
        for c in chunks
    ]
    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k]
