"""Thin wrapper around a FAISS index for local, single-process vector search.

Chosen for a personal-project scale: no server to run, the whole index
lives in one file on disk, and it's loaded into memory at startup. If this
ever needs to scale beyond one machine or handle heavy concurrent writes,
swap this module for pgvector or a hosted vector DB — nothing outside this
file needs to change since routers/services talk to it through add() /
search() / remove().
"""
import threading

import faiss
import numpy as np

from app.core.config import settings

_lock = threading.Lock()
_index: faiss.Index | None = None


def _new_index() -> faiss.Index:
    # Inner product on L2-normalized vectors == cosine similarity.
    # IDMap lets us use our own integer ids (Chunk.vector_id) instead of
    # FAISS's implicit sequential position, which matters once chunks get
    # deleted and ids are no longer contiguous.
    return faiss.IndexIDMap(faiss.IndexFlatIP(settings.embedding_dim))


def _ensure_loaded() -> faiss.Index:
    global _index
    if _index is None:
        if settings.faiss_index_path.exists():
            _index = faiss.read_index(str(settings.faiss_index_path))
        else:
            _index = _new_index()
    return _index


def _save() -> None:
    faiss.write_index(_index, str(settings.faiss_index_path))


def add(vectors: np.ndarray, ids: list[int]) -> None:
    """Add embeddings to the index, tagged with caller-supplied integer ids
    (Chunk.vector_id), and persist to disk."""
    if len(ids) == 0:
        return
    with _lock:
        index = _ensure_loaded()
        index.add_with_ids(vectors, np.array(ids, dtype="int64"))
        _save()


def search(query_vector: np.ndarray, top_k: int) -> tuple[list[int], list[float]]:
    """Return (vector_ids, scores) for the top_k nearest chunks, most
    similar first. Scores are cosine similarity in [-1, 1]."""
    with _lock:
        index = _ensure_loaded()
        if index.ntotal == 0:
            return [], []
        k = min(top_k, index.ntotal)
        scores, ids = index.search(query_vector, k)

    result_ids = [int(i) for i in ids[0] if i != -1]
    result_scores = [float(s) for i, s in zip(ids[0], scores[0]) if i != -1]
    return result_ids, result_scores


def remove(ids: list[int]) -> None:
    """Remove vectors by id (e.g. when a paper is deleted)."""
    if not ids:
        return
    with _lock:
        index = _ensure_loaded()
        index.remove_ids(np.array(ids, dtype="int64"))
        _save()


def count() -> int:
    with _lock:
        return _ensure_loaded().ntotal
