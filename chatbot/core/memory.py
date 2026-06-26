"""
core/memory.py
──────────────
Utilities for reading and reasoning over conversation history.

Responsibilities:
  • Scanning past messages to resolve follow-up product references
  • Building the trimmed message list sent to Ollama for conversational queries

Imports:
  • core/intent  (detect_product, detect_all_products)

No imports from retrieval, chroma, or ollama → no circular risk.
"""

from typing import List, Optional

from chatbot.core.intent import detect_all_products, detect_product


# ─────────────────────────────────────────────────────────────
# HISTORY SCANNING
# ─────────────────────────────────────────────────────────────

def find_last_products(messages) -> List[str]:
    """
    Walk backwards through previous user messages and return the
    most recently mentioned products.

    `messages` is the full List[Message] from the ChatRequest —
    the current (last) message is excluded from the scan.
    """
    for msg in reversed(messages[:-1]):   # ignore current message
        if msg.role != "user":
            continue
        products = detect_all_products(
            (msg.content or "").lower().replace("-", " ")
        )
        if products:
            return products
    return []


def resolve_followup_product(
    messages,
    is_followup: bool,
    mentioned_product: Optional[str],
    q: str,
    latest_question: str,
) -> tuple[Optional[str], str, str, bool]:
    """
    If this is a follow-up query with no product mentioned, scan the last
    2 exchanges (4 messages) and inherit the most recently named product.

    Returns (mentioned_product, q, latest_question, is_company_question).
    The caller should use the returned values to replace the originals.
    """
    if not (is_followup and not mentioned_product):
        return mentioned_product, q, latest_question, False

    recent = messages[:-1][-4:]   # up to 4 messages = ~2 exchanges
    for msg in reversed(recent):
        p = detect_product((msg.content or "").lower().replace("-", " "))
        if p:
            print(f"FOLLOW-UP resolved → product: {p}")
            return p, q + f" {p.lower()}", latest_question + f" {p}", True

    return mentioned_product, q, latest_question, False


# ─────────────────────────────────────────────────────────────
# OLLAMA MESSAGE HISTORY BUILDER
# ─────────────────────────────────────────────────────────────

def build_ollama_messages(
    system_content:  str,
    messages,                       # List[Message] from ChatRequest
    latest_question: str,
    *,
    is_self_contained: bool,
) -> List[dict]:
    """
    Build the list of dicts sent to Ollama.

    Self-contained queries (product / comparison / team / overview / listing /
    technical) include ONLY the current question — history is excluded to
    prevent the model from choosing old product descriptions over the fresh
    context.

    Conversational queries include the last 3 full exchanges (6 messages)
    so the bot can say "as I mentioned above…" on follow-ups.  Very long
    turns are trimmed to ≤ 600 chars to protect the context window.
    """
    ollama_messages: List[dict] = [{"role": "system", "content": system_content}]

    if is_self_contained:
        # Self-contained query: only the current question.
        # No history — the model was choosing old product descriptions
        # over the new context when history was included.
        ollama_messages.append({"role": "user", "content": latest_question})
    else:
        # Conversational query: include last 3 full exchanges (user + assistant).
        # This lets the bot say "as I mentioned above…" on follow-ups.
        history = messages[:-1]   # everything except the current message
        recent  = history[-6:]    # last 6 messages = ~3 exchanges
        for msg in recent:
            content = (msg.content or "").strip()
            # Trim very long turns to protect the context window
            if len(content) > 600:
                content = content[-600:]
            if content:
                ollama_messages.append({"role": msg.role, "content": content})
        # Always append the current question last
        ollama_messages.append({"role": "user", "content": latest_question})

    return ollama_messages