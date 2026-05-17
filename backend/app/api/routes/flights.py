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
        
    selected = next((f for f in flights if f.get("flightNumber") == flight_number), None)

    if not selected:
        raise HTTPException(status_code=400, detail="Không tìm thấy chuyến bay.")

    if _fg.flight_graph is None:
        raise HTTPException(status_code=503, detail="Graph chưa sẵn sàng.")

    config = {"configurable": {"thread_id": thread_id}}
    await _fg.flight_graph.aupdate_state(config, {"saved_flights": [selected]})

    return {"msg": f"Đã lưu chuyến {flight_number} vào giỏ hàng."}