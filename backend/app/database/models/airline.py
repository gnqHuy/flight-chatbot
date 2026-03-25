from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, Text
from typing import Optional, List

class Airline(SQLModel, table=True):
    __tablename__ = "airlines"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True, unique=True, max_length=10)
    name: str = Field(max_length=100)
    website_url: str = Field(max_length=255)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    hotline: Optional[str] = Field(default=None, max_length=50)
    
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    pros: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    cons: Optional[List[str]] = Field(default=[], sa_column=Column(JSON))
    baggage_basic_info: Optional[str] = Field(default=None, sa_column=Column(Text))

    promotions: List["FlightPromotion"] = Relationship(back_populates="airline")
    crawler_urls: List["CrawlerUrl"] = Relationship(back_populates="airline")