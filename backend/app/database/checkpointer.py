import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# ĐỔI SANG DÙNG POOL ASYNC
from psycopg_pool import AsyncConnectionPool 
from dotenv import load_dotenv

load_dotenv()

db_uri = os.getenv("DATABASE_URL")
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

checkpointer = AsyncPostgresSaver(async_pool)

def get_checkpointer():
    """Hàm này chỉ trả về object, không làm block hệ thống nữa"""
    return checkpointer