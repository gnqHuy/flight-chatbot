from sqlmodel import Session, select
from app.database.models.conversation import Conversation
from uuid import UUID

class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: UUID | None) -> Conversation:
        convo = Conversation(
            user_id=user_id,
            state_json={}
        )
        self.session.add(convo)
        self.session.commit()
        self.session.refresh(convo)
        return convo

    def get(self, conversation_id: UUID) -> Conversation | None:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        return self.session.exec(stmt).first()

    def update_state(self, convo: Conversation, new_state: dict):
        convo.state_json = new_state
        self.session.add(convo)
        self.session.commit()
        self.session.refresh(convo)
        return convo
