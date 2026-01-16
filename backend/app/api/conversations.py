from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID
from app.database.database import get_session
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.conversation import ConversationRead

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.post("/", response_model=ConversationRead)
def create_conversation(
    user_id: UUID | None = None,
    session: Session = Depends(get_session)
):
    repo = ConversationRepository(session)
    return repo.create(user_id=user_id)
