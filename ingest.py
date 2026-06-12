import os
import chromadb

from sentence_transformers import SentenceTransformer

# ==========================================
# CONFIG
# ==========================================

CHUNK_SIZE = 1000

# ==========================================
# LOAD EMBEDDING MODEL
# ==========================================

print("Loading embedding model...")

model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# ==========================================
# CONNECT TO CHROMADB
# ==========================================

print("Connecting to ChromaDB...")

client = chromadb.PersistentClient(
    path="./chroma_db"
)

# ==========================================
# DELETE OLD COLLECTION
# ==========================================

try:
    client.delete_collection(
        name="company_knowledge"
    )

    print("Old collection deleted.")

except Exception:

    print("No existing collection found.")

collection = client.get_or_create_collection(
    name="company_knowledge"
)

# ==========================================
# READ KNOWLEDGE FOLDER
# ==========================================

knowledge_folder = "knowledge"

if not os.path.exists(knowledge_folder):
    raise FileNotFoundError(
        "knowledge folder not found."
    )

all_chunks = []

print("\nReading knowledge files...")

for root, dirs, files in os.walk(
    knowledge_folder
):

    for filename in files:

        if not filename.endswith(".txt"):
            continue

        file_path = os.path.join(
            root,
            filename
        )

        print(
            f"Processing: {file_path}"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

        current_chunk = ""

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            current_chunk += (
                line + "\n"
            )

            if len(current_chunk) >= CHUNK_SIZE:

                all_chunks.append({
                    "source": file_path,
                    "text": current_chunk.strip()
                })

                current_chunk = ""

        if current_chunk:

            all_chunks.append({
                "source": file_path,
                "text": current_chunk.strip()
            })

    current_chunk = ""

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        current_chunk += (
            line + "\n"
        )

        if len(current_chunk) >= CHUNK_SIZE:

            all_chunks.append({
                "source": file_path,
                "text": current_chunk.strip()
            })

            current_chunk = ""

    if current_chunk:

        all_chunks.append({
            "source": file_path,
            "text": current_chunk.strip()
        })

# ==========================================
# STORE EMBEDDINGS
# ==========================================

print(
    f"\nFound {len(all_chunks)} chunks"
)

for i, chunk_data in enumerate(
    all_chunks
):

    chunk = chunk_data["text"]

    embedding = model.encode(
        chunk
    ).tolist()

    collection.add(
        ids=[
            f"chunk_{i}"
        ],
        documents=[
            chunk
        ],
        embeddings=[
            embedding
        ],
        metadatas=[
            {
                "source":
                chunk_data["source"]
            }
        ]
    )

    print(
        f"Added chunk {i+1}/{len(all_chunks)}"
    )

# ==========================================
# VERIFY DATABASE
# ==========================================

print("\n================================")

print(
    f"Total Chunks Stored: {collection.count()}"
)

print(
    "Knowledge base created successfully!"
)

print("================================")