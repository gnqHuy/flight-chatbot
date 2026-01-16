from sqlmodel import Session
from app.database.models.message import Message
from uuid import UUID

class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        conversation_id: UUID,
        role: str,
        content: str
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content
        )
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg
