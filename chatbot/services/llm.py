"""
services/llm.py
────────────────
Automatic failover LLM router.

Tries Hugging Face Inference API first (fast, ~3-5s, free tier).
On failure (rate limit, timeout, server error), falls back to local
Ollama (medium-slow, ~30-50s, local), and flags the response so the frontend can show a notice.

Automatically retries HF every 24 hours in case the rate limit reset.

app.py imports ONLY from here — never from hf.py or ollama.py directly.
"""

import asyncio
import time

import httpx

from chatbot.config import OLLAMA_URL
from chatbot.services import hf
from chatbot.services import ollama as ollama_backend

_hf_available = True
_fallback_since: float | None = None
HF_RETRY_INTERVAL_SECONDS = 24 * 60 * 60  # retry HF once a day
HF_FALLBACK_NOTICE = (
    "The Hugging Face free tier is currently unavailable or slow, so the model will take a bit longer "
    "while we respond locally."
)
UNAVAILABLE_NOTICE = "Sorry, we’re not available right now. Please try again shortly."


def prewarm_ollama() -> None:
    """Pre-warm both backends so neither pays a cold-start penalty
    whenever it's actually used."""
    hf.prewarm_ollama()
    ollama_backend.prewarm_ollama()


def _maybe_auto_reset() -> None:
    """If we've been on fallback long enough, give HF another shot."""
    global _hf_available, _fallback_since
    if not _hf_available and _fallback_since is not None:
        elapsed = time.time() - _fallback_since
        if elapsed >= HF_RETRY_INTERVAL_SECONDS:
            print("24h elapsed on fallback — retrying HF Inference API.")
            _hf_available = True
            _fallback_since = None


async def _ensure_ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            return resp.status_code == 200
    except Exception as exc:
        print(f"Ollama availability check failed: {exc}")
        return False


async def call_llm(payload: dict, timeout: float = 120.0) -> dict:
    """
    Try HF first. On failure, fall back to local Ollama (which must be
    running on this server) and tag the response so app.py can surface
    a notice to the frontend. Auto-retries HF after 24h on fallback.
    """
    global _hf_available, _fallback_since

    _maybe_auto_reset()

    if _hf_available:
        try:
            result = await hf.call_llm(payload, timeout=timeout)
            result["_backend"] = "hf"
            result["_notice"] = None
            return result
        except (httpx.TimeoutException, httpx.RequestError, RuntimeError) as e:
            print(f"HF API failed, falling back to local Ollama: {e}")
            _hf_available = False
            _fallback_since = time.time()
        except Exception as e:
            print(f"HF API unexpected error, falling back to local Ollama: {e}")
            _hf_available = False
            _fallback_since = time.time()

    # ── Fallback path — local Ollama on this server ──────────────────
    ollama_ready = await _ensure_ollama_available()
    if not ollama_ready:
        raise RuntimeError("Sorry, we’re not available right now. Please try again shortly.")

    try:
        result = await ollama_backend.call_llm(payload, timeout=timeout)
        result["_backend"] = "ollama"
        result["_notice"] = HF_FALLBACK_NOTICE
        return result
    except (httpx.ConnectError, httpx.TimeoutException, RuntimeError) as e:
        print(f"Ollama fallback also unavailable: {e}")
        raise RuntimeError(UNAVAILABLE_NOTICE)


def compute_ctx(ollama_messages: list, desired_predict: int) -> tuple[int, int]:
    if _hf_available:
        return hf.compute_ctx(ollama_messages, desired_predict)
    return ollama_backend.compute_ctx(ollama_messages, desired_predict)


def log_timing_summary(*args, **kwargs) -> None:
    if _hf_available:
        hf.log_timing_summary(*args, **kwargs)
    else:
        ollama_backend.log_timing_summary(*args, **kwargs)


def get_model_name() -> str:
    return hf.get_model_name() if _hf_available else ollama_backend.get_model_name()


def is_using_fallback() -> bool:
    return not _hf_available