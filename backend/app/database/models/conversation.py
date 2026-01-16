from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"
    id: UUID = Field(default_factory=uuid4, primary_key=True)

    user_id: UUID | None = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )

    current_intent: str | None = None
    status: str = Field(default="active")
    state_json: dict = Field(sa_column=Column(JSONB))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional["User"] = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation")
