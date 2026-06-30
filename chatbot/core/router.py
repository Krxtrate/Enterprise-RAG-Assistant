"""
core/router.py
──────────────
Context routing: given a classified intent dict, calls the correct
retrieval function and returns the assembled context string.

Also owns:
  • Follow-up comparison resolution (scanning history for product names)
  • desired_predict sizing (how many tokens the LLM should generate)
  • The is_self_contained flag consumed by core/memory

All retrieval calls are synchronous; the async caller in app.py wraps
each call with `loop.run_in_executor`.

Imports:
  • config          (no keyword lists needed here — intent already classified)
  • core/intent     (is_followup_compare, detect_all_products)
  • core/memory     (find_last_products)
  • core/retrieval  (all build_* functions)
"""

from typing import List, Optional, Tuple

from chatbot.core.intent import detect_all_products, is_followup_compare
from chatbot.core.memory import find_last_products
from chatbot.core.retrieval import (
    build_comparison_context,
    build_global_context,
    build_multi_product_context,
    build_overview_context,
    build_product_context,
    build_product_listing_context,
    build_semantic_context,
    build_team_context,
)

# Sentinel returned by all retrieval functions when nothing is found
_NO_INFO = "NO_RELEVANT_COMPANY_INFORMATION"


def resolve_comparison_followup(
    intent: dict,
    messages,
) -> dict:
    """
    If the current query has no products but looks like a comparison follow-up
    (e.g. "which is better?"), scan message history and inherit products.

    Returns a (potentially mutated copy of) the intent dict.
    """
    intent = dict(intent)   # shallow copy — don't mutate caller's dict

    if intent["mentioned_products"]:
        return intent   # products already named in this message

    if not is_followup_compare(
        # caller already has the normalised `q`; we receive it as part of intent
        intent.get("_q", "")
    ):
        return intent

    history_products = find_last_products(messages)

    if len(history_products) >= 2:
        intent["mentioned_products"] = history_products
        intent["is_comparison"]      = True
    elif len(history_products) == 1:
        intent["mentioned_product"]  = history_products[0]
        intent["mentioned_products"] = history_products

    return intent


def route_context(intent: dict, latest_question: str) -> Tuple[str, bool]:
    """
    Select and call the correct retrieval function based on the intent dict.

    Returns:
      (context_string, is_company_question)

    The second return value indicates whether a company-data lookup was
    attempted; it's used downstream to emit an "I don't have that
    information" fallback instead of calling the LLM with empty context.
    """
    is_overview         = intent["is_overview"]
    is_listing          = intent["is_listing"]
    is_team_query       = intent["is_team_query"]
    is_comparison       = intent["is_comparison"]
    is_technical        = intent["is_technical"]
    is_company_question = intent["is_company_question"]
    mentioned_product   = intent["mentioned_product"]
    mentioned_products  = intent["mentioned_products"]

    context: str  = _NO_INFO
    is_company    = False

    if is_overview:
        context    = build_overview_context()
        is_company = True

    elif is_listing:
        context    = build_product_listing_context()
        is_company = True

    elif is_team_query:
        context    = build_team_context()
        is_company = True

    elif is_comparison:
        context    = build_comparison_context(mentioned_products)
        is_company = True

    elif len(mentioned_products) > 1:
        context    = build_multi_product_context(mentioned_products)
        is_company = True

    elif mentioned_product:
        context    = build_product_context(mentioned_product)
        is_company = True

    elif is_technical:
        context    = build_global_context(latest_question)
        is_company = True

    elif is_company_question:
        context    = build_semantic_context(latest_question)
        is_company = True

    # Automatic fallback: if primary retrieval returned nothing, try global search
    if context == _NO_INFO:
        print("Primary retrieval failed")
        print("Semantic search failed → global search")
        context = build_global_context(latest_question)

    return context, is_company


def compute_desired_predict(intent: dict) -> int:
    """
    Return the desired number of tokens for the LLM to generate,
    based on the query type.
    """
    if intent["is_overview"] or intent["is_listing"]:
        return 1800
    if intent["is_comparison"]:
        return 1200   # needs more tokens to cover both products side-by-side
    if intent["mentioned_product"] or intent["is_team_query"]:
        return 1000
    return 400


def is_self_contained(intent: dict) -> bool:
    """
    True when the query should be answered without chat history.

    Self-contained queries use ONLY the current question so the model
    does not confuse old product descriptions with the fresh context.
    """
    return bool(
        intent["mentioned_product"]
        or intent["is_comparison"]
        or intent["is_team_query"]
        or intent["is_overview"]
        or intent["is_listing"]
        or intent["is_technical"]
    )