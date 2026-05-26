import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool 
from dotenv import load_dotenv
from app.core.config import CHECKPOINT_DATABASE_URL

load_dotenv()

db_uri = CHECKPOINT_DATABASE_URL
if not db_uri:
    raise ValueError("Chưa cấu hình DATABASE_URL trong file .env")

if "postgresql+psycopg2://" in db_uri:
    db_uri = db_uri.replace("postgresql+psycopg2://", "postgresql://")

async_pool = AsyncConnectionPool(
    conninfo=db_uri,
    max_size=20,
    kwargs={"autocommit": True},
    open=False 
)
checkpointer = None

def get_checkpointer():
    """Hàm này chỉ trả về object, không làm block hệ thống nữa"""
    return checkpointer