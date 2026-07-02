"""
config.py
─────────
Single source of truth for every constant in the application.

Nothing in here imports from any other internal module, so it can be
safely imported by every other module without creating circular imports.
"""

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# EXTERNAL SERVICE URLS & MODEL SETTINGS
# ─────────────────────────────────────────────────────────────

# Hugging Face Inference API — primary backend, tried first.
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
HF_MODEL     = os.environ.get("HF_MODEL")
HF_API_URL   = "https://router.huggingface.co/v1/chat/completions"

# Local Ollama — used as automatic fallback if HF Inference API fails.
# Must be reachable on this server for the fallback to actually work.
OLLAMA_URL   = "http://localhost:11434"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")

# ─────────────────────────────────────────────────────────────
# EMBEDDING MODEL
# ─────────────────────────────────────────────────────────────

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ─────────────────────────────────────────────────────────────
# CHROMADB SETTINGS + SMALLTALK DIRECTORY
# ─────────────────────────────────────────────────────────────

# Project root (C:\Internship)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
URLS_FILE = DATA_DIR / "urls.txt"
CHROMA_DB_PATH = str(DATA_DIR / "knowledge")
SMALLTALK_DIR = str(DATA_DIR / "smalltalk")

CHROMA_COLLECTION_NAME = "company_knowledge"

# ─────────────────────────────────────────────────────────────
# MCP TRANSPORT SETTING
# ─────────────────────────────────────────────────────────────

MCP_TRANSPORT = "stdio"   
MCP_SERVER_NAME = "AdCounty Chatbot"

# ─────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────
# CONTEXT CHAR BUDGETS
# RTX 3050 6 GB: model weights ~4.7 GB (Q4), leaving ~1.3 GB for KV cache.
# At 4096 ctx, KV cache ≈ 0.5 GB — safe. At 8192 it doubles and spills to RAM → slow.
# Single-product / team queries stay at ≤ 4096.
# Overview / listing queries can afford 8192 because desired_predict is higher
# and the VRAM pressure is bounded by MAX_CONTEXT_CHARS_OVERVIEW.
# ─────────────────────────────────────────────────────────────

MAX_CONTEXT_CHARS          = 16_000   # single-product / team / generic
MAX_CONTEXT_CHARS_OVERVIEW = 20_000   # overview / product listing
MAX_CHARS_PER_PRODUCT_OV   =  2_500   # per-product cap inside overview

# ─────────────────────────────────────────────────────────────
# PRODUCT / KEYWORD TABLES
# ─────────────────────────────────────────────────────────────

# Longest keyword first so "opsis pro" matches before bare "opsis"
PRODUCT_NAME_MAP: dict[str, str] = {
    "opsis pro":  "OpSIS Pro",
    "opsis":      "OpSIS Pro",
    "bidcounty":  "BidCounty",
    "gam360":     "GAM360",
    "genwin":     "GenWin",
    "isearchads": "iSearchAds",
    "isearch":    "iSearchAds",
    "seetv":      "SeeTV",
}

# Stable insertion-ordered list — dict.fromkeys removes value duplicates
PRODUCT_LIST: List[str] = list(dict.fromkeys(PRODUCT_NAME_MAP.values()))

HARD_COMPANY_SIGNALS: List[str] = [
    "adcounty", "adcounty media",
    "bidcounty", "gam360", "isearchads", "isearch",
    "genwin", "seetv", "opsis pro", "opsis",
]

COMPANY_KEYWORDS: List[str] = [
    "adcounty", "adcounty media", "company", "service", "services",
    "product", "products", "contact", "support", "career", "careers",
    "internship", "employee", "office", "address", "email", "phone",
    "opsis", "bidcounty", "gam360", "isearch", "genwin", "seetv",
    "cfo", "cro", "cto", "cso", "founder", "co-founder", "cofounder",
    "chairman", "director", "leadership", "team", "management",
    "executive", "advisor", "board", "md",
]

TEAM_KEYWORDS: List[str] = [
    "team", "leadership", "management", "board", "advisor",
    "founder", "cfo", "cro", "cto", "cso", "chairman", "director",
]

TEAM_TITLE_KEYWORDS: List[str] = [
    "leadership", "founder", "co-founder", "chairman",
    "chief executive", "chief financial", "chief technology",
    "chief revenue", "chief strategy", "chief operating",
    "managing director", " md ", "cfo", "cto", "cro", "cso",
    "ceo", "coo", "board advisor", "board member", "director",
    "vice president", " vp ",
]

TEAM_SOURCE_HINTS: List[str] = [
    "about-us", "about", "leadership", "management", "team", "board",
]

COMPANY_OVERVIEW_TRIGGERS: List[str] = [
    "about adcounty", "about adcounty media", "tell me about adcounty",
    "tell me about your company", "what else can you tell me",
    "company overview", "about the company", "who are you",
]

FOLLOWUP_TRIGGERS: List[str] = [
    "what does it do", "tell me more", "explain further", "more details",
    "give me more", "elaborate", "expand on that", "detailed description",
    "more info", "what else",
]

COMPARISON_TRIGGERS: List[str] = [
    "compare", "comparison", "vs", "versus", "difference", "better",
    "best", "which", "which one", "recommend", "suggest", "prefer",
    "more suitable", "more appropriate", "good for", "ideal for",
]

PRODUCT_LISTING_PHRASES: List[str] = [
    "all products", "your products", "company products",
    "products offered", "products do you offer", "products do you have",
    "products you offer", "what are your products", "which products do you",
    "products list", "product list", "list of products",
]

PRODUCT_LISTING_MODIFIERS: List[str] = [
    "all", "describe", "description", "detail", "detailed",
    "overview", "list", "tell me", "offer", "have", "portfolio", "catalog",
]

TECHNICAL_TERMS: List[str] = [
    "macro", "macros", "parameter", "parameters", "api", "tracking", "tracking parameter",
    "placeholder", "postback", "postback url", "click id", "clickid", "utm", "s2s", "sdk",
    "integration", "endpoint", "token", "campaign id", "publisher id", "offer id", "advertiser",
    "pixel", "callback", "setup", "configuration", "xml", "json", "csv", "documentation",
]

FOLLOWUP_COMPARE: List[str] = [
    "between them", "between those", "which is better", "which one",
    "better", "best", "compare them", "among them",
]

# ─────────────────────────────────────────────────────────────
# THREAD POOL / CONCURRENCY SETTINGS
# ─────────────────────────────────────────────────────────────

THREAD_POOL_MAX_WORKERS = 4