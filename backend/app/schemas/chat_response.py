from enum import Enum
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

from app.core.enums import ChatIntent, ChatRole, ComponentType

class ClientAction(BaseModel):
    type: ComponentType = ComponentType.NONE
    payload: Dict[str, Any] = Field(default_factory=dict) 

class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: Optional[UUID] = Field(
        default=None, 
        description="ID của cuộc hội thoại (Session ID)"
    )
    role: ChatRole
    content: str
    intent: ChatIntent
    
    action: Optional[ClientAction] = None