import json
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import MAX_FLIGHTS_RETURNED, ContextTag
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.validators import validate_flight_params
from app.utils.helpers import consume_task

def search_flights_node(state: ChatState) -> dict:
    print("--- VÀO TRẠM TÌM KIẾM CHUYẾN BAY (API SEARCH) ---")
    
    user_prefs = state.get("user_prefs", {})
    current_tasks = state.get("tasks", [])
    remaining_tasks = consume_task(current_tasks, ["search_flight"])
    
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {"node_results": error_msgs, "action": None, "tasks": remaining_tasks}
        if state_updates:
            result["user_prefs"] = state_updates
        return result

    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    final_airlines = get_final_airlines(user_prefs)
    
    if not final_airlines:
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Khách hàng đã loại trừ tất cả các hãng hỗ trợ. Vui lòng đổi lọc hãng bay."],
            "action": None, 
            "tasks": remaining_tasks
        }

    try:
        flights = flight_service.search_flights(
            origin=origin,
            destination=destination,
            departureDate=departureDate,
            returnDate=user_prefs.get("returnDate"),
            adults=user_prefs.get("adults", 1),
            children=user_prefs.get("children", 0),
            infants=user_prefs.get("infants", 0),
            includedAirlines=final_airlines,
            nonStop=user_prefs.get("nonStop"),
            travelClass=user_prefs.get("travelClass"),
            maxPrice=user_prefs.get("maxPrice"),
            start_hour=user_prefs.get("start_hour"),
            end_hour=user_prefs.get("end_hour"),
            max_offers=MAX_FLIGHTS_RETURNED
        )

        if not flights:
            not_found_msg = f"{ContextTag.SYS_NOT_FOUND}: Không có chuyến bay từ {origin} đi {destination} vào {departureDate} khớp với yêu cầu."
            return {
                "node_results": [not_found_msg], 
                "action": None, 
                "tasks": remaining_tasks,
                "current_search_id": "NOT_FOUND"
            }
        
        search_id = redis_service.save_flight_offers(flights)
        
        found_msg = f"{ContextTag.FLIGHT_FOUND}: Đã tìm thấy thành công các chuyến bay từ {origin} đi {destination} vào ngày {departureDate}."
        
        return {
            "node_results": [found_msg],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": search_id}
            },
            "user_prefs": state_updates if state_updates else {},
            "current_search_id": search_id,
            "chat_history": {"search_ids": [search_id]},
            "tasks": remaining_tasks
        }

    except Exception as e:
        print(f"ERROR - API Search: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống Amadeus gặp sự cố hoặc hết thời gian phản hồi."], 
            "error_msg": str(e),
            "tasks": remaining_tasks
        }