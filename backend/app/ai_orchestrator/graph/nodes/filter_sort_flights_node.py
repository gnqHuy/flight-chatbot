import json
from datetime import datetime
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.helpers import consume_task
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent 
from app.core.constants import ContextTag

def filter_sort_flights_node(state: ChatState) -> dict:
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])    
    
    sort_pref = user_prefs.get("sort_preference", "price_asc")
    sort_val = sort_pref.value if hasattr(sort_pref, 'value') else str(sort_pref)

    if not current_search_id or current_search_id == "CLEAR":
        return {
            "current_search_id": "CLEAR", 
            "tasks": consume_task(
                tasks, 
                ["filter_sort_flights"], 
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=None)
            )
        }

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return {
            "current_search_id": "CLEAR", 
            "tasks": consume_task(
                tasks, 
                ["filter_sort_flights"], 
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=None)
            )
        }
        
    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    final_airlines = get_final_airlines(user_prefs)
    max_price = user_prefs.get("maxPrice")
    start_hour = user_prefs.get("start_hour")
    end_hour = user_prefs.get("end_hour")
    is_non_stop = user_prefs.get("nonStop")

    filtered_flights = []
    
    if isinstance(all_flights, list):
        for f in all_flights:
            is_match = True
            
            if final_airlines:
                flight_airlines = f.get("airlines", [])
                if not flight_airlines:
                    fn = str(f.get("flightNumber", "")).upper()
                    if fn: flight_airlines = [fn[:2]]
                
                if not any(a in final_airlines for a in flight_airlines):
                    is_match = False

            if is_match and max_price is not None:
                try:
                    if float(f.get('price', 0)) > float(max_price):
                        is_match = False
                except ValueError:
                    pass

            if is_match and is_non_stop is True:
                segments = f.get("segments", [])
                if len(segments) > 1 or f.get("isNonStop") is False:
                    is_match = False

            if is_match and (start_hour is not None or end_hour is not None):
                dep_time_str = f.get('departureTime', '') 
                if 'T' in dep_time_str:
                    try:
                        hour = int(dep_time_str.split('T')[1].split(':')[0])
                        if start_hour is not None and hour < int(start_hour):
                            is_match = False
                        if end_hour is not None and hour > int(end_hour):
                            is_match = False
                    except Exception:
                        pass

            if is_match:
                filtered_flights.append(f)

    if not filtered_flights:
        return {
            "current_search_id": "CLEAR",
            "tasks": consume_task(
                tasks, 
                ["filter_sort_flights"], 
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=None)
            )
        }

    try:
        if sort_val == "price_desc":
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
        else: 
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)))
    except Exception as e:
        print(f"ERROR - Sort: {e}")

    new_search_id = redis_service.save_flight_offers(filtered_flights)
    
    node_msg = f"{ContextTag.FILTER_APPLIED}: Hệ thống đã áp dụng bộ lọc và sắp xếp thành công."

    return {
        "node_results": [node_msg],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": new_search_id}
        },
        "current_search_id": new_search_id,
        "tasks": consume_task(tasks, ["filter_sort_flights"])
    }