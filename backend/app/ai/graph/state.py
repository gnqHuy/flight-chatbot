from typing import Optional, Dict, Any
from pydantic import BaseModel

class ChatState(BaseModel):
    user_message: str
    intent: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    departureDate: Optional[str] = None
    returnDate: Optional[str] = None
    adults: Optional[int] = None
    language: Optional[str] = "vi"
    response_text: Optional[str] = None
    error_msg: Optional[str] = None 
    action: Optional[Dict[str, Any]] = None