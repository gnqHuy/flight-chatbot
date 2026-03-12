import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.validators import validate_flight_params         
from app.utils.flight_analysis import analyze_flights_for_comparison, analyze_specific_flights

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE PHÂN TÍCH CHUYẾN BAY ---")

    tasks = state.get("tasks", [])
    remaining_tasks = tasks[1:] if tasks else []

    user_prefs = state.get("user_prefs", {})
    
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {"node_results": error_msgs, "action": None, "tasks": remaining_tasks}
        if state_updates:
            result["user_prefs"] = state_updates
        return result

    target_flights = user_prefs.get("target_flights", []) 
    sort_preference = user_prefs.get("sort_preference", "price") 
    saved_flights = state.get("saved_flights", [])
    
    current_search_id = user_prefs.get("current_search_id")
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})

    result_dict = {"tasks": remaining_tasks}

    if target_flights:
        found_flights = []
        missing_targets = set([str(t).upper().replace(" ", "") for t in target_flights])

        def _extract_targets_from(flight_list):
            for f in flight_list:
                fn = str(f.get("flightNumber", "")).upper().replace(" ", "")
                if fn in missing_targets:
                    found_flights.append(f)
                    missing_targets.remove(fn)
                    if not missing_targets: break 

        if current_search_id and missing_targets:
            cached_data = redis_service.get_flight_offers(current_search_id)
            if cached_data:
                flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
                _extract_targets_from(flights)

        if missing_targets and saved_flights:
            _extract_targets_from(saved_flights)

        if missing_targets:
            recent_ids = history_dict.get("search_ids", [])[-3:] 
            for sid in reversed(recent_ids):
                if not missing_targets: break
                if sid == current_search_id: continue
                
                cached_data = redis_service.get_flight_offers(sid)
                if cached_data:
                    flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
                    _extract_targets_from(flights)

        analysis_report = analyze_specific_flights(found_flights, target_flights)
        result_dict["node_results"] = [analysis_report]
        
        user_prefs["target_flights"] = [] 
        result_dict["user_prefs"] = user_prefs

    else:
        flights_pool = []
        
        if current_search_id:
            cached_data = redis_service.get_flight_offers(current_search_id)
            if cached_data:
                flights_pool = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
            else:
                user_prefs["current_search_id"] = None
                current_search_id = None

        if not flights_pool:
            not_found_msg = "[ANALYZE_ERROR]: Không có dữ liệu chuyến bay trong bộ nhớ tạm để phân tích."
            result_dict["node_results"] = [not_found_msg]
            return result_dict

        unique_pool = {str(f.get("flightNumber")): f for f in flights_pool}
        final_pool = list(unique_pool.values())

        analysis_report = analyze_flights_for_comparison(final_pool, sort_pref=sort_preference)
        result_dict["node_results"] = [analysis_report]
        
        if current_search_id:
            result_dict["action"] = {
                "type": "flight_list",
                "payload": {"search_id": current_search_id}
            }
            result_dict["user_prefs"] = user_prefs

    return result_dict