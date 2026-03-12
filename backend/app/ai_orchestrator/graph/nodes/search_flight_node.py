from app.ai_orchestrator.graph.state import ChatState
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.validators import validate_flight_params

def search_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE TÌM KIẾM CHUYẾN BAY ---")
    print("[DEBUG - STATE]: \n", state)
    print("\n🔹🔹🔹 ------------------------------------")

    user_prefs = state.get("user_prefs", {})

    print("👉 [DEBUG - PREFS]: ", user_prefs)

    tasks = state.get("tasks", [])
    remaining_tasks = tasks[1:] if tasks else []
    
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {"node_results": error_msgs, "action": None, "tasks": remaining_tasks}
        if state_updates:
            user_prefs.update(state_updates)
            result["user_prefs"] = user_prefs
        return result

    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    
    try:
        flights = flight_service.search_flights(
            origin=origin,
            destination=destination,
            departureDate=departureDate,
            returnDate=user_prefs.get("returnDate"),
            adults=user_prefs.get("adults", 1),
            includedAirlines=user_prefs.get("includedAirlines"),
            excludedAirlines=user_prefs.get("excludedAirlines"),
            nonStop=user_prefs.get("nonStop"),
            travelClass=user_prefs.get("travelClass"),
            maxPrice=user_prefs.get("maxPrice"),
            start_hour=user_prefs.get("start_hour"),
            end_hour=user_prefs.get("end_hour")
        )

        print(f"👉 [DEBUG - API]: API search_flights trả về {len(flights)} kết quả.")
        
        if not flights:
            not_found_msg = f"[FLIGHTS_NOT_FOUND]: origin={origin}, destination={destination}, date={departureDate}."
            return {"node_results": [not_found_msg], "action": None, "tasks": remaining_tasks}
        
        search_id = redis_service.save_flight_offers(flights)
        found_msg = f"FLIGHTS_FOUND: {len(flights)} flights. FROM: {origin}. TO: {destination}. DATE: {departureDate}."
        user_prefs["current_search_id"] = search_id
        
        return {
            "node_results": [found_msg],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": search_id}
            },
            "user_prefs": user_prefs,
            "chat_history": {"search_ids": [search_id]},
            "tasks": remaining_tasks
        }

    except Exception as e:
        print(f"Lỗi tìm vé: {e}")
        return {
            "node_results": ["[FLIGHTS_FOUND_ERROR]: API search failed."], 
            "error_msg": str(e),
            "tasks": remaining_tasks
        }