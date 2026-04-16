"""
app/ai_orchestrator/graph/nodes/search_flight_node.py
Thin async wrapper — toàn bộ logic nằm trong mcp-flight server.
"""
import json
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp
from app.utils.helpers import consume_task
from app.core.constants import ContextTag, SUPPORTED_AIRLINES


async def search_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM (MCP FLIGHT) ---")

    sf      = state.get("search_filters", {})
    tasks   = state.get("tasks", [])
    remaining = consume_task(tasks, ["search_flight"])
    current_search_id = state.get("current_search_id")

    try:
        result_text = await flight_mcp.call_tool("search_flights", {
            "origin":            sf.get("origin"),
            "destination":       sf.get("destination"),
            "departureDate":     sf.get("departureDate"),
            "roundTrip":         sf.get("roundTrip", False),
            "returnDate":        sf.get("returnDate"),
            "adults":            sf.get("adults", 1),
            "children":          sf.get("children", 0),
            "infants":           sf.get("infants", 0),
            "travelClass":       sf.get("travelClass"),
            "preferred_airlines": sf.get("preferred_airlines") or [],
            "current_search_id": current_search_id,
        })
    except Exception as e:
        print(f"❌ [search_flights MCP error]: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không thể kết nối tới Flight Server."],
            "tasks": remaining,
        }

    new_search_id = _extract_value(result_text, "search_id")

    if not new_search_id or new_search_id == "NONE":
        return {"node_results": [result_text], "tasks": remaining}

    action = {
        "type":    "flight_list",
        "payload": {"search_id": new_search_id},
    }

    return {
        "node_results":      [result_text],
        "action":            action,
        "current_search_id": new_search_id,
        "chat_history":      {"search_ids": [new_search_id]},
        "tasks":             remaining,
    }


def _extract_value(text: str, key: str) -> str | None:
    """Tìm 'key=value' trong text trả về từ MCP tool."""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            val = line.split("=", 1)[1].strip()
            return None if val in ("None", "NONE", "") else val
    return None