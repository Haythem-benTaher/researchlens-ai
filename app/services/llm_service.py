"""Talks to a locally running Ollama server to generate answers.

Ollama exposes a plain HTTP API on your machine (default
http://localhost:11434) — no API key, no cloud call. This module is the
only place that knows about Ollama specifically; swapping to a hosted LLM
later would mean changing only this file.
"""
import httpx

from app.core.config import settings


class LLMError(Exception):
    """Raised when the local LLM can't be reached or returns an error —
    typically because Ollama isn't running or the model hasn't been pulled."""


SYSTEM_PROMPT = (
    "You are a research assistant answering questions about academic papers. "
    "Answer ONLY using the provided excerpts below. Each excerpt is labeled "
    "with its source paper and page number. "
    "If the excerpts don't contain enough information to answer, say so "
    "plainly instead of guessing. "
    "Keep answers concise and grounded in the excerpts — don't invent facts, "
    "numbers, or citations that aren't in the provided text."
)


def build_prompt(question: str, context_blocks: list[str]) -> str:
    context = "\n\n".join(context_blocks) if context_blocks else "(no relevant excerpts found)"
    return (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- EXCERPTS ---\n{context}\n--- END EXCERPTS ---\n\n"
        f"Question: {question}\n"
        f"Answer:"
    )


def generate_answer(question: str, context_blocks: list[str]) -> str:
    """Send the question + retrieved context to the local Ollama model and
    return its generated answer text."""
    prompt = build_prompt(question, context_blocks)

    try:
        response = httpx.post(
            f"{settings.ollama_base_url}/api/generate",
            json={
                "model": settings.ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=settings.ollama_timeout_seconds,
        )
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise LLMError(
            "Could not reach Ollama at "
            f"{settings.ollama_base_url}. Is it installed and running? "
            "Try `ollama serve` or check the Ollama app is open."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise LLMError(
            f"Ollama returned an error ({exc.response.status_code}). "
            f"Is the model '{settings.ollama_model}' pulled? "
            f"Try: ollama pull {settings.ollama_model}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise LLMError(
            "Ollama took too long to respond. The model may be loading for "
            "the first time, or your machine may be under heavy load."
        ) from exc

    data = response.json()
    return data.get("response", "").strip()
