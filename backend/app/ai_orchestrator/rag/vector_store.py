
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from app.core.config import DATABASE_URL

shared_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

policy_vector_store = PGVector(
    embeddings=shared_embeddings,
    connection=DATABASE_URL,
    collection_name="flight_policies"
)

promo_vector_store = PGVector(
    embeddings=shared_embeddings,
    connection=DATABASE_URL,
    collection_name="flight_promos"
)