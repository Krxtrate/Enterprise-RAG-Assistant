"""
core/smalltalk.py
─────────────────
Loads all smalltalk intent JSON files at import time and provides
a single `match_smalltalk` function consumed by the /generate handler.

Imports:
  • config  (SMALLTALK_DIR)
  • core/utils (normalise)

No imports from retrieval, ollama, or chroma → no circular risk.
"""

import json
import os
import random
import re
from typing import Dict, List, Optional

from chatbot.config import SMALLTALK_DIR
from chatbot.core.utils import normalise

# ─────────────────────────────────────────────────────────────
# LOADER  (runs once at import time, same as original)
# ─────────────────────────────────────────────────────────────

smalltalk_lookup: Dict[str, List[dict]] = {}

if os.path.isdir(SMALLTALK_DIR):
    for _fname in os.listdir(SMALLTALK_DIR):
        if not _fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(SMALLTALK_DIR, _fname), "r", encoding="utf-8") as _f:
                _intent = json.load(_f)
            _responses = _intent["body"]["bot_says"]["en"]["en"]
            for _ex in _intent["body"]["user_says"]:
                if _ex.get("active"):
                    _key = re.sub(r"[^\w\s]", "", _ex["text"].lower()).strip()
                    smalltalk_lookup[_key] = _responses
        except Exception as _e:
            print(f"Smalltalk load failed ({_fname}): {_e}")
    print(f"Smalltalk: {len(smalltalk_lookup)} entries from {SMALLTALK_DIR}/")
else:
    print(f"WARNING: '{SMALLTALK_DIR}' directory not found — smalltalk disabled.")


# ─────────────────────────────────────────────────────────────
# MATCHER
# ─────────────────────────────────────────────────────────────

def match_smalltalk(user_text: str) -> Optional[List[dict]]:
    """
    Return the list of candidate responses for `user_text` if it matches
    a known smalltalk intent, or None if no match.

    The caller is responsible for picking a random response and rendering
    template placeholders via core.utils.render_smalltalk.
    """
    key = normalise(user_text)
    return smalltalk_lookup.get(key)


def pick_smalltalk_reply(candidates: List[dict]) -> str:
    """Pick one reply text at random from a list of smalltalk candidates."""
    return random.choice(candidates)["text"]