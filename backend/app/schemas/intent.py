from pydantic import BaseModel, Field
from typing import Optional, Literal

from app.core.enums import ChatIntent
class IntentResult(BaseModel):
    intent: ChatIntent = Field(index=True)
    origin: Optional[str]
    destination: Optional[str]
    departureDate: Optional[str]
    returnDate: Optional[str]
    adults: Optional[int]
