import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.helpers import consume_task

def filter_sort_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE LỌC & SẮP XẾP DANH SÁCH ---")
    
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "filter_sort_flights")
    
    sort_pref = user_prefs.get("sort_preference", "price_asc")
    sort_val = sort_pref.value if hasattr(sort_pref, 'value') else str(sort_pref)
    
    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": ["Không tìm thấy danh sách chuyến bay hiện tại. Vui lòng yêu cầu tìm kiếm hành trình mới."],
            "action": None,
            "tasks": remaining_tasks
        }

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return {
            "node_results": ["Phiên tìm kiếm đã hết hạn, vui lòng yêu cầu tìm lại chuyến bay."],
            "action": {"type": "session_expired"},
            "tasks": remaining_tasks
        }
        
    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    final_airlines = get_final_airlines(user_prefs)
    filtered_flights = []
    
    if isinstance(all_flights, list):
        for f in all_flights:
            flight_airlines = f.get("airlines", [])
            
            if not flight_airlines:
                fn = str(f.get("flightNumber", "")).upper()
                if fn: flight_airlines = [fn[:2]]
                
            if any(a in final_airlines for a in flight_airlines):
                filtered_flights.append(f)

    if not filtered_flights:
        return {
            "node_results": ["Không có chuyến bay nào khớp với bộ lọc của bạn trên danh sách này."],
            "action": {"type": "flight_list", "payload": {"search_id": current_search_id}},
            "tasks": remaining_tasks
        }

    try:
        if sort_val == "price_desc":
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
        else: 
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)))
    except Exception as e:
        print(f"❌ Lỗi sắp xếp: {e}")

    new_search_id = redis_service.save_flight_offers(filtered_flights)
    
    node_msg = f"Đã áp dụng bộ lọc và sắp xếp. Dữ liệu trên màn hình đã được cập nhật."

    return {
        "node_results": [node_msg],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": new_search_id}
        },
        "current_search_id": new_search_id,
        "tasks": remaining_tasks
    }