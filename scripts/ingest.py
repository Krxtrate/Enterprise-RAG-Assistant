from chatbot.database import SessionLocal
from chatbot.database.models import Document, Chunk


CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


print("\nReading knowledge files...")

db = SessionLocal()

db.query(Chunk).delete()
db.commit()

documents = db.query(Document).all()

for document in documents:

    text = document.content

    url_lower = document.url.lower()

    print(document.url)

    print(
        f"Processing: {document.url}"
    )

    company = "general"


    product = None

    if "opsis" in url_lower:
        company = "opsis"
        product = "OpSIS Pro"

    elif "bidcounty" in url_lower:
        company = "bidcounty"
        product = "BidCounty"

    elif "gam360" in url_lower:
        company = "gam360"
        product = "GAM360"

    elif "isearch" in url_lower:
        company = "isearch"
        product = "iSearchAds"

    elif "genwin" in url_lower:
        company = "genwin"
        product = "GenWin"

    elif "seetv" in url_lower:
        company = "seetv"
        product = "SeeTV"

    # Product files = one chunk

    if company != "general":

        db.add(
            Chunk(
                document_id=document.id,
                chunk_index=0,
                text=text.strip(),
                product=product,
                source=document.source
            )
        )

    # General files = chunk normally

    else:

        chunk_index = 0
        current_chunk = ""

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            current_chunk += line + "\n"

            if len(current_chunk) >= CHUNK_SIZE:

                db.add(
                    Chunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        text=current_chunk.strip(),
                        product=None,
                        source=document.source
                    )
                )

                chunk_index += 1
                current_chunk = ""

        if current_chunk:

                db.add(
                    Chunk(
                        document_id=document.id,
                        chunk_index=chunk_index,
                        text=current_chunk.strip(),
                        product=None,
                        source=document.source
                    )
                )

                chunk_index += 1
    db.commit()

db.close()

print("Chunk ingestion completed successfully!")