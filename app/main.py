from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.models import paper  # noqa: F401 ensures models are registered before create_all
from app.routers import papers

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ResearchLens API",
    description="Upload research papers, chat with them, and extract structured insights.",
    version="0.1.0",
)

# Wide-open CORS for local dev with a separate frontend (Milestone 4).
# Tighten this to specific origins before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(papers.router)


@app.get("/health")
def health():
    return {"status": "ok"}
