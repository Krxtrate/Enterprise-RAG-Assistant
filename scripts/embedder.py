import chromadb

from sentence_transformers import SentenceTransformer

from chatbot.database import SessionLocal
from chatbot.database.models import Chunk
from chatbot.config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
)

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path=CHROMA_DB_PATH
)

try:
    client.delete_collection(
        CHROMA_COLLECTION_NAME
    )
    print("Old collection deleted.")
except Exception:
    print("No existing collection.")

collection = client.get_or_create_collection(
    CHROMA_COLLECTION_NAME
)

db = SessionLocal()

chunks = db.query(Chunk).all()

print(f"Embedding {len(chunks)} chunks...\n")

for chunk in chunks:

    embedding = model.encode(
        chunk.text
    ).tolist()

    collection.add(

        ids=[
            f"chunk_{chunk.id}"
        ],

        documents=[
            chunk.text
        ],

        embeddings=[
            embedding
        ],

        metadatas=[

            {
                "chunk_id": chunk.id,
                "document_id": chunk.document_id,
                "product": chunk.product or "",
                "source": chunk.source,
            }

        ]

    )

    print(
        f"Embedded chunk {chunk.id}"
    )

db.close()

print("\n================================")
print(f"Stored {collection.count()} embeddings.")
print("Embedding complete.")
print("================================")