"""
core/utils.py
─────────────
Pure helper functions shared across the application.

Rules for this file:
  • No business logic.
  • No external service calls (no ChromaDB, no Ollama, no HTTP).
  • No imports from other internal modules (avoids circular imports).
  • Every function here takes only plain Python types as arguments.
"""

import re
from typing import List, Optional, Tuple


# ─────────────────────────────────────────────────────────────
# TEXT NORMALISATION
# ─────────────────────────────────────────────────────────────

def normalise(text: str) -> str:
    """Lowercase + strip punctuation. Used for smalltalk matching."""
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def contains_keyword(text: str, keywords: List[str]) -> bool:
    """
    Return True if any keyword in `keywords` appears as a whole word
    inside `text` (case-insensitive, word-boundary aware).
    """
    text = text.lower()
    return any(
        re.search(rf"\b{re.escape(k.lower())}\b", text)
        for k in keywords
    )


# ─────────────────────────────────────────────────────────────
# LLM OUTPUT CLEANING
# ─────────────────────────────────────────────────────────────

def clean_llm_output(text: str) -> str:
    """Remove LLaMA 3 special tokens that occasionally leak into generation."""
    for token in (
        "<|eot_id|>",
        "<|start_header_id|>",
        "<|end_header_id|>",
        "<|begin_of_text|>",
    ):
        text = text.strip()
        if text.startswith(token):
            text = text[len(token):].strip()
        if text.endswith(token):
            text = text[: -len(token)].strip()
    return text.strip()


# ─────────────────────────────────────────────────────────────
# SMALLTALK RENDERING
# ─────────────────────────────────────────────────────────────

def render_smalltalk(text: str, current_time: str, current_date: str, hour: int) -> str:
    """
    Replace smalltalk template placeholders with live values.
    Called after a smalltalk match is confirmed; not used by the LLM path.
    """
    greeting = "morning" if hour < 12 else ("afternoon" if hour < 17 else "evening")
    subs = {
        "%botname":      "AdCounty Assistant",
        "%company":      "AdCounty Media",
        "%botgender":    "bot",
        "%feedbacklink": "https://adcountymedia.com/contact",
        "%greeting":     greeting,
        "%languages": (
            "English, Hindi, German, French, Spanish, Italian, Portuguese, Dutch, "
            "Russian, Arabic, Chinese, Japanese, Korean, Turkish, Indonesian, Vietnamese, "
            "Thai, Polish, Ukrainian, Urdu, Tamil, Telugu, Kannada, Malayalam, Marathi, "
            "Gujarati, Punjabi, Bengali"
        ),
        "%location": "our Gurugram office",
        "%name":     "friend",
        "%sitelink": "https://adcountymedia.com",
        "%time":     current_time,
        "%date":     current_date,
    }
    for k, v in subs.items():
        text = text.replace(k, v)
    return text


# ─────────────────────────────────────────────────────────────
# CHROMADB RESULT DEDUPLICATION
# ─────────────────────────────────────────────────────────────

def dedup_docs(
    docs: List[str],
    metas: List[dict],
    label: str = "",
) -> List[Tuple[str, dict]]:
    """
    Return (doc, meta) pairs with content-level deduplication.
    Deduplication is on stripped doc text, not on the assembled entry string,
    so DB-level duplicates (same content, different ChromaDB IDs) are caught.
    """
    seen:   set              = set()
    result: List[Tuple[str, dict]] = []
    skipped = 0
    for doc, meta in zip(docs, metas):
        key = (doc or "").strip()
        if key in seen:
            skipped += 1
            continue
        seen.add(key)
        result.append((doc, meta))
    if skipped:
        print(f"  DEDUP [{label}]: skipped {skipped} duplicate chunk(s)")
    return result


# ─────────────────────────────────────────────────────────────
# CONTEXT ASSEMBLY
# ─────────────────────────────────────────────────────────────

def cap_and_join(entries: List[str], max_chars: int) -> str:
    """
    Join entries up to max_chars. Logs each included chunk and the cap event.
    Returns the sentinel string if nothing fits.
    """
    result: List[str] = []
    total = 0
    for entry in entries:
        if total + len(entry) > max_chars:
            print(
                f"  CONTEXT CAP at {total} chars — "
                f"dropping {len(entries) - len(result)} remaining entries"
            )
            break
        result.append(entry)
        total += len(entry)
    for i, e in enumerate(result):
        tag = next(
            (l for l in e.splitlines() if l.startswith(("SOURCE:", "PRODUCT:"))),
            "?",
        )
        print(f"  CTX[{i}] {len(e)}c  {tag}")
    return "\n\n".join(result) if result else "NO_RELEVANT_COMPANY_INFORMATION"