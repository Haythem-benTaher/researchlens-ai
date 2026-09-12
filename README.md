# ResearchLens — Milestone 1: PDF Ingestion

A FastAPI backend for uploading research papers, extracting their text
page-by-page, and storing metadata. This is the foundation for the later
RAG, chat, and analysis milestones.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`. Interactive API docs at
`http://localhost:8000/docs`.

A SQLite DB (`storage/researchlens.db`) and uploaded PDFs
(`storage/pdfs/`) are created automatically on first run.

## Endpoints

| Method | Path                     | Description                                  |
|--------|--------------------------|-----------------------------------------------|
| POST   | `/papers/upload`         | Upload a PDF (multipart `file` field)         |
| GET    | `/papers`                | List all papers, newest first                 |
| GET    | `/papers/{id}`           | Paper metadata + per-page char counts         |
| GET    | `/papers/{id}/pages`     | Full extracted text for every page            |
| DELETE | `/papers/{id}`           | Remove a paper and its stored file            |
| GET    | `/health`                | Liveness check                                |

### Example

```bash
curl -X POST http://localhost:8000/papers/upload \
  -F "file=@paper.pdf;type=application/pdf"
```

Response:

```json
{
  "id": "c03f0465-...",
  "title": "Attention Is All You Need",
  "original_filename": "paper.pdf",
  "file_size_bytes": 2156,
  "page_count": 3,
  "status": "ready",
  "error_message": null,
  "uploaded_at": "2026-09-12T13:26:56Z"
}
```

## Design notes

- **Text extraction** (`app/services/pdf_service.py`) uses `pypdf` and
  keeps text split by page from the start — this page-level granularity is
  what lets Milestone 3 cite exact page numbers in chat answers.
- **Title inference** falls back from PDF metadata to the first
  substantial line of page 1, since most papers don't set a metadata
  title.
- **Failed uploads aren't rejected outright** — a paper that fails
  extraction (e.g. scanned/image-only PDF, corrupt file) is still saved
  with `status: "failed"` and an `error_message`, so it shows up in the
  library instead of vanishing. Scanned-PDF support (OCR) can be added
  later without changing the API shape.
- **Sync extraction for now.** Upload blocks until extraction finishes.
  Fine for typical paper sizes; if large batch uploads become common,
  move `ingest_pdf` to a background task/queue — the DB schema (`status:
  processing|ready|failed`) already supports polling for that.

## Project layout

```
app/
  core/       # config, DB engine/session
  models/     # SQLAlchemy models + Pydantic schemas
  routers/    # FastAPI route handlers
  services/   # PDF extraction & ingestion logic
storage/
  pdfs/       # uploaded PDF files
  researchlens.db  # SQLite DB (created on first run)
```

## Next: Milestone 2 (RAG core)

The `pages` table (page number + text) is the input for chunking. Suggested
next steps:
1. Add a `chunks` table (paper_id, page_number, chunk_index, text, embedding).
2. Chunk each page's text (e.g. ~500 tokens, with overlap) — keep the source
   `page_number` on every chunk for later citations.
3. Generate embeddings (OpenAI/Anthropic/local model) per chunk.
4. Store vectors — start with an in-process index (e.g. `sqlite-vec`,
   `faiss`) to avoid standing up infra, or use `pgvector`/a hosted vector
   DB if you want it production-ready from day one.
5. Add a `/search` endpoint for semantic search, then eyeball results on a
   few real papers before wiring it into chat.
