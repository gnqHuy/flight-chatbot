from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import Annotated

from app.database.database import get_session
from app.services.auth_service import AuthService
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserCreate, UserRead, Token
from app.api.deps import get_current_user
from app.database.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_auth_service(session: Session = Depends(get_session)) -> AuthService:
    return AuthService(UserRepository(session))

@router.post("/register", response_model=UserRead)
def register(
    user_in: UserCreate,
    service: AuthService = Depends(get_auth_service)
):
    return service.register(user_in)

@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthService = Depends(get_auth_service)
):
    return service.authenticate(email=form_data.username, password=form_data.password)

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: User = Depends(get_current_user)):
    """API test để xem token có hoạt động không"""
    return current_user