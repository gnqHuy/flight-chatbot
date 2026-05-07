from datetime import datetime
from typing import Optional

from sqlalchemy import Text
from sqlmodel import Column, Field, SQLModel


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipeline_runs"

    id:           str           = Field(primary_key=True)
    pipeline_type: str          = Field(index=True) 
    status:       str           = Field(default="running")
    started_at:   datetime      = Field(default_factory=datetime.now)
    finished_at:  Optional[datetime] = Field(default=None)
    urls_discovered: int        = Field(default=0)
    urls_crawled:    int        = Field(default=0)
    urls_ingested:   int        = Field(default=0)
    llm_tokens_used:  int   = Field(default=0)
    llm_cost_usd:     float = Field(default=0.0)
    error_message:  Optional[str] = Field(default=None, sa_column=Column(Text))