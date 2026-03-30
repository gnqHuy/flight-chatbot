import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.validators import validate_flight_params

def search_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM CHUYẾN BAY ---")
    print("\n👉 [GỠ LỖI - SỞ THÍCH KHÁCH HÀNG]: ", state.get("user_prefs", {}))
    print("\n🔹🔹🔹 ------------------------------------")

    user_prefs = state.get("user_prefs", {})
    
    # Xóa task search_flight an toàn
    current_tasks = state.get("tasks", [])
    remaining_tasks = []
    
    for t in current_tasks:
        task_name = t.intent.value if hasattr(t.intent, 'value') else str(t.intent)
        task_name_lower = task_name.lower()
        if "search_flight" not in task_name_lower:
            remaining_tasks.append(t)
            
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {"node_results": error_msgs, "action": None, "tasks": remaining_tasks}
        if state_updates:
            result["user_prefs"] = state_updates
        return result

    current_search_id = state.get("current_search_id")
    
    if current_search_id and current_search_id != "CLEAR":
        cached_data = redis_service.get_flight_offers(current_search_id)
        
        if cached_data:
            print(f"👉 [ĐIỀU HƯỚNG]: Khách cung cấp thêm thông tin. Vé cũ ({current_search_id}) CÒN HẠN trên Redis, KHÔNG gọi lại API.")
            return {
                "node_results": ["[THÔNG TIN CHUYẾN BAY] Hệ thống đang hiển thị lại danh sách chuyến bay từ bộ nhớ đệm dựa trên yêu cầu thao tác của khách hàng."],
                "action": {
                    "type": "flight_list",
                    "payload": {"search_id": current_search_id}
                },
                "user_prefs": state_updates if state_updates else {}, 
                "tasks": remaining_tasks
            }
        else:
            print(f"👉 [ĐIỀU HƯỚNG]: Vé cũ ({current_search_id}) ĐÃ HẾT HẠN. Bắt buộc phải gọi API Amadeus để tìm lại vé mới.")
            current_search_id = None 

    print("👉 [ĐIỀU HƯỚNG]: Phát hiện hành trình mới hoặc vé đã hết hạn. Đang tính toán hãng bay và gọi API Amadeus...")
    
    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    final_airlines = get_final_airlines(user_prefs)
    
    if not final_airlines:
        return {
            "node_results": ["[KHÔNG TÌM THẤY] Khách hàng đã loại trừ tất cả các hãng hàng không mà hệ thống đang hỗ trợ. Vui lòng yêu cầu khách thay đổi bộ lọc hãng bay."],
            "action": None, 
            "tasks": remaining_tasks
        }

    num_airlines = len(final_airlines)
    if num_airlines == 1:
        max_results = 25
    elif num_airlines == 2:
        max_results = 50
    else:
        max_results = 100

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
            max_offers=max_results
        )

        print(f"👉 [GỠ LỖI - API]: Hệ thống Amadeus trả về {len(flights) if flights else 0} chuyến bay.")
        
        if not flights:
            not_found_msg = f"[KHÔNG TÌM THẤY] Không tìm thấy chuyến bay nào từ {origin} đi {destination} vào ngày {departureDate}. Hãy gợi ý khách hàng đổi ngày bay hoặc điểm đến."
            return {"node_results": [not_found_msg], "action": None, "tasks": remaining_tasks}
        
        search_id = redis_service.save_flight_offers(flights)
        
        found_msg = f"[THÔNG TIN CHUYẾN BAY] Đã tìm thấy thành công các chuyến bay từ {origin} đi {destination} vào ngày {departureDate}."
        
        return {
            "node_results": [found_msg],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": search_id}
            },
            "user_prefs": state_updates,
            "current_search_id": search_id,
            "chat_history": {"search_ids": [search_id]},
            "tasks": remaining_tasks
        }

    except Exception as e:
        print(f"👉 ❌ [LỖI]: Lỗi trong quá trình gọi API tìm vé: {e}")
        return {
            "node_results": ["[LỖI] Hệ thống đặt vé (Amadeus API) đang gặp sự cố kết nối hoặc hết thời gian phản hồi. Xin vui lòng xin lỗi khách hàng và thử lại sau."], 
            "error_msg": str(e),
            "tasks": remaining_tasks
        }