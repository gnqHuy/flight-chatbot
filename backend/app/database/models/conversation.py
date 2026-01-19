from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    title: str = Field(default="New Chat", max_length=255)

    user_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )

    current_intent: str | None = None
    status: str = Field(default="active")
    state_json: dict = Field(default={}, sa_column=Column(JSONB, default={}))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="conversations")
    
    messages: List["Message"] = Relationship(
        back_populates="conversation", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )