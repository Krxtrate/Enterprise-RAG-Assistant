"""
patch_chroma.py
---------------
Patches ChromaDB directly with enriched knowledge for BidCounty and GenWin.
Run this script once after updating the knowledge .txt files.
It REPLACES existing chunks for the two products without touching any other data.

Usage:
    python patch_chroma.py
"""

import chromadb
import os
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "company_knowledge"
KNOWLEDGE_DIR = "./knowledge"

PRODUCTS_TO_PATCH = {
    "BidCounty": "products_bidcounty.txt",
    "GenWin":    "products_genwin.txt",
}

CHUNK_SIZE    = 1500   # characters per chunk (larger = more context per retrieval)
CHUNK_OVERLAP = 200

print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

print("Connecting to ChromaDB...")
client     = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)

# ── Helper: split text into overlapping chunks ──────────────────────────────

def split_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into chunks of ~chunk_size chars with overlap."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end].strip())
        start += chunk_size - overlap
    return [c for c in chunks if c]   # drop empty

# ── For each product: delete old chunks, add new ones ───────────────────────

for product, filename in PRODUCTS_TO_PATCH.items():
    filepath = os.path.join(KNOWLEDGE_DIR, filename)

    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath} — skipping {product}")
        continue

    with open(filepath, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()

    # 1. Find existing IDs for this product
    existing = collection.get(where={"product": product})
    old_ids  = existing.get("ids", [])
    print(f"\n[{product}] Found {len(old_ids)} existing chunks -> deleting...")

    if old_ids:
        collection.delete(ids=old_ids)

    # 2. Chunk the new text
    chunks = split_chunks(raw_text)
    print(f"[{product}] Ingesting {len(chunks)} new chunk(s) from '{filename}'...")

    for i, chunk in enumerate(chunks):
        embedding = model.encode(chunk).tolist()
        chunk_id  = f"patch_{product.lower().replace(' ', '_')}_{i}"
        source    = filename.replace(".txt", "")

        collection.add(
            ids        =[chunk_id],
            documents  =[chunk],
            embeddings =[embedding],
            metadatas  =[{
                "source":      source,
                "url":         f"knowledge/{filename}",
                "title":       product,
                "company":     product.lower().replace(" ", ""),
                "product":     product,
                "doc_type":    "product",
                "document_id": -1,
            }],
        )
        print(f"  OK Chunk {i+1}/{len(chunks)} - {len(chunk)} chars")


print(f"\nTotal chunks in collection: {collection.count()}")
print("\nDONE: ChromaDB patch complete. Restart the FastAPI server to pick up changes.")
