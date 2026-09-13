"""Local embedding generation via sentence-transformers.

No API key needed — the model runs on-device. The first call downloads
the model weights (~90MB for the default model) and caches them under
~/.cache/huggingface; every call after that is fully offline.
"""
from functools import lru_cache

import numpy as np

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_model():
    # Imported lazily so the (slow) torch/transformers import only happens
    # once embeddings are actually needed, not on every app startup.
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.embedding_model_name)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts, L2-normalized so inner product == cosine
    similarity (this is what the FAISS index in vector_store.py assumes)."""
    if not texts:
        return np.zeros((0, settings.embedding_dim), dtype="float32")

    model = _get_model()
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return vectors.astype("float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string; returns a (1, dim) array ready for
    vector_store search."""
    return embed_texts([query])
