from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.database.database import get_session
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserRead)
def create_user(
    payload: UserCreate,
    session: Session = Depends(get_session)
):
    repo = UserRepository(session)

    if repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email already exists")

    return repo.create(
        name=payload.name,
        email=payload.email,
        password_hash=payload.password
    )
