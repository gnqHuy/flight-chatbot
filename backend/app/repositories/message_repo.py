import uuid
from sqlmodel import Session, select
from typing import List
from uuid import UUID
from datetime import datetime, timezone
from app.database.models.message import Message

class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, conversation_id: UUID, role: str, content: str, id: UUID | None = None) -> Message:
        if id is None:
            id = uuid.uuid4()
            
        msg = Message(
            id=id,
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def get_by_conversation_id(self, conversation_id: UUID, limit: int = 100, offset: int = 0) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(stmt).all()