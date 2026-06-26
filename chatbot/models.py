"""
models.py
─────────
Pydantic request and response models.

No internal imports — safe to import from anywhere.
"""

from typing import List, Optional

from pydantic import BaseModel


class Message(BaseModel):
    role:    str
    content: Optional[str] = ""


class ChatRequest(BaseModel):
    messages: List[Message]
    company:  str = "general"