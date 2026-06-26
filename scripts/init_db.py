from chatbot.database.database import Base, engine
from chatbot.database.models import Document

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Done!")