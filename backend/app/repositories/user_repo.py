from sqlmodel import Session, select
from app.database.models.user import User
from uuid import UUID

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, email: str, password_hash: str) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash
        )
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.exec(stmt).first()
