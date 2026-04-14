import os
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL", "")

engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-csearch_path=public"},
    echo=False,
    pool_pre_ping=True,
)

def init_db():
    """Tạo bảng nếu chưa có (chỉ gọi lúc startup)."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)