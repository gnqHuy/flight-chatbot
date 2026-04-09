from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import MAX_FLIGHTS_RETURNED, ContextTag, SUPPORTED_AIRLINES
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.validators import validate_flight_params
from app.utils.helpers import consume_task

def search_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM TỔNG THỂ (API SEARCH) ---")
    
    search_filters = state.get("search_filters", {})
    current_search_id = state.get("current_search_id")
    current_tasks = state.get("tasks", [])
    remaining_tasks = consume_task(current_tasks, ["search_flight"])
    
    is_valid, error_msgs, state_updates = validate_flight_params(search_filters)
    
    if not is_valid:
        return {
            "node_results": error_msgs, 
            "action": None, 
            "tasks": remaining_tasks,
            "search_filters": state_updates if state_updates else {} 
        }

    if current_search_id and current_search_id != "CLEAR":
        cached_data = redis_service.get_flight_offers(current_search_id)
        if cached_data:
            print(f"⚡ [CACHE HIT]: Dữ liệu vé vẫn còn sống. Tái sử dụng Search ID: {current_search_id}")
            return {
                "node_results": [f"{ContextTag.FLIGHT_FOUND}: Đã tải lại danh sách vé từ bộ nhớ tạm."],
                "action": {
                    "type": "flight_list",
                    "payload": {"search_id": current_search_id}
                },
                "tasks": remaining_tasks
            }
        else:
            print(f"⚠️ [CACHE MISS]: Phiên {current_search_id} đã hết hạn. Chuẩn bị kéo API mới...")

    origin = search_filters.get("origin")
    destination = search_filters.get("destination")
    departureDate = search_filters.get("departureDate")

    try:
        print(f"👉 [API CALL]: Đang kéo toàn bộ vé {origin}-{destination} ngày {departureDate}...")
        
        flights = flight_service.search_flights(
            origin=origin,
            destination=destination,
            departureDate=departureDate,
            roundTrip=search_filters.get("roundTrip", False),
            returnDate=search_filters.get("returnDate"),
            adults=search_filters.get("adults", 1),
            children=search_filters.get("children", 0),
            infants=search_filters.get("infants", 0),
            travelClass=search_filters.get("travelClass"),
            includedAirlines=SUPPORTED_AIRLINES,
            max_offers=MAX_FLIGHTS_RETURNED
        )

        if not flights:
            return {
                "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Hiện tại không tìm thấy chuyến bay nào của VN, VJ, QH cho hành trình này."], 
                "action": None, 
                "tasks": remaining_tasks,
                "current_search_id": "CLEAR"
            }
        
        search_id = redis_service.save_flight_offers(flights)

        print(f"✅ [API SUCCESS]: Đã lưu {len(flights)} chuyến bay vào Redis với Search ID: {search_id}")
        
        found_msg = f"{ContextTag.FLIGHT_FOUND}: Đã tải xong danh sách chuyến bay. Hệ thống sẵn sàng lọc theo yêu cầu của bạn."
        
        return {
            "node_results": [found_msg],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": search_id}
            },
            "current_search_id": search_id,
            "chat_history": {"search_ids": [search_id]},
            "tasks": remaining_tasks
        }

    except Exception as e:
        print(f"❌ [LỖI API]: {str(e)}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không thể kết nối với máy chủ hàng không. Vui lòng thử lại sau."], 
            "tasks": remaining_tasks
        }