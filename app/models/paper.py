import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Paper(Base):
    """A single uploaded research paper (PDF) and its metadata."""

    __tablename__ = "papers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    # status: processing | ready | failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    pages: Mapped[list["Page"]] = relationship(
        "Page", back_populates="paper", cascade="all, delete-orphan", order_by="Page.page_number"
    )


class Page(Base):
    """Extracted text for a single page of a paper. This is the atomic unit
    that later gets chunked for embeddings (Milestone 2) and cited back to
    the user in chat answers (Milestone 3)."""

    __tablename__ = "pages"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    paper_id: Mapped[str] = mapped_column(String, ForeignKey("papers.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-indexed
    text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    paper: Mapped["Paper"] = relationship("Paper", back_populates="pages")
