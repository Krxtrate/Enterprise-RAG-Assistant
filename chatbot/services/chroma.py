"""
services/chroma.py
──────────────────
ChromaDB initialisation.

Exposes a single `collection` object that every retrieval function
imports.  Keeping this isolated means swapping to a remote ChromaDB
server only requires changes in this one file.

Imports: config only (no other internal modules → no circular risk).
"""

import chromadb
import os
from chatbot.config import CHROMA_COLLECTION_NAME, CHROMA_DB_PATH

# ─────────────────────────────────────────────────────────────
# CLIENT & COLLECTION
# ─────────────────────────────────────────────────────────────

print("Connecting to ChromaDB...")
print("Database path:", CHROMA_DB_PATH)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
collection    = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)
print("Collection count:", collection.count())

print("Configured DB path:", CHROMA_DB_PATH)
print("Resolved DB path:", os.path.abspath(CHROMA_DB_PATH))
print("Collections:")
for c in chroma_client.list_collections():
    print("-", c.name)
print("Collection:", CHROMA_COLLECTION_NAME)
print("Count:", collection.count())

# ─────────────────────────────────────────────────────────────
# STARTUP DIAGNOSTICS
# ─────────────────────────────────────────────────────────────

_boot = collection.get()
print("Products in DB:", {m.get("product", "") for m in _boot["metadatas"]})
print("Sources in DB:", sorted({m.get("source", "") for m in _boot["metadatas"]}))