from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID
from app.database.database import get_session
from app.repositories.message_repo import MessageRepository
from app.schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/messages", tags=["Messages"])

@router.post("/", response_model=MessageRead)
def create_message(
    payload: MessageCreate,
    session: Session = Depends(get_session)
):
    repo = MessageRepository(session)
    return repo.add(
        conversation_id=payload.conversation_id,
        role=payload.role,
        content=payload.content
    )
