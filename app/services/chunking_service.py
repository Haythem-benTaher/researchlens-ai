"""Splits page text into overlapping chunks sized for embedding.

Word-count based rather than token-based: it avoids pulling in a tokenizer
dependency, and for typical English paper text a word is a close-enough
proxy for a token that the approximation doesn't matter at this chunk
granularity.
"""
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class TextChunk:
    chunk_index: int  # order within the page, 0-indexed
    text: str


def chunk_text(
    text: str,
    *,
    chunk_size_words: int = settings.chunk_size_words,
    overlap_words: int = settings.chunk_overlap_words,
) -> list[TextChunk]:
    """Split text into overlapping word-windows.

    Overlap keeps a sentence that straddles a chunk boundary from having
    its meaning split across two disconnected chunks, which would hurt
    retrieval for anything near a boundary.
    """
    words = text.split()
    if not words:
        return []

    if chunk_size_words <= 0:
        raise ValueError("chunk_size_words must be positive")
    if overlap_words >= chunk_size_words:
        raise ValueError("overlap_words must be smaller than chunk_size_words")

    stride = chunk_size_words - overlap_words
    chunks: list[TextChunk] = []
    start = 0
    idx = 0
    while start < len(words):
        window = words[start : start + chunk_size_words]
        chunks.append(TextChunk(chunk_index=idx, text=" ".join(window)))
        idx += 1
        if start + chunk_size_words >= len(words):
            break
        start += stride

    return chunks
