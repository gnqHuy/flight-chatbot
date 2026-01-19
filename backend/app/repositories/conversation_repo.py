from sqlmodel import Session, select
from datetime import datetime, timezone
from uuid import UUID
from app.database.models.conversation import Conversation

class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, id: UUID, user_id: UUID | None = None, title: str = "New Chat") -> Conversation:
        convo = Conversation(
            id=id,
            user_id=user_id,
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        self.session.add(convo)
        self.session.commit()
        self.session.refresh(convo)
        return convo

    def get_by_id(self, conversation_id: UUID) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        return self.session.exec(stmt).first()

    def update_timestamp(self, conversation_id: UUID) -> Conversation | None:
        convo = self.get_by_id(conversation_id)
        if convo:
            convo.updated_at = datetime.now(timezone.utc)
            self.session.add(convo)
            self.session.commit()
            self.session.refresh(convo)
        return convo
    
    def get_by_user(self, user_id: UUID, limit: int = 20, offset: int = 0) -> list[Conversation]:
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return self.session.exec(stmt).all()