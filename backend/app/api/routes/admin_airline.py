from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database.database import get_session
from app.database.models.airline import Airline
from app.repositories.airline_repo import AirlineRepository

router = APIRouter(prefix="/api/admin/airlines", tags=["Admin Airlines"])

class AirlineCreateItem(BaseModel):
    code: str
    name: str
    website_url: str
    logo_url: Optional[str] = None
    hotline: Optional[str] = None
    description: Optional[str] = None
    pros: Optional[List[str]] = []
    cons: Optional[List[str]] = []
    baggage_basic_info: Optional[str] = None

class BulkAirlineCreateRequest(BaseModel):
    airlines: List[AirlineCreateItem]

@router.post("/bulk")
def add_airlines_bulk(request: BulkAirlineCreateRequest, session: Session = Depends(get_session)):
    repo = AirlineRepository(session)
    added_count = 0
    skipped_count = 0

    for item in request.airlines:
        existing = repo.get_by_code(item.code.upper())
        if existing:
            skipped_count += 1
            continue

        new_airline = Airline(
            code=item.code.upper(),
            name=item.name,
            website_url=item.website_url,
            logo_url=item.logo_url,
            hotline=item.hotline,
            description=item.description,
            pros=item.pros,
            cons=item.cons,
            baggage_basic_info=item.baggage_basic_info
        )
        session.add(new_airline)
        added_count += 1

    if added_count > 0:
        session.commit()

    return {
        "status": "success",
        "message": f"Đã thêm {added_count} hãng bay. Bỏ qua {skipped_count} hãng đã tồn tại.",
        "data": {
            "added": added_count,
            "skipped": skipped_count
        }
    }