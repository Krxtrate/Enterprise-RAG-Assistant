"""
services/hf.py
──────────────
All communication with the Hugging Face Inference API lives here.

No local model needed — just a HF_API_TOKEN in the environment.
"""

import asyncio
import os
import time
from typing import List

import httpx

from chatbot.config import HF_MODEL, HF_API_URL

_hf_sem = asyncio.Semaphore(3)  # HF API supports concurrent requests unlike local Ollama
HF_TIMEOUT_SECONDS = 20.0

HF_API_TOKEN = os.environ.get("HF_API_TOKEN", "")


def prewarm_ollama() -> None:
    """No-op — HF API has no warm-up needed. Kept for drop-in compatibility."""
    if not HF_API_TOKEN:
        print("WARNING: HF_API_TOKEN not set. Set it in your environment.")
    else:
        print("HF Inference API ready.")


async def call_ollama(payload: dict, timeout: float = 120.0) -> dict:
    """
    Translate an Ollama-style payload to HF Inference API format and call it.
    Returns an Ollama-compatible response dict so app.py needs zero changes.
    """
    effective_timeout = min(timeout, HF_TIMEOUT_SECONDS)
    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not set")

    messages = payload.get("messages", [])

    hf_payload = {
        "model": HF_MODEL,
        "messages": messages,
        "max_tokens": payload.get("options", {}).get("num_predict", 512),
        "temperature": payload.get("options", {}).get("temperature", 0.2),
        "stream": False,
    }

    async with _hf_sem:
        print(f"HF API request sending with timeout={effective_timeout}s...")
        t0 = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=effective_timeout) as client:
                resp = await client.post(
                    HF_API_URL,
                    headers={
                        "Authorization": f"Bearer {HF_API_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json=hf_payload,
                )
            elapsed = time.perf_counter() - t0
            print(f"HF API STATUS: {resp.status_code}  TIME: {elapsed:.2f}s")

            if resp.status_code != 200:
                print(f"HF API ERROR: {resp.text[:500]}")
                raise RuntimeError(f"HF API HTTP {resp.status_code}")

            data = resp.json()

            content = data["choices"][0]["message"]["content"]
            return {
                "message": {"content": content},
                "done_reason": data["choices"][0].get("finish_reason", "stop"),
                "eval_count": data.get("usage", {}).get("completion_tokens", 0),
            }

        except httpx.TimeoutException as exc:
            print(f"HF API TIMEOUT: {exc!r}")
            raise
        except httpx.RequestError as exc:
            print(f"HF API REQUEST ERROR: {exc!r}")
            raise


def compute_ctx(ollama_messages: List[dict], desired_predict: int) -> tuple[int, int]:
    """
    Kept for drop-in compatibility with app.py.
    HF API manages context internally — we just return the desired_predict.
    """
    prompt_chars = sum(len(m.get("content", "")) for m in ollama_messages)
    prompt_tok_est = int(prompt_chars / 3.0)
    print(
        f"CTX SIZING — prompt_chars: {prompt_chars}, "
        f"est_tokens: {prompt_tok_est}, desired_predict: {desired_predict}"
    )
    return 8192, desired_predict


def log_timing_summary(
    intent_time: float,
    retrieval_time: float,
    prompt_time: float,
    ollama_time: float,
    parse_time: float,
    prompt_chars: int,
    num_predict: int,
) -> None:
    total = intent_time + retrieval_time + prompt_time + ollama_time + parse_time
    print(
        f"\n── TIMING SUMMARY ──────────────────────────────\n"
        f"  Intent detection : {intent_time:.3f}s\n"
        f"  Chroma retrieval : {retrieval_time:.3f}s\n"
        f"  Prompt building  : {prompt_time:.3f}s\n"
        f"  HF API inference : {ollama_time:.3f}s\n"
        f"  JSON parsing     : {parse_time:.3f}s\n"
        f"  ─────────────────────────────────────────────\n"
        f"  TOTAL            : {total:.3f}s\n"
        f"────────────────────────────────────────────────\n"
    )


def get_model_name() -> str:
    return HF_MODEL