from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql://postgres:admin@localhost:5432/enterprise_rag"
)

with engine.connect() as conn:
    print("Connected successfully!")

    result = conn.execute(text("SELECT * FROM documents"))

    for row in result:
        print(row)