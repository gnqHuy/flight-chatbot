import os
import logging
from langchain_postgres.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

logger = logging.getLogger(__name__)

DATABASE_URL  = os.getenv("DATABASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
COLLECTION_NAME = "flight_policies"

_policy_store: PGVector | None = None
_embeddings: OpenAIEmbeddings | None = None


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )
    return _embeddings


def get_policy_vector_store() -> PGVector:
    global _policy_store
    if _policy_store is None:
        _policy_store = PGVector(
            embeddings=get_embeddings(),
            collection_name=COLLECTION_NAME,
            connection=DATABASE_URL,
            use_jsonb=True,
        )
        logger.info(f"PGVector store '{COLLECTION_NAME}' initialized")
    return _policy_store