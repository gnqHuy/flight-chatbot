from app.ai_orchestrator.graph.state import ChatState
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.flight_parser import get_final_airlines
from app.utils.helpers import consume_task
from app.utils.validators import validate_flight_params

def search_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE TÌM KIẾM CHUYẾN BAY ---")
    print("\n👉 [DEBUG - PREFS]: ", state.get("user_prefs", {}))
    print("\n🔹🔹🔹 ------------------------------------")

    user_prefs = state.get("user_prefs", {})
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "search_flight")

    if tasks:
        current_task = tasks[0]
        intent_val = current_task.intent.value if hasattr(current_task.intent, 'value') else str(current_task.intent)
        if intent_val == "filter_sort_flights":
            remaining_tasks = tasks[1:]
    
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {"node_results": error_msgs, "action": None, "tasks": remaining_tasks}
        if state_updates:
            result["user_prefs"] = state_updates
        return result

    current_search_id = state.get("current_search_id")
    if current_search_id and current_search_id != "CLEAR":
        print(f"👉 [ROUTE]: Khách chỉ lọc/sắp xếp. Dùng lại search_id [{current_search_id}], KHÔNG gọi Amadeus.")
        return {
            "node_results": ["FILTER_SORT: Khách thao tác trên danh sách cũ, hệ thống hiển thị lại dữ liệu từ bộ nhớ đệm."],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": current_search_id}
            },
            "user_prefs": state_updates if state_updates else {}, 
            "tasks": remaining_tasks
        }

    print("👉 [ROUTE]: Hành trình mới. Tính toán hãng bay và gọi API Amadeus...")
    
    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    final_airlines = get_final_airlines(user_prefs)
    
    if not final_airlines:
        return {
            "node_results": ["[FLIGHTS_NOT_FOUND]: Khách đã loại trừ tất cả các hãng bay hỗ trợ."],
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

        print(f"👉 [DEBUG - API]: API trả về {len(flights) if flights else 0} kết quả.")
        
        if not flights:
            not_found_msg = f"[FLIGHTS_NOT_FOUND]: origin={origin}, destination={destination}, date={departureDate}."
            return {"node_results": [not_found_msg], "action": None, "tasks": remaining_tasks}
        
        search_id = redis_service.save_flight_offers(flights)
        
        found_msg = f"FLIGHTS_FOUND: Đã tìm thấy các chuyến bay từ {origin} đi {destination} ngày {departureDate}."
        
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
        print(f"👉 Lỗi tìm vé: {e}")
        return {
            "node_results": ["[FLIGHTS_FOUND_ERROR]: API search failed."], 
            "error_msg": str(e),
            "tasks": remaining_tasks
        }