from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central app configuration. Values can be overridden via environment
    variables or a .env file (e.g. DATABASE_URL=..., STORAGE_DIR=...)."""

    app_name: str = "ResearchLens"

    # Storage
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    storage_dir: Path = base_dir / "storage"
    pdf_storage_dir: Path = storage_dir / "pdfs"

    # Database
    database_url: str = f"sqlite:///{base_dir / 'storage' / 'researchlens.db'}"

    # Upload constraints
    max_upload_mb: int = 50
    allowed_content_types: tuple[str, ...] = ("application/pdf",)

    # Chunking
    chunk_size_words: int = 180
    chunk_overlap_words: int = 40

    # Embeddings / vector search
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_dim: int = 384  # must match the model above
    faiss_index_path: Path = storage_dir / "vectors.index"

    # Chat / LLM (local via Ollama — no API key needed)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    ollama_timeout_seconds: int = 120
    chat_top_k: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
settings.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
