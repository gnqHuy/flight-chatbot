import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.utils.validators import validate_flight_params         
from app.utils.flight_analysis import analyze_flights_for_comparison

def compare_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE SO SÁNH CHUYẾN BAY ---")

    user_prefs = state.get("user_prefs", {})
    
    is_valid, error_msgs, state_updates = validate_flight_params(user_prefs)
    
    if not is_valid:
        result = {
            "node_results": error_msgs,
            "action": None
        }
        if state_updates:
            result["user_prefs"] = state_updates
        return result

    origin = user_prefs.get("origin")
    dest = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")

    current_search_id = user_prefs.get("current_search_id")
    flights = []
    
    if current_search_id:
        cached_data = redis_service.get_flight_offers(current_search_id)
        if cached_data:
            flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    if not flights:
        inc_airlines = user_prefs.get("includedAirlines", [])
        if not isinstance(inc_airlines, list): inc_airlines = []
            
        comp_targets = user_prefs.get("comparison_target", [])
        if not isinstance(comp_targets, list): comp_targets = []
        
        api_airlines = list(set(inc_airlines + comp_targets))
        valid_api_airlines = [a.upper() for a in api_airlines if isinstance(a, str) and len(a) == 2]

        flights = flight_service.search_flights(
            origin=origin,
            destination=dest,
            departureDate=departureDate,
            returnDate=user_prefs.get("returnDate"),
            adults=user_prefs.get("adults", 1),
            includedAirlines=valid_api_airlines if valid_api_airlines else None,
            excludedAirlines=user_prefs.get("excludedAirlines"),
            nonStop=user_prefs.get("nonStop"),
            travelClass=user_prefs.get("travelClass"),
            maxPrice=user_prefs.get("maxPrice"),
            start_hour=user_prefs.get("start_hour"),
            end_hour=user_prefs.get("end_hour")
        )
        if flights:
            current_search_id = redis_service.save_flight_offers(flights)
            
    if not flights:
        not_found_msg = f"[FLIGHTS_NOT_FOUND]: origin={origin}, destination={dest}, date={departureDate}."
        return {"node_results": [not_found_msg]}

    analysis_report = analyze_flights_for_comparison(flights)
    
    return {
        "node_results": [analysis_report],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": current_search_id}
        },
        "user_prefs": {"current_search_id": current_search_id} 
    }