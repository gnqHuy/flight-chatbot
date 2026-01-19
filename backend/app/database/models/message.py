from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional

from app.core.enums import ChatRole

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    conversation_id: UUID = Field(
        foreign_key="conversations.id",
        index=True
    )

    role: ChatRole = Field(index=True)
    content: str
    
    action: dict | None = Field(default=None, sa_column=Column(JSONB, nullable=True))
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    conversation: "Conversation" = Relationship(back_populates="messages")