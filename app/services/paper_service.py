import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.paper import Page, Paper
from app.services.pdf_service import PDFExtractionError, extract_pdf


def save_upload_to_disk(filename: str, content: bytes) -> Path:
    """Write raw upload bytes to the storage dir under a unique name,
    preserving the original extension."""
    suffix = Path(filename).suffix or ".pdf"
    stored_name = f"{uuid.uuid4()}{suffix}"
    dest = settings.pdf_storage_dir / stored_name
    dest.write_bytes(content)
    return dest


def ingest_pdf(db: Session, *, original_filename: str, file_path: Path, file_size_bytes: int) -> Paper:
    """Create a Paper record, extract its text, and persist Page rows.

    On extraction failure, the Paper row is still kept (status="failed")
    so the user gets feedback instead of a silent 500, and the failed
    upload is visible in their library.
    """
    paper = Paper(
        title=original_filename,
        original_filename=original_filename,
        file_path=str(file_path),
        file_size_bytes=file_size_bytes,
        status="processing",
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    try:
        result = extract_pdf(file_path)
    except PDFExtractionError as exc:
        paper.status = "failed"
        paper.error_message = str(exc)
        db.commit()
        db.refresh(paper)
        return paper

    paper.page_count = result.page_count
    if result.inferred_title:
        paper.title = result.inferred_title
    paper.status = "ready"
    paper.error_message = None

    for p in result.pages:
        db.add(
            Page(
                paper_id=paper.id,
                page_number=p.page_number,
                text=p.text,
                char_count=len(p.text),
            )
        )

    db.commit()
    db.refresh(paper)
    return paper
