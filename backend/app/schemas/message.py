from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime

class MessageCreate(SQLModel):
    conversation_id: UUID
    role: str
    content: str

class MessageRead(SQLModel):
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    created_at: datetime
