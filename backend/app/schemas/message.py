from pydantic import BaseModel, Field
from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime

from app.core.enums import ChatRole

class MessageCreate(SQLModel):
    conversation_id: UUID
    role: ChatRole = Field(index=True)
    content: str

class MessageRead(SQLModel):
    id: UUID
    conversation_id: UUID
    role: ChatRole = Field(index=True)
    content: str
    created_at: datetime
    action: dict | None = None

class MessageCreateBody(BaseModel):
    message: str