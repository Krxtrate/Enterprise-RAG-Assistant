"""
services/ollama.py
──────────────────
All communication with the Ollama inference server lives here.

Responsibilities:
  • Pre-warming the model at startup
  • Sending chat requests under the global concurrency semaphore
  • Context-window sizing (_compute_ctx)
  • Per-request timing summary (_log_timing_summary)

Imports: config only (no other internal modules → no circular risk).
"""


import asyncio
import time
from typing import List

import httpx

from chatbot.config import OLLAMA_MODEL, OLLAMA_URL

# ─────────────────────────────────────────────────────────────
# CONCURRENCY GUARD
# Ollama runs one inference at a time on a single GPU.
# The semaphore queues concurrent requests instead of letting them
# collide, which caused the blank "OLLAMA REQUEST ERROR:" crash.
# ─────────────────────────────────────────────────────────────

_ollama_sem = asyncio.Semaphore(1)

# ─────────────────────────────────────────────────────────────
# PRE-WARM
# ─────────────────────────────────────────────────────────────

def get_model_name() -> str:
    return OLLAMA_MODEL

def prewarm_ollama() -> None:
    """
    Load the model into GPU VRAM at startup so the first real request
    is not penalised by the cold-start overhead.
    Non-fatal: if Ollama is not yet running the app still starts.
    """
    print("Pre-warming Ollama model...")
    try:
        with httpx.Client(timeout=60) as _c:
            _c.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model":      OLLAMA_MODEL,
                    "messages":   [{"role": "user", "content": "hi"}],
                    "stream":     False,
                    "keep_alive": "30m",
                    "options":    {"num_predict": 1, "num_gpu": 99},
                },
            )
        print("Ollama model loaded.")
    except Exception as _e:
        print(f"Ollama pre-warm failed (non-fatal): {_e}")


# ─────────────────────────────────────────────────────────────
# CALLER
# ─────────────────────────────────────────────────────────────

async def call_llm(payload: dict, timeout: float = 120.0) -> dict:
    """
    POST to Ollama under the global semaphore.
    - Semaphore ensures only one inference runs at a time → no connection resets.
    - exc.__class__.__name__ logged so the error is never silently blank.
    - Raises on any network or HTTP error; caller handles user-facing message.
    """
    # Force the correct local model name regardless of what's already in
    # payload["model"] — the payload may have been built while HF was still
    # the active backend (e.g. "meta-llama/Llama-3.1-8B-Instruct"), which
    # Ollama doesn't recognize and will 404 on.
    payload = {**payload, "model": OLLAMA_MODEL}

    async with _ollama_sem:
        print("Ollama semaphore acquired — sending request...")
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(f"{OLLAMA_URL}/api/chat", json=payload)
            elapsed = time.perf_counter() - t0
            print(f"OLLAMA STATUS: {resp.status_code}  TIME: {elapsed:.2f}s")

            if resp.status_code != 200:
                print(f"OLLAMA ERROR BODY: {resp.text[:500]}")
                raise RuntimeError(f"Ollama HTTP {resp.status_code}")

            return resp.json()

        except httpx.TimeoutException as exc:
            print(f"OLLAMA TIMEOUT [{exc.__class__.__name__}]: {exc!r}")
            raise
        except httpx.RequestError as exc:
            print(f"OLLAMA REQUEST ERROR [{exc.__class__.__name__}]: {exc!r}")
            raise


# ─────────────────────────────────────────────────────────────
# CONTEXT WINDOW SIZING
# RTX 3050 6 GB: keep num_ctx ≤ 4096 for focused queries so the
# KV cache stays inside the ~1.3 GB of free VRAM. num_gpu=99 forces
# all model layers onto the GPU, preventing the CPU fallback that
# caused the 226-second BidCounty response.
# ─────────────────────────────────────────────────────────────

def compute_ctx(ollama_messages: List[dict], desired_predict: int) -> tuple[int, int]:
    """
    Returns (num_ctx, num_predict) sized to fit both prompt and generation.

    Sizing formula:
      prompt_tokens_est = (total chars across all messages) / 3.0 + 1024 overhead
      num_ctx = smallest power-of-2 ≥ prompt_tokens_est + desired_predict, capped at 8192
      num_predict = min(desired_predict, num_ctx - prompt_tokens_est), floor 256
    """
    prompt_chars     = sum(len(m.get("content", "")) for m in ollama_messages)
    prompt_tok_est   = int(prompt_chars / 3.0) + 1024
    total_needed     = prompt_tok_est + desired_predict

    num_ctx = 2048
    while num_ctx < total_needed and num_ctx < 8192:
        num_ctx *= 2

    remaining   = num_ctx - prompt_tok_est
    num_predict = max(256, min(desired_predict, remaining))

    print(
        f"CTX SIZING — prompt_chars: {prompt_chars}, "
        f"est_tokens: {prompt_tok_est}, desired_predict: {desired_predict}, "
        f"num_ctx: {num_ctx}, num_predict: {num_predict}"
    )
    return num_ctx, num_predict


# ─────────────────────────────────────────────────────────────
# TIMING SUMMARY
# ─────────────────────────────────────────────────────────────

def log_timing_summary(
    intent_time: float,
    retrieval_time: float,
    prompt_time: float,
    ollama_time: float,
    parse_time: float,
    prompt_chars: int,
    num_predict: int,
) -> None:
    """Log a structured timing breakdown for a single /generate request."""
    total = intent_time + retrieval_time + prompt_time + ollama_time + parse_time
    print(
        f"\n── TIMING SUMMARY ──────────────────────────────\n"
        f"  Intent detection : {intent_time:.3f}s\n"
        f"  Chroma retrieval : {retrieval_time:.3f}s\n"
        f"  Prompt building  : {prompt_time:.3f}s\n"
        f"  Ollama inference : {ollama_time:.3f}s\n"
        f"  JSON parsing     : {parse_time:.3f}s\n"
        f"  ─────────────────────────────────────────────\n"
        f"  TOTAL            : {total:.3f}s\n"
        f"  Prompt chars     : {prompt_chars}\n"
        f"  Prompt tokens est: {prompt_chars // 4}\n"
        f"  num_predict      : {num_predict}\n"
        f"  Total tokens est : {prompt_chars // 4 + num_predict}\n"
        f"────────────────────────────────────────────────\n"
    )