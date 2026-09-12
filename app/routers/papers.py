from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.paper import Paper
from app.models.schemas import PaperDetailOut, PaperOut, PaperPagesOut
from app.services.paper_service import ingest_pdf, save_upload_to_disk

router = APIRouter(prefix="/papers", tags=["papers"])

MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024


@router.post("/upload", response_model=PaperOut, status_code=201)
async def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a PDF, extract its text page-by-page, and store it.

    Returns the paper record immediately with status "ready" or "failed"
    (extraction is synchronous for now; Milestone 2 can move this to a
    background task/queue once embedding generation is added).
    """
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(415, f"Unsupported file type: {file.content_type}. Only PDF is accepted.")

    content = await file.read()
    if not content:
        raise HTTPException(400, "Uploaded file is empty")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, f"File exceeds max size of {settings.max_upload_mb}MB")

    dest_path = save_upload_to_disk(file.filename or "upload.pdf", content)

    try:
        paper = ingest_pdf(
            db,
            original_filename=file.filename or dest_path.name,
            file_path=dest_path,
            file_size_bytes=len(content),
        )
    except Exception:
        dest_path.unlink(missing_ok=True)
        raise

    return paper


@router.get("", response_model=list[PaperOut])
def list_papers(db: Session = Depends(get_db)):
    """Return every paper in the library, most recent first."""
    papers = db.scalars(select(Paper).order_by(Paper.uploaded_at.desc())).all()
    return papers


@router.get("/{paper_id}", response_model=PaperDetailOut)
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    return paper


@router.get("/{paper_id}/pages", response_model=PaperPagesOut)
def get_paper_pages(paper_id: str, db: Session = Depends(get_db)):
    """Return the full extracted text for every page, with page numbers —
    the raw material Milestone 2's chunking step will consume."""
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")
    return PaperPagesOut(paper_id=paper.id, pages=paper.pages)


@router.delete("/{paper_id}", status_code=204)
def delete_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.get(Paper, paper_id)
    if not paper:
        raise HTTPException(404, "Paper not found")

    file_path = Path(paper.file_path)
    file_path.unlink(missing_ok=True)

    db.delete(paper)
    db.commit()
    return None
