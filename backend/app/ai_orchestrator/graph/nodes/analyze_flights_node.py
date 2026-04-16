"""
app/ai_orchestrator/graph/nodes/analyze_flights_node.py
Thin async wrapper — build analysis context từ mcp-flight server.
Không còn dùng LangChain tool wrapper hay raw data dump.
"""
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp
from app.utils.helpers import consume_task
from app.core.constants import ContextTag


async def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH (MCP FLIGHT) ---")

    action_targets    = state.get("action_targets", {})
    current_search_id = state.get("current_search_id")
    tasks             = state.get("tasks", [])
    remaining         = consume_task(tasks, "analyze_flights")

    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Vui lòng tìm kiếm chuyến bay trước khi phân tích."],
            "tasks":        remaining,
            "action_targets": {},
        }

    comp_flights  = action_targets.get("compare_flights")  or []
    comp_airlines = action_targets.get("compare_airlines") or []

    if not comp_flights and not comp_airlines:
        return {
            "node_results": [
                f"{ContextTag.SYS_NOT_FOUND}: Vui lòng tick chọn chuyến bay hoặc hãng bay "
                f"trên màn hình để so sánh nhé!"
            ],
            "action": {
                "type":    "require_flight_selection",
                "payload": {"search_id": current_search_id},
            },
            "tasks":          [],
            "action_targets": {},
        }

    try:
        result_text = await flight_mcp.call_tool("analyze_flights", {
            "search_id":             current_search_id,
            "target_flight_numbers": comp_flights  or None,
            "target_airline_codes":  comp_airlines or None,
        })
    except Exception as e:
        print(f"❌ [analyze MCP error]: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Lỗi kết nối Flight Server khi lấy dữ liệu phân tích."],
            "tasks":          remaining,
            "action_targets": {},
        }

    return {
        "node_results":   [result_text],
        "tasks":          remaining,
        "action_targets": {},
    }