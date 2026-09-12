"""PDF ingestion: extracting per-page text and basic metadata.

Kept isolated from the FastAPI layer so the extraction strategy can be
swapped later (e.g. add OCR fallback for scanned PDFs) without touching
routers.
"""
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PdfReadError


class PDFExtractionError(Exception):
    """Raised when a PDF cannot be parsed or contains no extractable text."""


@dataclass
class ExtractedPage:
    page_number: int  # 1-indexed
    text: str


@dataclass
class ExtractionResult:
    page_count: int
    pages: list[ExtractedPage]
    inferred_title: str | None


def extract_pdf(file_path: Path) -> ExtractionResult:
    """Extract text page-by-page from a PDF file on disk.

    Raises PDFExtractionError if the file is not a readable PDF.
    """
    try:
        reader = PdfReader(str(file_path))
    except (PdfReadError, Exception) as exc:  # pypdf raises various errors on malformed files
        raise PDFExtractionError(f"Could not read PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")  # try empty password; common for "restricted" but not private PDFs
        except Exception as exc:
            raise PDFExtractionError("PDF is password-protected and could not be decrypted") from exc

    pages: list[ExtractedPage] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        pages.append(ExtractedPage(page_number=i, text=text.strip()))

    if not pages:
        raise PDFExtractionError("PDF has no pages")

    if all(p.text == "" for p in pages):
        # Extractable-but-empty usually means a scanned/image-only PDF.
        raise PDFExtractionError(
            "No extractable text found — this PDF may be a scanned image without OCR"
        )

    inferred_title = _infer_title(reader, pages)

    return ExtractionResult(page_count=len(pages), pages=pages, inferred_title=inferred_title)


def _infer_title(reader: PdfReader, pages: list[ExtractedPage]) -> str | None:
    """Best-effort title: PDF metadata first, else the first non-trivial
    line of page 1 (a common heuristic for paper titles)."""
    meta_title = None
    try:
        if reader.metadata and reader.metadata.title:
            meta_title = reader.metadata.title.strip()
    except Exception:
        pass

    if meta_title:
        return meta_title

    if pages:
        for line in pages[0].text.splitlines():
            line = line.strip()
            if len(line) > 8 and not line.isdigit():
                return line[:300]

    return None
