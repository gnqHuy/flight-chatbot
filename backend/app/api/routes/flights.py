import os
import httpx
from fastapi import APIRouter, HTTPException
import app.ai_orchestrator.graph.flight_graph as _fg

router = APIRouter(prefix="/flights", tags=["Flights"])

FLIGHT_SERVER_URL = os.getenv("FLIGHT_MCP_URL").replace("/sse", "")

@router.get("/cache/{search_id}")
async def get_cached_flights(search_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FLIGHT_SERVER_URL}/api/flights/cache/{search_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail="Phiên tìm vé đã hết hạn")
        
        return resp.json()

@router.post("/save")
async def save_flight_to_cart(thread_id: str, search_id: str, flight_number: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{FLIGHT_SERVER_URL}/api/flights/cache/{search_id}")
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Không tìm thấy chuyến bay hoặc phiên tìm kiếm đã hết hạn.")
        
        data = resp.json()
        flights = data.get("flights", [])
        
    selected = None
    for f in flights:
        itineraries = f.get("itineraries", [])
        if itineraries and len(itineraries) > 0:
            if itineraries[0].get("flightNumber") == flight_number:
                selected = f
                break

    if not selected:
        raise HTTPException(status_code=400, detail=f"Không tìm thấy chuyến bay mã {flight_number} trong danh sách.")

    if _fg.flight_graph is None:
        raise HTTPException(status_code=503, detail="Graph chưa sẵn sàng.")

    config = {"configurable": {"thread_id": thread_id}}
    
    current_state = await _fg.flight_graph.aget_state(config)
    existing_flights = current_state.values.get("saved_flights") or []
    
    flight_id = selected.get("id")
    is_already_saved = any(f.get("id") == flight_id for f in existing_flights)
    
    if not is_already_saved:
        existing_flights.append(selected)
        await _fg.flight_graph.aupdate_state(config, {"saved_flights": existing_flights})

    return {"msg": f"Đã lưu chuyến {flight_number} vào giỏ hàng."}


@router.get("/saved/{thread_id}")
async def get_saved_flights(thread_id: str):
    if _fg.flight_graph is None:
        raise HTTPException(status_code=503, detail="Graph chưa sẵn sàng.")
        
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        current_state = await _fg.flight_graph.aget_state(config)
        saved_flights = current_state.values.get("saved_flights") or []
        return {"flights": saved_flights}
    except Exception as e:
        return {"flights": []}