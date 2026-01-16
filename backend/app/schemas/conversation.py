from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class ConversationRead(SQLModel):
    id: UUID
    user_id: Optional[UUID]
    state_json: Dict[str, Any]
    status: str
    created_at: datetime
