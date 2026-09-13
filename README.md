# ResearchLens — Milestones 1–2: PDF Ingestion + RAG Core

A FastAPI backend for uploading research papers, extracting their text
page-by-page, chunking and embedding that text locally, and semantically
searching across it. This is the foundation for the chat and analysis
milestones still to come.

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

A SQLite DB (`storage/researchlens.db`), uploaded PDFs (`storage/pdfs/`),
and a FAISS vector index (`storage/vectors.index`) are created
automatically on first run.

**First run will be slower** — `sentence-transformers` downloads the
embedding model (`all-MiniLM-L6-v2`, ~90MB) from Hugging Face the first
time it's used, then caches it under `~/.cache/huggingface` for every run
after that. Needs a normal internet connection for that one-time
download; no API key required.

## Endpoints

| Method | Path                     | Description                                  |
|--------|--------------------------|-----------------------------------------------|
| POST   | `/papers/upload`         | Upload a PDF (multipart `file` field)         |
| GET    | `/papers`                | List all papers, newest first                 |
| GET    | `/papers/{id}`           | Paper metadata + per-page char counts         |
| GET    | `/papers/{id}/pages`     | Full extracted text for every page            |
| DELETE | `/papers/{id}`           | Remove a paper, its file, and its vectors     |
| GET    | `/search?q=...`          | Semantic search across all indexed chunks     |
| GET    | `/health`                | Liveness check                                |

`/search` also accepts `top_k` (default 5) and `paper_id` (to restrict
search to one paper).

### Search example

```bash
curl "http://localhost:8000/search?q=what+dataset+was+used&top_k=3"
```

```json
{
  "query": "what dataset was used",
  "results": [
    {
      "chunk_id": "...",
      "paper_id": "...",
      "paper_title": "Attention Is All You Need",
      "page_number": 2,
      "text": "Methodology section: we use a synthetic dataset with 100 examples...",
      "score": 0.71
    }
  ]
}
```

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
- **Sync extraction for now.** Upload blocks until extraction, chunking,
  and embedding all finish. Fine for typical paper sizes; if large batch
  uploads become common, move `ingest_pdf` to a background task/queue —
  the DB schema (`status: processing|ready|failed`) already supports
  polling for that.
- **Chunking is word-count based** (~180 words per chunk, 40-word overlap;
  see `app/services/chunking_service.py`), not token-based. This avoids an
  extra tokenizer dependency; for English paper text a word is a close
  enough proxy for a token at this granularity. Overlap prevents a
  sentence near a chunk boundary from having its meaning split across two
  disconnected chunks.
- **Embeddings are local** via `sentence-transformers`
  (`all-MiniLM-L6-v2`, 384 dimensions) — no API key, runs on CPU, good
  enough quality for a personal-project scale. Swappable later for a
  hosted model (OpenAI/Voyage) by changing only
  `app/services/embedding_service.py`.
- **Vector storage is FAISS**, a single index file on disk
  (`storage/vectors.index`), loaded into memory at request time. Chosen
  over Postgres/pgvector or a hosted vector DB because it needs zero extra
  infrastructure — appropriate for a personal project, not for multi-user
  production scale. `app/services/vector_store.py` is the only place that
  would need to change to swap it out later.
- **Deleting a paper removes its vectors too** (`deindex_paper`), so the
  index doesn't accumulate orphaned vectors for papers that no longer
  exist.
- **Indexing failure doesn't fail the upload.** If chunking/embedding
  raises (e.g. the embedding model can't be loaded), the paper is still
  saved and readable — it just won't show up in search results, and
  `error_message` explains why.

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

## Testing retrieval quality

Once you've uploaded a few real papers, spot-check `/search` with
questions you know the answer to (e.g. "what evaluation metric did they
use", "what was the sample size") and confirm the top result actually
contains that answer, on the page it should be on. If results feel off:
- Try adjusting `chunk_size_words`/`chunk_overlap_words` in
  `app/core/config.py` — too large and chunks mix unrelated content
  together; too small and a chunk loses surrounding context.
- Try `top_k` higher (e.g. 10) to see if the right chunk is close but not
  first — that's a ranking problem; if it's missing entirely, that's a
  chunking or embedding-model problem.

## Next: Milestone 3 (AI chat)

`app/services/retrieval_service.search()` is already the retrieval half
of RAG. Milestone 3 adds:
1. A `/chat` endpoint that takes a question (and optionally a `paper_id`
   to scope it).
2. Call `retrieval_service.search()` to fetch the top-k relevant chunks.
3. Build a prompt with those chunks as context and send it to an LLM.
4. Return the answer with citations — each chunk already carries its
   source `paper_id` and `page_number`, so citations are close to free.
