import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.analysis_handlers import (
    handle_general_analysis,
    handle_airline_comparison,
    handle_specific_flight_comparison
)

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE PHÂN TÍCH CHUYẾN BAY ---")
    print("\n👉 [DEBUG - PREFS]: ", state.get("user_prefs", {}))
    print("\n🔹🔹🔹 ------------------------------------")
    
    user_prefs = state.get("user_prefs", {})
    tasks = state.get("tasks", [])
    remaining_tasks = tasks[1:] if tasks else []
    
    analysis_targets = user_prefs.get("analysis_targets", []) 
    sort_preference = user_prefs.get("sort_preference", "price") 
    saved_flights = state.get("saved_flights", [])
    current_search_id = state.get("current_search_id")
    
    history_dict = state.get("chat_history", {})
    recent_ids = history_dict.get("search_ids", [])[-3:]

    grouped_data = {}
    if current_search_id:
        cached_data = redis_service.get_flight_offers(current_search_id)
        if cached_data:
            grouped_data = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    targets_clean = [str(t).upper().replace(" ", "") for t in analysis_targets if t]
    report = ""
    
    if not targets_clean:
        print("👉 [ROUTE]: Phân tích tổng thể.")
        report = handle_general_analysis(grouped_data, sort_preference)
    elif any(len(t) == 2 for t in targets_clean):
        print(f"👉 [ROUTE]: So sánh Hãng bay: {targets_clean}")
        report = handle_airline_comparison(grouped_data, targets_clean, sort_preference)
    else:
        print(f"👉 [ROUTE]: So sánh Chuyến bay: {targets_clean}")
        report = handle_specific_flight_comparison(current_search_id, saved_flights, recent_ids, targets_clean)

    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "user_prefs": {"analysis_targets": ["CLEAR"]}
    }