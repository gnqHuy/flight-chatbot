from fastapi import APIRouter, Depends
from typing import List
from uuid import UUID
from sqlmodel import Session

from app.api.deps import get_current_user
from app.database.database import get_session
from app.database.models.user import User
from app.schemas.conversation import ConversationRead
from app.schemas.message import MessageRead

from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("/", response_model=List[ConversationRead])
def get_user_conversations(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    
    service = ConversationService(conv_repo, msg_repo)
    
    return service.get_user_conversations(user_id=current_user.id)

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
def get_conversation_history(
    conversation_id: UUID,
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    return service.get_conversation_history(conversation_id)

@router.post("/create", response_model=ConversationRead)
def create_conversation(
    current_user: User = Depends(get_current_user),
    title: str = "New Chat",
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    
    service = ConversationService(conv_repo, msg_repo)
    
    return service.create_conversation(user_id=current_user.id, title=title)

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: UUID, 
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    service.delete_conversation(conversation_id)
    return {"status": "success"}