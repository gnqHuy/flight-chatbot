from sqlmodel import SQLModel
from uuid import UUID
from datetime import datetime

class UserCreate(SQLModel):
    name: str
    email: str
    password: str

class UserRead(SQLModel):
    id: UUID
    name: str
    email: str
    created_at: datetime
