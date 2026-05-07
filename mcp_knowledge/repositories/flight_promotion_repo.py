from sqlmodel import Session, select
from typing import List, Optional
from datetime import date
from models.flight_promotion import FlightPromotion


class FlightPromotionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_active_promotions(self, target_airline_id: Optional[int] = None) -> List[FlightPromotion]:
        today = date.today()
        q = select(FlightPromotion).where(
            (FlightPromotion.booking_end_date == None) |
            (FlightPromotion.booking_end_date >= today)
        )
        if target_airline_id:
            q = q.where(FlightPromotion.airline_id == target_airline_id)
        return list(self.session.exec(q).all())