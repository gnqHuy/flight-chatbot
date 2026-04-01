import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.helpers import consume_task

def filter_sort_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM LỌC & SẮP XẾP CHUYẾN BAY ---")
    
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])    
    remaining_tasks = consume_task(tasks, ["filter_sort_flights"])
    
    sort_pref = user_prefs.get("sort_preference", "price_asc")
    sort_val = sort_pref.value if hasattr(sort_pref, 'value') else str(sort_pref)
    
    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": ["[KHÔNG TÌM THẤY] Không tìm thấy danh sách chuyến bay hiện tại để lọc. Xin vui lòng yêu cầu khách hàng cung cấp điểm đi và điểm đến để tìm kiếm chuyến bay mới."],
            "action": None,
            "tasks": remaining_tasks
        }

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return {
            "node_results": ["[KHÔNG TÌM THẤY] Dữ liệu chuyến bay đã hết hạn do phiên làm việc quá lâu. Xin vui lòng yêu cầu khách hàng tìm kiếm lại chuyến bay."],
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
            "node_results": ["[KHÔNG TÌM THẤY] Không có chuyến bay nào khớp với bộ lọc của khách hàng (ví dụ: bị loại trừ hết hãng bay). Hãy thông báo để khách hàng nới lỏng hoặc thay đổi bộ lọc."],
            "action": {"type": "flight_list", "payload": {"search_id": current_search_id}},
            "tasks": remaining_tasks
        }

    try:
        if sort_val == "price_desc":
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)), reverse=True)
        else: 
            filtered_flights.sort(key=lambda x: float(x.get('price', 0)))
    except Exception as e:
        print(f"❌ [LỖI]: Lỗi trong quá trình sắp xếp chuyến bay: {e}")

    new_search_id = redis_service.save_flight_offers(filtered_flights)
    
    node_msg = "[THÔNG TIN CHUYẾN BAY] Hệ thống đã áp dụng bộ lọc và sắp xếp thành công. Dữ liệu trên màn hình giao diện đã được cập nhật. Hãy thông báo cho khách hàng biết."
    
    print(f"👉 [GỠ LỖI]: Đã lọc xong, còn lại {len(filtered_flights)} chuyến bay. Đã cập nhật giao diện.")

    return {
        "node_results": [node_msg],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": new_search_id}
        },
        "current_search_id": new_search_id,
        "tasks": remaining_tasks
    }