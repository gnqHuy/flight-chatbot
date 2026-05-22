import traceback
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from sqlmodel import Session
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.database.database import get_session
from app.database.models.user import User
from app.schemas.conversation import ConversationRead, ConversationTitleUpdate
from app.schemas.message import MessageCreateBody, MessageRead
from app.schemas.chat_response import ChatResponse, ResumeRequest
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

@router.get("/{conversation_id}/messages", response_model=List[MessageRead])
def get_conversation_history(
    conversation_id: UUID,
    db: Session = Depends(get_session)
):
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
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ChatService(conv_repo, msg_repo)
    
    try:
        result = await service.process_message(
            conversation_id=str(conversation_id), 
            user_message=body.message,
            ui_context=body.ui_context.model_dump() if body.ui_context else None
        )
        
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            role=result["role"],
            content=result["content"],
            slots=result["slots"],
            action=result["action"]
        )
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Lỗi hệ thống: {str(e)}"
        )

@router.post("/{conversation_id}/resume", response_model=ChatResponse)
async def resume_graph(
    conversation_id: UUID,
    body: ResumeRequest, 
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ChatService(conv_repo, msg_repo) 
    
    try:
        result = await service.resume_message(
            conversation_id=str(conversation_id),
            selected_flight_ids=body.selected_flight_ids
        )
        
        return ChatResponse(
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            role=result["role"],
            content=result["content"],
            slots=result["slots"],
            action=result["action"]
        )
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi tiếp tục luồng AI: {str(e)}"
        )
    
@router.patch("/{conversation_id}/title", response_model=ConversationRead)
def update_conversation_title(
    conversation_id: UUID,
    body: ConversationTitleUpdate, 
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    service = ConversationService(conv_repo, msg_repo)
    
    return service.update_conversation_title(conversation_id, body.title)