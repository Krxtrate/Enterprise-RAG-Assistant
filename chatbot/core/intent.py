"""
core/intent.py
──────────────
Intent detection: product name extraction and query classification.

All functions here are pure (no I/O, no DB calls).  They take a
lowercased, dash-normalised query string and return typed results.

Imports:
  • config  (all keyword lists)
  • core/utils  (contains_keyword)

No imports from retrieval, chroma, or ollama → no circular risk.
"""

from typing import List, Optional

from chatbot.config import (
    COMPARISON_TRIGGERS,
    COMPANY_KEYWORDS,
    COMPANY_OVERVIEW_TRIGGERS,
    FOLLOWUP_COMPARE,
    FOLLOWUP_TRIGGERS,
    HARD_COMPANY_SIGNALS,
    PRODUCT_LISTING_MODIFIERS,
    PRODUCT_LISTING_PHRASES,
    PRODUCT_NAME_MAP,
    TEAM_KEYWORDS,
    TECHNICAL_TERMS,
)
from chatbot.core.utils import contains_keyword


# ─────────────────────────────────────────────────────────────
# PRODUCT NAME DETECTION
# ─────────────────────────────────────────────────────────────

def detect_product(text_lower: str) -> Optional[str]:
    """Return the FIRST canonical product name found, longest keyword first."""
    for kw, product in sorted(PRODUCT_NAME_MAP.items(), key=lambda x: -len(x[0])):
        if kw in text_lower:
            return product
    return None


def detect_all_products(text_lower: str) -> List[str]:
    """Return ALL canonical product names found in text, deduplicated, order-preserved."""
    found: List[str] = []
    seen:  set       = set()
    for kw, product in sorted(PRODUCT_NAME_MAP.items(), key=lambda x: -len(x[0])):
        if kw in text_lower and product not in seen:
            found.append(product)
            seen.add(product)
    return found


# ─────────────────────────────────────────────────────────────
# PRODUCT LISTING DETECTION
# ─────────────────────────────────────────────────────────────

def is_product_listing(q: str) -> bool:
    """True if the question is asking for all products."""
    if any(phrase in q for phrase in PRODUCT_LISTING_PHRASES):
        return True
    if "products" in q and any(mod in q for mod in PRODUCT_LISTING_MODIFIERS):
        return True
    return False


# ─────────────────────────────────────────────────────────────
# FULL INTENT CLASSIFICATION
# ─────────────────────────────────────────────────────────────

def detect_intent(q: str) -> dict:
    """
    Classify a normalised (lowercased, dash-replaced) query string
    into a flat intent dict consumed by the router.

    Returns:
      {
        "mentioned_product":   Optional[str],
        "mentioned_products":  List[str],
        "is_hard_signal":      bool,
        "is_company_question": bool,
        "is_team_query":       bool,
        "is_overview":         bool,
        "is_listing":          bool,
        "is_followup":         bool,
        "is_technical":        bool,
        "is_comparison":       bool,
        "is_multi_product":    bool,
      }
    """
    mentioned_product  = detect_product(q)
    mentioned_products = detect_all_products(q)

    is_hard_signal      = any(sig in q for sig in HARD_COMPANY_SIGNALS)
    is_company_question = any(kw in q for kw in COMPANY_KEYWORDS)
    is_team_query       = contains_keyword(q, TEAM_KEYWORDS)
    is_overview         = any(t in q for t in COMPANY_OVERVIEW_TRIGGERS)
    is_listing          = is_product_listing(q)
    is_followup         = any(t in q for t in FOLLOWUP_TRIGGERS)
    is_technical        = any(t in q for t in TECHNICAL_TERMS)

    is_comparison = (
        len(mentioned_products) >= 2
        and any(t in q for t in COMPARISON_TRIGGERS)
    )
    is_multi_product = len(mentioned_products) > 1 and not is_comparison

    return {
        "mentioned_product":   mentioned_product,
        "mentioned_products":  mentioned_products,
        "is_hard_signal":      is_hard_signal,
        "is_company_question": is_company_question,
        "is_team_query":       is_team_query,
        "is_overview":         is_overview,
        "is_listing":          is_listing,
        "is_followup":         is_followup,
        "is_technical":        is_technical,
        "is_comparison":       is_comparison,
        "is_multi_product":    is_multi_product,
    }


# ─────────────────────────────────────────────────────────────
# FOLLOW-UP COMPARISON HELPER
# ─────────────────────────────────────────────────────────────

def is_followup_compare(q: str) -> bool:
    """
    True if the current query looks like a comparison follow-up
    (e.g. "which is better", "between them") but names no products.
    The caller must then scan message history to find the referenced products.
    """
    return any(k in q for k in FOLLOWUP_COMPARE)