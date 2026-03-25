from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, String, Enum as SaEnum
from typing import Optional
from datetime import datetime
from app.core.enums import UrlType

class CrawlerUrl(SQLModel, table=True):
    __tablename__ = "crawler_urls"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    airline_id: int = Field(foreign_key="airlines.id", index=True)
    
    url_type: UrlType = Field(sa_column=Column(SaEnum(UrlType)))
    category: Optional[str] = Field(default=None, max_length=100)
    url: str = Field(sa_column=Column(String(1000)))
    
    is_active: bool = Field(default=True)
    last_crawled_at: Optional[datetime] = Field(default=None)
    
    airline: Optional["Airline"] = Relationship(back_populates="crawler_urls")