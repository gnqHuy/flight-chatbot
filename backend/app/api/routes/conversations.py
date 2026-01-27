from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlmodel import Session
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.database.database import get_session
from app.database.models.user import User
from app.schemas.conversation import ConversationRead
from app.schemas.message import MessageCreateBody, MessageRead
from app.schemas.chat_response import ChatResponse
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.services.conversation_service import ConversationService
from app.services.chat_service import ChatService

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("/", response_model=List[ConversationRead])
def get_user_conversations(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_session)
):
    """Lấy danh sách các cuộc trò chuyện của User hiện tại"""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    return service.get_user_conversations(user_id=current_user.id)

@router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
def create_conversation(
    current_user: User = Depends(get_current_user),
    title: str = "New Chat", 
    db: Session = Depends(get_session)
):
    """Tạo cuộc trò chuyện mới"""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    return service.create_conversation(user_id=current_user.id, title=title)

@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: UUID, 
    db: Session = Depends(get_session)
):
    """Xóa cuộc trò chuyện"""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    service.delete_conversation(conversation_id)
    return {"status": "success"}

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
def get_conversation_history(
    conversation_id: UUID,
    db: Session = Depends(get_session)
):
    """Lấy lịch sử tin nhắn của một cuộc hội thoại"""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    return service.get_conversation_history(conversation_id)

@router.post("/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: UUID,
    body: MessageCreateBody, 
    db: Session = Depends(get_session)
):
    """Gửi tin nhắn đến Bot và nhận phản hồi (Logic Chat cũ)"""
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    
    service = ChatService(conv_repo, msg_repo)
    
    try:
        result = await service.process_message(conversation_id, body.message)
        
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            reply=result["reply"],
            intent=result["intent"],
            slots=result["slots"],
            action=result["action"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))