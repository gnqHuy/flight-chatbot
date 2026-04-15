from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.flight_tools import fetch_airline_info, fetch_flight_details
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

async def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH ---")

    action_targets    = state.get("action_targets", {})
    current_search_id = state.get("current_search_id")
    tasks             = state.get("tasks", [])
    remaining_tasks   = consume_task(tasks, "analyze_flights")

    comp_airlines = action_targets.get("compare_airlines", [])
    comp_flights  = action_targets.get("compare_flights",  [])

    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Vui lòng tìm kiếm chuyến bay trước khi phân tích."],
            "tasks": remaining_tasks, "action_targets": {},
        }

    gathered_data = []

    if not comp_airlines and not comp_flights:
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Bạn vui lòng tick chọn chuyến bay/hãng bay trên màn hình nhé!"],
            "action": {"type": "require_flight_selection", "payload": {"search_id": current_search_id}},
            "tasks": [], "action_targets": {},
        }

    try:
        if comp_airlines and not comp_flights:
            res = await fetch_airline_info.ainvoke({"airline_codes": comp_airlines, "search_id": current_search_id, "skip_example": False})
            gathered_data.append(res)
        elif comp_flights and not comp_airlines:
            res = await fetch_flight_details.ainvoke({"flight_numbers": comp_flights, "search_id": current_search_id})
            gathered_data.append(res)
        else:
            res1 = await fetch_airline_info.ainvoke({"airline_codes": comp_airlines, "search_id": current_search_id, "skip_example": True})
            res2 = await fetch_flight_details.ainvoke({"flight_numbers": comp_flights, "search_id": current_search_id})
            gathered_data.extend([res1, res2])
    except Exception as e:
        print(f"❌ [analyze error]: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống gặp lỗi khi lấy dữ liệu phân tích."],
            "tasks": remaining_tasks, "action_targets": {},
        }

    ctx = "\n\n".join(gathered_data) if gathered_data else "Không lấy được dữ liệu."
    return {
        "node_results": [f"{ContextTag.FLIGHT_ANALYSIS}:\n{ctx}\n\n"],
        "tasks":        remaining_tasks,
        "action_targets": {},
    }