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

    class Config:
        env_file = ".env"


settings = Settings()
settings.pdf_storage_dir.mkdir(parents=True, exist_ok=True)
