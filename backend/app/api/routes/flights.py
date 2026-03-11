import json
from fastapi import APIRouter, HTTPException
from app.services.redis_service import redis_service
from app.ai_orchestrator.graph.flight_graph import flight_graph 

router = APIRouter(prefix="/flights", tags=["Flights"])

@router.get("/cache/{search_id}")
async def get_cached_flights(search_id: str):
    flights = redis_service.get_flight_offers(search_id)
    if not flights:
        raise HTTPException(status_code=410, detail="Phiên tìm vé đã hết hạn")
    return {"flights": json.loads(flights) if isinstance(flights, str) else flights}

@router.post("/save") 
async def save_flight_to_cart(thread_id: str, search_id: str, flight_number: str):
    cached_data = redis_service.get_flight_offers(search_id)

    flights = json.loads(cached_data) if isinstance(cached_data, str) else (cached_data or [])

    selected_flight = next((f for f in flights if f.get("flightNumber") == flight_number), None)
    
    if selected_flight:
        config = {"configurable": {"thread_id": thread_id}}
        
        flight_graph.update_state(config, {"saved_flights": [selected_flight]})
        
        return {"msg": f"Đã lưu chuyến {flight_number} vào giỏ hàng."}
    
    raise HTTPException(status_code=400, detail="Không tìm thấy chuyến bay hoặc phiên tìm kiếm đã hết hạn.")