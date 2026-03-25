from sqlmodel import Session, select
from typing import List, Optional
from app.database.models.airline import Airline

class AirlineRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, airline: Airline) -> Airline:
        self.session.add(airline)
        self.session.commit()
        self.session.refresh(airline)
        return airline

    def get_by_id(self, airline_id: int) -> Optional[Airline]:
        return self.session.get(Airline, airline_id)

    def get_by_code(self, code: str) -> Optional[Airline]:
        statement = select(Airline).where(Airline.code == code)
        return self.session.exec(statement).first()

    def get_all(self) -> List[Airline]:
        statement = select(Airline)
        return list(self.session.exec(statement).all())