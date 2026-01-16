from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID, uuid4

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)

    conversation_id: UUID = Field(
        foreign_key="conversations.id",
        index=True
    )

    role: str
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    conversation: "Conversation" = Relationship(back_populates="messages")
