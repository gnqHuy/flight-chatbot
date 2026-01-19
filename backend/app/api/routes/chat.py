from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database.database import get_session
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.chat_request import ChatRequest
from app.schemas.chat_response import ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/send_message", response_model=ChatResponse)
async def chat(
    req: ChatRequest, 
    db: Session = Depends(get_session)
):
    conv_repo = ConversationRepository(db)
    msg_repo = MessageRepository(db)
    
    service = ChatService(conv_repo, msg_repo)
    
    try:
        result = await service.process_message(req.conversation_id, req.message)
        
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