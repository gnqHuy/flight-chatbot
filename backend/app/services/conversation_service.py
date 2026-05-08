from uuid import UUID, uuid4
from typing import List
from fastapi import HTTPException

from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.conversation import ConversationRead
from app.schemas.message import MessageRead

class ConversationService:
    def __init__(self, 
                 conversation_repo: ConversationRepository, 
                 message_repo: MessageRepository):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    def create_conversation(self, user_id: UUID, title: str) -> ConversationRead:
        convo = self.conversation_repo.create(id=uuid4(), user_id=user_id, title=title)
        return convo

    def get_user_conversations(self, user_id: UUID, limit: int = 20, offset: int = 0) -> List[ConversationRead]:
        return self.conversation_repo.get_by_user(user_id, limit, offset)

    def get_conversation_history(self, conversation_id: UUID) -> List[MessageRead]:
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return self.message_repo.get_by_conversation_id(conversation_id)

    def delete_conversation(self, conversation_id: UUID):
        conversation = self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return self.conversation_repo.delete(conversation_id)