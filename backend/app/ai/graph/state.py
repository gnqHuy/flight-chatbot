from typing import Optional, List, Dict
from pydantic import BaseModel

class ChatState(BaseModel):
    user_message: str
    intent: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departureDate: Optional[str] = None
    returnDate: Optional[str] = None
    adults: Optional[int] = None
    flight_offers: Optional[List[Dict]] = None
    response_text: Optional[str] = None
