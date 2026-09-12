from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    page_number: int
    char_count: int


class PageTextOut(PageOut):
    text: str


class PaperOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_filename: str
    file_size_bytes: int
    page_count: int
    status: str
    error_message: str | None
    uploaded_at: datetime


class PaperDetailOut(PaperOut):
    pages: list[PageOut] = []


class PaperPagesOut(BaseModel):
    paper_id: str
    pages: list[PageTextOut]
