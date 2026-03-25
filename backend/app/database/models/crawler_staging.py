import enum
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, JSON, Enum as SaEnum
from typing import Optional
from datetime import datetime, timezone
from app.core.enums import StagingStatus

class CrawlerStaging(SQLModel, table=True):
    __tablename__ = "crawler_staging"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    url_id: int = Field(foreign_key="crawler_urls.id", index=True)
    airline_id: int = Field(foreign_key="airlines.id")
    
    raw_text: Optional[str] = Field(default=None, sa_column=Column(Text))
    formatted_data: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    
    status: StagingStatus = Field(
        default=StagingStatus.PENDING, 
        sa_column=Column(SaEnum(StagingStatus), nullable=False, index=True)
    )
    
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))