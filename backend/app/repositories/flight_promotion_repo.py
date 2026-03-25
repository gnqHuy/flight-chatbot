from sqlmodel import Session, select
from typing import List, Optional
from datetime import date
from app.database.models.flight_promotion import FlightPromotion

class FlightPromotionRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, promotion: FlightPromotion) -> FlightPromotion:
        self.session.add(promotion)
        self.session.commit()
        self.session.refresh(promotion)
        return promotion

    def create_batch(self, promotions: List[FlightPromotion]):
        self.session.add_all(promotions)
        self.session.commit()

    def get_active_promotions(self) -> List[FlightPromotion]:
        today = date.today()
        statement = select(FlightPromotion).where(
            (FlightPromotion.booking_end_date == None) | 
            (FlightPromotion.booking_end_date >= today)
        )
        return list(self.session.exec(statement).all())