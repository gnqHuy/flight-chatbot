from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = Field(
        default=None, 
        description="ID của cuộc hội thoại (Session ID)"
    )
    
    message: str = Field(..., min_length=1, description="Nội dung tin nhắn user")