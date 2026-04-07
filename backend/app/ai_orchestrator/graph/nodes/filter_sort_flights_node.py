from app.ai_orchestrator.graph.state import ChatState
from app.utils.helpers import consume_task
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent 
from app.core.constants import ContextTag

def filter_sort_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM LỌC & SẮP XẾP CHUYẾN BAY ---")
    
    search_filters = state.get("search_filters", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])    
    print(f"👉 [DEBUG] Search Filters tại trạm filter_sort_flights: {search_filters}")
    print(f"👉 [DEBUG] Current Search ID: {current_search_id}")
    if not current_search_id or current_search_id == "CLEAR":
        return {
            "current_search_id": "CLEAR", 
            "tasks": consume_task(
                tasks, 
                ["filter_sort_flights"], 
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=None)
            )
        }

    target_filter_keys = [
        "maxPrice", "start_hour", "end_hour", "nonStop", 
        "preferred_airlines", "travelClass"
    ]
    
    fe_filters = {}
    for key in target_filter_keys:
        if key in search_filters:
            fe_filters[key] = search_filters[key]

    sort_pref = search_filters.get("sort_preference")
    sort_val = sort_pref.value if hasattr(sort_pref, 'value') else str(sort_pref) if sort_pref else None

    node_msg = f"{ContextTag.FILTER_APPLIED}: Đã gửi lệnh điều chỉnh bộ lọc lên giao diện."

    return {
        "node_results": [node_msg],
        "action": {
            "type": "apply_filters",
            "payload": {
                "search_id": current_search_id,
                "filters": fe_filters,
                "sort": sort_val
            }
        },
        "tasks": consume_task(tasks, ["filter_sort_flights"])
    }