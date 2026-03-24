from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, Date
from datetime import datetime, date, timezone
from typing import Optional, List
from pgvector.sqlalchemy import Vector

class FlightPromotion(SQLModel, table=True):
    __tablename__ = "flight_promotions"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    airline: str = Field(max_length=10, index=True)
    promo_code: Optional[str] = Field(default=None, max_length=50, index=True)
    
    promo_name: str = Field(sa_column=Column(Text, nullable=False))
    
    booking_start_date: Optional[date] = Field(default=None, sa_column=Column(Date))
    booking_end_date: Optional[date] = Field(default=None, sa_column=Column(Date, index=True))
    
    travel_period: Optional[str] = Field(default=None, sa_column=Column(Text))
    description: str = Field(sa_column=Column(Text, nullable=False))
    conditions: str = Field(sa_column=Column(Text, nullable=False))
    url: str = Field(sa_column=Column(Text, nullable=False))

    embedding: Optional[List[float]] = Field(
        default=None, 
        sa_column=Column(Vector(1536))
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))