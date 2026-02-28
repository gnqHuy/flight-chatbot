import os
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

connection = os.environ.get("DATABASE_URL")
collection_name = "flight_policies"
embeddings = OpenAIEmbeddings()

vector_store = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)