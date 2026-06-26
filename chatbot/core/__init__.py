# core package

from .intent import detect_intent
from .router import route_context
from .retrieval import (
    build_product_context,
    build_comparison_context,
)