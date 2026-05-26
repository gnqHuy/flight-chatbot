from sqlmodel import SQLModel, create_engine, Session
from app.core.config import BACKEND_DATABASE_URL
from app.database.models import *

engine = create_engine(
    BACKEND_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session