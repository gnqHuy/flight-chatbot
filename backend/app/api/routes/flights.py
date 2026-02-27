from fastapi import APIRouter, HTTPException
from app.services.redis_service import redis_service

router = APIRouter(prefix="/flights", tags=["Flights"])

@router.get("/cache/{search_id}")
async def get_cached_flights(search_id: str):
    flights = redis_service.get_flight_offers(search_id)
    if not flights:
        raise HTTPException(status_code=410, detail="Phiên tìm vé đã hết hạn")
    return {"flights": flights}