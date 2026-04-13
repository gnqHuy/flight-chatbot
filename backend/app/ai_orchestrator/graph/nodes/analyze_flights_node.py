from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.flight_tools import fetch_airline_info, fetch_flight_details
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH (PURE PYTHON ROUTER) ---")
    
    action_targets = state.get("action_targets", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "analyze_flights")
    
    comp_airlines = action_targets.get("compare_airlines", [])
    comp_flights = action_targets.get("compare_flights", [])
    
    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Vui lòng tìm kiếm chuyến bay trước khi phân tích."],
            "tasks": remaining_tasks,
            "action_targets": {}
        }

    gathered_data = []
    
    if not comp_airlines and not comp_flights:
        print("🛑 [HITL TRIGGERED]: Yêu cầu khách chọn chuyến bay trên UI.")
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Dạ, để so sánh chi tiết, bạn vui lòng tick chọn các chuyến bay hoặc hãng bay cụ thể trên màn hình giúp mình nhé!"],
            "action": {"type": "require_flight_selection", "payload": {"search_id": current_search_id}},
            "tasks": [], 
            "action_targets": {}
        }

    elif comp_airlines and not comp_flights:
        print(f"⚙️ [ROUTER]: Luồng Hãng Bay (Airlines: {comp_airlines})")
        res = fetch_airline_info.invoke({"airline_codes": comp_airlines, "search_id": current_search_id, "skip_example": False})
        gathered_data.append(res)

    elif comp_flights and not comp_airlines:
        print(f"⚙️ [ROUTER]: Luồng Chuyến Bay (Flights: {comp_flights})")
        res = fetch_flight_details.invoke({"flight_numbers": comp_flights, "search_id": current_search_id})
        gathered_data.append(res)

    else:
        print(f"⚙️ [ROUTER]: Luồng Kết Hợp (Airlines: {comp_airlines}, Flights: {comp_flights})")
        res_airline = fetch_airline_info.invoke({"airline_codes": comp_airlines, "search_id": current_search_id, "skip_example": True})
        gathered_data.append(res_airline)
        
        res_flight = fetch_flight_details.invoke({"flight_numbers": comp_flights, "search_id": current_search_id})
        gathered_data.append(res_flight)

    final_context = "\n\n".join(gathered_data) if gathered_data else "Không lấy được dữ liệu."
    
    report = (
        f"{ContextTag.FLIGHT_ANALYSIS}:\n"
        f"{final_context}\n\n"
    )

    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "action_targets": {}
    }