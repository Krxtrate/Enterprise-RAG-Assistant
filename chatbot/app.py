"""
app.py
──────
FastAPI application entry point.

This file contains almost no logic of its own.  Its only jobs are:

  1. Bootstrap the application (middleware, thread pool, startup tasks).
  2. Receive HTTP requests.
  3. Delegate to the appropriate module (intent → routing → prompts → Ollama).
  4. Return the response.

All business logic lives in the core/ and services/ modules.
"""

import asyncio
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import sys
import httpx
import pytz
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Internal modules ──────────────────────────────────────────────────────────
from chatbot.config import THREAD_POOL_MAX_WORKERS, HF_API_TOKEN, HF_API_URL, HF_MODEL
from chatbot.models import ChatRequest

from chatbot.core.intent import detect_intent
from chatbot.core.memory import build_ollama_messages, resolve_followup_product
from chatbot.prompts.prompts import build_system_prompt
from chatbot.core.router import (
    compute_desired_predict,
    is_self_contained,
    resolve_comparison_followup,
    route_context,
)
from chatbot.core.smalltalk import match_smalltalk, pick_smalltalk_reply
from chatbot.core.utils import clean_llm_output, render_smalltalk

'''
from chatbot.services.ollama import (
    call_ollama,
    compute_ctx,
    log_timing_summary,
    prewarm_ollama,
)
'''

from chatbot.services.hf import (
    call_ollama,
    compute_ctx,
    log_timing_summary,
    prewarm_ollama,
)

# services/chroma is imported by core/retrieval at module load, which triggers
# the ChromaDB startup diagnostics.  We import it here explicitly so the
# startup print statements appear before the route handlers are registered.
import chatbot.services.chroma  # noqa: F401  (side-effect import for startup diagnostics)

# ─────────────────────────────────────────────────────────────
# APP BOOTSTRAP
# ─────────────────────────────────────────────────────────────

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for blocking I/O (ChromaDB, embeddings)
_executor = ThreadPoolExecutor(max_workers=THREAD_POOL_MAX_WORKERS)

# ─────────────────────────────────────────────────────────────
# STARTUP  (runs once when the process starts)
# ─────────────────────────────────────────────────────────────

# Pre-warm the Ollama model so the first real request isn't penalised
# by cold-start overhead.  Non-fatal — the app still starts if Ollama
# is not yet available.
prewarm_ollama()

# ─────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    try:
        httpx.get("http://localhost:11434/api/tags", timeout=2)
        return {"fastapi": True, "ollama": True}
    except Exception:
        return {"fastapi": True, "ollama": False}


@app.get("/")
def home():
    return {"message": "AdCounty AI Assistant Running"}


@app.post("/generate")
async def generate(chat: ChatRequest):
    try:
        return await _generate(chat)
    except Exception:
        print("UNHANDLED ERROR IN /generate:")
        traceback.print_exc()
        return {"output": "Sorry, something went wrong. Please try again."}


# ─────────────────────────────────────────────────────────────
# MAIN ORCHESTRATION FUNCTION
# ─────────────────────────────────────────────────────────────

async def _generate(chat: ChatRequest):
    t_total_start = time.perf_counter()

    # ── 1. Extract latest user message ──────────────────────────────────────
    if not chat.messages:
        return {"output": "No message received."}

    latest_question = ""
    for msg in reversed(chat.messages):
        if msg.role == "user":
            latest_question = (msg.content or "").strip()
            break

    if not latest_question:
        return {"output": "No message received."}

    print(f"\n{'─' * 48}")
    print(f"  USER: {latest_question}")
    print(f"{'─' * 48}")

    # ── 2. Timezone ──────────────────────────────────────────────────────────
    ist          = pytz.timezone("Asia/Kolkata")
    now          = datetime.now(ist)
    current_time = now.strftime("%I:%M %p")
    current_date = now.strftime("%A, %d %B %Y")
    hour         = now.hour

    # ── 3. Smalltalk short-circuit ───────────────────────────────────────────
    smalltalk_candidates = match_smalltalk(latest_question)
    if smalltalk_candidates is not None:
        print(f"SMALLTALK MATCH: '{latest_question}'")
        reply = pick_smalltalk_reply(smalltalk_candidates)
        return {"output": render_smalltalk(reply, current_time, current_date, hour)}

    # ── 4. Intent detection ──────────────────────────────────────────────────
    t_intent_start = time.perf_counter()

    q = latest_question.lower().replace("-", " ")

    intent = detect_intent(q)
    # Stash the normalised query so resolve_comparison_followup can use it
    intent["_q"] = q

    # ── 4a. Follow-up comparison: inherit products from history ──────────────
    if not intent["mentioned_products"] and len(chat.messages) > 1:
        intent = resolve_comparison_followup(intent, chat.messages)

    intent_time = time.perf_counter() - t_intent_start

    print(
        f"\nINTENT — product: {intent['mentioned_product']}, "
        f"products: {intent['mentioned_products']}, "
        f"comparison: {intent['is_comparison']}, overview: {intent['is_overview']}, "
        f"listing: {intent['is_listing']}, team: {intent['is_team_query']}, "
        f"followup: {intent['is_followup']}, "
        f"company: {intent['is_company_question']}, "
        f"hard_signal: {intent['is_hard_signal']}"
    )
    print(f"INTENT TIME: {intent_time:.3f}s")

    # ── 5. Follow-up resolution: inherit product from previous exchange ───────
    (
        intent["mentioned_product"],
        q,
        latest_question,
        followup_is_company,
    ) = resolve_followup_product(
        chat.messages,
        is_followup=intent["is_followup"],
        mentioned_product=intent["mentioned_product"],
        q=q,
        latest_question=latest_question,
    )
    if followup_is_company:
        intent["is_company_question"] = True

    # ── 6. Build company context (blocking I/O → thread pool) ────────────────
    t_retrieval_start = time.perf_counter()
    loop = asyncio.get_event_loop()

    context, is_company_question = await loop.run_in_executor(
        _executor,
        route_context,
        intent,
        latest_question,
    )

    retrieval_time = time.perf_counter() - t_retrieval_start
    print(f"RETRIEVAL TIME: {retrieval_time:.3f}s")

    # If we flagged it as a company question but got nothing back, say so
    if is_company_question and not context:
        print("WARNING: company question but no context retrieved")
        return {"output": "I don't have that information right now."}

    print(f"CONTEXT: {context.count('SOURCE:')} chunks, {len(context)} chars\n")

    # ── 7. Build system prompt ───────────────────────────────────────────────
    t_prompt_start = time.perf_counter()

    system_content = build_system_prompt(
        is_overview=intent["is_overview"],
        is_listing=intent["is_listing"],
        current_date=current_date,
        current_time=current_time,
        context=context,
    )

    # ── 8. Build Ollama message list ─────────────────────────────────────────
    ollama_messages = build_ollama_messages(
        system_content=system_content,
        messages=chat.messages,
        latest_question=latest_question,
        is_self_contained=is_self_contained(intent),
    )

    prompt_time = time.perf_counter() - t_prompt_start
    print(f"PROMPT BUILD TIME: {prompt_time:.3f}s")

    # ── 9. Context window sizing ─────────────────────────────────────────────
    desired_predict         = compute_desired_predict(intent)
    num_ctx, num_predict    = compute_ctx(ollama_messages, desired_predict)

    # ── 10. Ollama payload ───────────────────────────────────────────────────
    payload = {
        "model":      HF_MODEL,
        "messages":   ollama_messages,
        "stream":     False,
        "keep_alive": "30m",
        "options": {
            "num_ctx":     num_ctx,
            "num_predict": num_predict,
            "num_gpu":     99,          # force all layers onto GPU — kills CPU fallback
            "temperature": 0.2,
            # Only real LLaMA 3 special tokens — NOT role words like "user" or "assistant"
            # which appear in valid prose and would silently truncate responses.
            "stop": ["<|eot_id|>", "<|start_header_id|>", "<|end_header_id|>"],
        },
    }

    # ── 11. Call Ollama ──────────────────────────────────────────────────────
    t_ollama_start = time.perf_counter()
    try:
        result = await call_ollama(payload)
    except (httpx.TimeoutException, httpx.RequestError, RuntimeError):
        return {"output": "The AI service is currently unavailable. Please try again in a moment."}
    except Exception as e:
        print(f"UNEXPECTED OLLAMA ERROR: {e}")
        traceback.print_exc()
        return {"output": "Sorry, something went wrong. Please try again."}
    ollama_time = time.perf_counter() - t_ollama_start
    print(f"OLLAMA TIME: {ollama_time:.3f}s")

    # ── 12. Parse response ───────────────────────────────────────────────────
    t_parse_start = time.perf_counter()

    done_reason = result.get("done_reason", "")
    eval_count  = result.get("eval_count", 0)
    print(f"DONE REASON: {done_reason}  EVAL COUNT: {eval_count}")

    raw = (result.get("message") or {}).get("content", "")
    print(f"RAW OUTPUT: {repr(raw[:200])}")

    output = clean_llm_output(raw)

    parse_time = time.perf_counter() - t_parse_start
    print(f"JSON PARSE TIME: {parse_time:.3f}s")

    # ── 13. Timing summary ───────────────────────────────────────────────────
    prompt_chars = sum(len(m.get("content", "")) for m in ollama_messages)
    log_timing_summary(
        intent_time=intent_time,
        retrieval_time=retrieval_time,
        prompt_time=prompt_time,
        ollama_time=ollama_time,
        parse_time=parse_time,
        prompt_chars=prompt_chars,
        num_predict=num_predict,
    )
    print(f"TOTAL TIME: {time.perf_counter() - t_total_start:.3f}s")

    if not output:
        return {"output": "I don't have that information right now."}

    return {"output": output}

# ─────────────────────────────────────────────────────────────
# MCP
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if "--mcp" in sys.argv:
        from chatbot.services.mcp_server import mcp
        mcp.run()
    else:
        import uvicorn
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)