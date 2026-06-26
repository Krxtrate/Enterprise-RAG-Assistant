"""
core/retrieval.py
─────────────────
Every function that reads from ChromaDB and assembles context strings
for the LLM prompt lives here.

All builders are synchronous (blocking I/O).  The async /generate handler
dispatches them via `asyncio.get_event_loop().run_in_executor`.

Imports:
  • config          (limits, lists)
  • services/chroma (collection)
  • core/utils      (dedup_docs, cap_and_join)

No imports from intent, memory, prompts, or ollama → no circular risk.
"""

from typing import List

from sentence_transformers import SentenceTransformer

from chatbot.config import (
    EMBEDDING_MODEL,
    MAX_CHARS_PER_PRODUCT_OV,
    MAX_CONTEXT_CHARS,
    MAX_CONTEXT_CHARS_OVERVIEW,
    PRODUCT_LIST,
    TEAM_SOURCE_HINTS,
    TEAM_TITLE_KEYWORDS,
)
from chatbot.core.utils import cap_and_join, dedup_docs
from chatbot.services.chroma import collection

# ─────────────────────────────────────────────────────────────
# EMBEDDING MODEL (shared across all retrieval functions)
# ─────────────────────────────────────────────────────────────

print("Loading embedding model...")
embedder = SentenceTransformer(EMBEDDING_MODEL)


# ─────────────────────────────────────────────────────────────
# SINGLE-PRODUCT RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_product_context(product: str) -> str:
    """Fetch every chunk for a single product, deduplicated, capped."""
    try:
        r = collection.get(where={"product": product})
    except Exception as e:
        print(f"PRODUCT FETCH '{product}' failed: {e}")
        return "NO_RELEVANT_COMPANY_INFORMATION"

    pairs   = dedup_docs(r.get("documents", []) or [], r.get("metadatas", []) or [], label=product)
    entries = [f"PRODUCT: {product}\nSOURCE: {m.get('source','unknown')}\n\n{d}" for d, m in pairs]
    print(f"PRODUCT CONTEXT '{product}': {len(entries)} unique chunks")
    return cap_and_join(entries, MAX_CONTEXT_CHARS)


# ─────────────────────────────────────────────────────────────
# TEAM / LEADERSHIP RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_team_context() -> str:
    """
    Fetch chunks that contain leadership/team info.
    Two passes: source-name hint first, then content keyword scan.
    Both passes share the same dedup set so nothing is counted twice.
    """
    try:
        r = collection.get()
    except Exception as e:
        print(f"TEAM FETCH failed: {e}")
        return "NO_RELEVANT_COMPANY_INFORMATION"

    docs  = r.get("documents", []) or []
    metas = r.get("metadatas", []) or []
    pairs = dedup_docs(docs, metas, label="team-all")

    seen_keys: set       = set()
    entries:   List[str] = []

    def _add(doc: str, meta: dict) -> None:
        key = doc.strip()
        if key in seen_keys:
            return
        seen_keys.add(key)
        entries.append(f"SOURCE: {meta.get('source','unknown')}\n\n{doc}")

    # Pass 1: source name suggests team/about content
    for doc, meta in pairs:
        src = (meta.get("source") or "").lower()
        if any(hint in src for hint in TEAM_SOURCE_HINTS):
            _add(doc, meta)

    # Pass 2: text contains a leadership title keyword
    for doc, meta in pairs:
        if any(kw in (doc or "").lower() for kw in TEAM_TITLE_KEYWORDS):
            _add(doc, meta)

    print(f"TEAM CONTEXT: {len(entries)} chunks")
    return cap_and_join(entries, MAX_CONTEXT_CHARS)


# ─────────────────────────────────────────────────────────────
# PRODUCT LISTING RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_product_listing_context() -> str:
    """
    Build context for 'list all your products' queries.
    Strategy:
      1. One guaranteed 'priority' slot per product (first unique chunk).
      2. Remaining unique chunks go into 'backfill'.
      3. Combine priority + backfill and cap.
    This ensures every product gets at least one chunk before any product
    can push others out via backfill.
    """
    seen_content: set       = set()
    priority:     List[str] = []
    backfill:     List[str] = []

    for product in PRODUCT_LIST:
        try:
            r = collection.query(
                query_texts=[product],
                where={"product": product},
                n_results=1,
            )
        except Exception as e:
            print(f"LISTING FETCH '{product}' failed: {e}")
            continue

        docs  = r.get("documents", [[]])[0]
        metas = r.get("metadatas", [[]])[0]
        pairs = dedup_docs(docs, metas, label=product)

        first = True
        for doc, meta in pairs:
            key = doc.strip()
            if key in seen_content:
                continue
            seen_content.add(key)
            entry = f"PRODUCT: {product}\nSOURCE: {meta.get('source','unknown')}\n\n{doc}"
            if first:
                priority.append(entry)
                first = False
            else:
                backfill.append(entry)

    combined = priority + backfill
    print(
        f"PRODUCT LISTING: {len(priority)} priority + "
        f"{len(backfill)} backfill = {len(combined)} total"
    )
    return cap_and_join(combined, MAX_CONTEXT_CHARS_OVERVIEW)


# ─────────────────────────────────────────────────────────────
# COMPANY OVERVIEW RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_overview_context() -> str:
    """
    Build context for broad 'tell me about AdCounty' queries.
    Strategy:
      Pass 1: general / untagged chunks (about page, leadership, history, awards).
              These go FIRST so the cap never drops them in favour of product data.
      Pass 2: up to MAX_CHARS_PER_PRODUCT_OV chars per product (priority slot).
      Pass 3: remaining product chunks (overflow).
    """
    try:
        r = collection.get()
    except Exception as e:
        print(f"OVERVIEW FETCH failed: {e}")
        return "NO_RELEVANT_COMPANY_INFORMATION"

    pairs = dedup_docs(
        r.get("documents", []) or [],
        r.get("metadatas", []) or [],
        label="overview",
    )

    product_buckets: dict[str, List[str]] = {p: [] for p in PRODUCT_LIST}
    general: List[str] = []

    for doc, meta in pairs:
        product = (meta.get("product") or "").strip()
        source  = meta.get("source", "unknown")
        entry   = (
            f"PRODUCT: {product}\nSOURCE: {source}\n\n{doc}"
            if product in product_buckets
            else f"SOURCE: {source}\n\n{doc}"
        )
        if product in product_buckets:
            product_buckets[product].append(entry)
        else:
            general.append(entry)

    priority: List[str] = []
    overflow: List[str] = []
    for product in PRODUCT_LIST:
        budget = MAX_CHARS_PER_PRODUCT_OV
        for entry in product_buckets[product]:
            if budget > 0:
                priority.append(entry)
                budget -= len(entry)
            else:
                overflow.append(entry)

    combined = general + priority + overflow

    for p in PRODUCT_LIST:
        n  = len(product_buckets[p])
        ch = sum(len(e) for e in product_buckets[p])
        np = sum(1 for e in priority if f"PRODUCT: {p}" in e)
        print(f"  OVERVIEW '{p}': {n} chunks, {ch} chars, {np} in priority")
    print(
        f"OVERVIEW: {len(general)} general + "
        f"{len(priority)} priority + {len(overflow)} overflow"
    )
    return cap_and_join(combined, MAX_CONTEXT_CHARS_OVERVIEW)


# ─────────────────────────────────────────────────────────────
# SEMANTIC FALLBACK RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_semantic_context(question: str) -> str:
    """
    Vector search fallback for generic company questions with no specific product.
    """
    try:
        embedding = embedder.encode(question).tolist()
        r = collection.query(query_embeddings=[embedding], n_results=5)
    except Exception as e:
        print(f"SEMANTIC FETCH failed: {e}")
        return "NO_RELEVANT_COMPANY_INFORMATION"

    docs  = r.get("documents", [[]])[0]
    metas = r.get("metadatas", [[]])[0]
    dists = r.get("distances", [[]])[0]
    print(f"SEMANTIC DISTANCES: {[round(d, 3) for d in dists]}")

    pairs   = dedup_docs(docs, metas, label="semantic")
    entries = [f"SOURCE: {m.get('source','unknown')}\n\n{d}" for d, m in pairs]
    return cap_and_join(entries, MAX_CONTEXT_CHARS)


# ─────────────────────────────────────────────────────────────
# COMPARISON RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_comparison_context(products: List[str]) -> str:
    """
    Fetch context for each product in a comparison query.
    Each product gets its own capped budget so one large product
    can't crowd out the others.
    """
    per_product_cap = MAX_CONTEXT_CHARS // max(len(products), 1)
    all_entries: List[str] = []

    for product in products:
        try:
            r = collection.get(where={"product": product})
        except Exception as e:
            print(f"COMPARISON FETCH '{product}' failed: {e}")
            continue

        pairs = dedup_docs(
            r.get("documents", []) or [],
            r.get("metadatas", []) or [],
            label=f"comparison-{product}",
        )
        entries = [
            f"PRODUCT: {product}\nSOURCE: {m.get('source','unknown')}\n\n{d}"
            for d, m in pairs
        ]
        # Cap each product individually before combining
        capped = cap_and_join(entries, per_product_cap)
        if capped != "NO_RELEVANT_COMPANY_INFORMATION":
            all_entries.append(capped)
        print(f"COMPARISON '{product}': {len(entries)} chunks, capped to {per_product_cap} chars")

    if not all_entries:
        return "NO_RELEVANT_COMPANY_INFORMATION"

    combined = "\n\n".join(all_entries)
    print(f"COMPARISON CONTEXT: {len(products)} products, {len(combined)} total chars")
    return combined


# ─────────────────────────────────────────────────────────────
# MULTI-PRODUCT RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_multi_product_context(products: List[str]) -> str:
    """Concatenate individually-capped product contexts with clear section dividers."""
    sections = []
    for product in products:
        sections.append(
            f"""
        =========================
        PRODUCT: {product}
        =========================

        {build_product_context(product)}
        """
        )
    return "\n\n".join(sections)


# ─────────────────────────────────────────────────────────────
# GLOBAL / GITBOOK RETRIEVAL
# ─────────────────────────────────────────────────────────────

def build_global_context(question: str) -> str:
    """
    Vector search scoped to the gitbook source.
    Used as:
      • Primary retrieval for technical / API / macro questions.
      • Automatic fallback when all other retrievers return nothing.
    """
    try:
        embedding = embedder.encode(question).tolist()
        r = collection.query(
            query_embeddings=[embedding],
            where={"source": "gitbook"},
            n_results=8,
        )
    except Exception as e:
        print(f"GLOBAL SEARCH failed: {e}")
        return "NO_RELEVANT_COMPANY_INFORMATION"

    docs  = r.get("documents", [[]])[0]
    metas = r.get("metadatas", [[]])[0]
    pairs = dedup_docs(docs, metas, "global")
    entries = [
        f"SOURCE: {m.get('source','unknown')}\n"
        f"PRODUCT: {m.get('product','')}\n\n"
        f"{d}"
        for d, m in pairs
    ]
    return cap_and_join(entries, MAX_CONTEXT_CHARS)