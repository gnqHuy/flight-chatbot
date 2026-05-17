from sqlalchemy import text
from sqlmodel import SQLModel, create_engine, Session
from constants import KNOWLEDGE_DATABASE_URL

from models.airline import Airline
from models.crawler_url import CrawlerUrl
from models.crawler_staging import CrawlerStaging
from models.flight_promotion import FlightPromotion
from models.pipeline_run import PipelineRun

engine = create_engine(KNOWLEDGE_DATABASE_URL, echo=False, pool_pre_ping=True)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session