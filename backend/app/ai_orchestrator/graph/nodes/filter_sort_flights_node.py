import json
from datetime import datetime
import uuid
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.helpers import consume_task
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent 
from app.core.constants import ContextTag

def filter_sort_flights_node(state: ChatState) -> dict:
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])    
    
    sort_pref = user_prefs.get("sort_preference")
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
            "node_results": [f"{ContextTag.SYS_ERROR}: Phiên tìm kiếm đã hết hạn hoặc không tìm thấy dữ liệu. Hệ thống sẽ tự động tìm lại."],
            "current_search_id": "CLEAR", 
            "tasks": consume_task(
                tasks, 
                ["filter_sort_flights"], 
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=None)
            )
        }
        
    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    max_price = user_prefs.get("maxPrice")
    start_hour = user_prefs.get("start_hour")
    end_hour = user_prefs.get("end_hour")
    is_non_stop = user_prefs.get("nonStop")

    filtered_flights = []
    
    for f in all_flights:
        is_match = True
        
        if is_match and max_price not in [None, 0, "CLEAR"]:
            try:
                if float(f.get('price', 0)) > float(max_price):
                    is_match = False
            except ValueError:
                pass

        if is_match and is_non_stop is True:
            segments = f.get("segments", [])
            if len(segments) > 1 or f.get("isNonStop") is False:
                is_match = False

        if is_match and (start_hour not in [None, "CLEAR"] or end_hour not in [None, "CLEAR"]):
            dep_time_str = f.get('departureTime', '') 
            if 'T' in dep_time_str:
                try:
                    hour = int(dep_time_str.split('T')[1].split(':')[0])
                    if start_hour not in [None, "CLEAR"] and hour < int(start_hour):
                        is_match = False
                    if end_hour not in [None, "CLEAR"] and hour > int(end_hour):
                        is_match = False
                except Exception:
                    pass

        if is_match:
            filtered_flights.append(f)

    if not filtered_flights:
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Không có chuyến bay nào thỏa mãn bộ lọc hiện tại (giờ, mức giá). Khách có thể nới lỏng hoặc hủy bộ lọc để xem lại danh sách cũ."],
            "action": None, 
            "tasks": consume_task(tasks, ["filter_sort_flights"])
        }

    try:
        if sort_val == "price_desc":
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
        elif sort_val == "departure_time":
            filtered_flights.sort(key=lambda x: str(x.get('departureTime', '9999-12-31T23:59:59')))
        elif sort_val == "arrival_time":
            filtered_flights.sort(key=lambda x: str(x.get('arrivalTime', '9999-12-31T23:59:59')))
        else:
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)))
    except Exception as e:
        print(f"ERROR - Sort: {e}")
    
    filtered_id = redis_service.save_flight_offers(filtered_flights, parent_id=current_search_id)
    
    node_msg = f"{ContextTag.FILTER_APPLIED}: Hệ thống đã áp dụng bộ lọc và sắp xếp thành công ({len(filtered_flights)} vé)."

    return {
        "node_results": [node_msg],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": filtered_id}
        },
        "tasks": consume_task(tasks, ["filter_sort_flights"])
    }