import os
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg_pool import ConnectionPool
from dotenv import load_dotenv

load_dotenv()

def get_checkpointer():
    db_uri = os.getenv("DATABASE_URL")
    
    if not db_uri:
        raise ValueError("Chưa cấu hình DATABASE_URL trong file .env")

    if "postgresql+psycopg2://" in db_uri:
        db_uri = db_uri.replace("postgresql+psycopg2://", "postgresql://")
    
    pool = ConnectionPool(
        conninfo=db_uri,
        max_size=20,
        kwargs={"autocommit": True}
    )

    checkpointer = PostgresSaver(pool)
    checkpointer.setup()
    
    return checkpointer