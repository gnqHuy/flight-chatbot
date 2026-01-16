from sqlmodel import SQLModel, create_engine, Session
from app.core.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    connect_args={"options": "-csearch_path=public"},
    echo=True
)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
