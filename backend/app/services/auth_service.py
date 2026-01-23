from fastapi import HTTPException, status
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserCreate, Token
from app.database.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register(self, user_in: UserCreate) -> User:
        if self.user_repo.get_by_email(user_in.email):
            raise HTTPException(
                status_code=400, 
                detail="Email này đã được đăng ký."
            )
        
        hashed_pw = get_password_hash(user_in.password)
        
        new_user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hashed_pw
        )
        
        return self.user_repo.create(new_user)

    def authenticate(self, email: str, password: str) -> Token:
        user = self.user_repo.get_by_email(email)
        if not user:
            raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không đúng")
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Email hoặc mật khẩu không đúng")

        access_token = create_access_token(subject=user.id)
        return Token(access_token=access_token)