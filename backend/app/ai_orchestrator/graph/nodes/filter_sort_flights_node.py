"""
app/ai_orchestrator/graph/nodes/filter_sort_flights_node.py
Thin async wrapper — filter/sort xử lý server-side trong mcp-flight.
"""
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp
from app.utils.helpers import consume_task
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent
from app.core.constants import ContextTag


async def filter_sort_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM LỌC & SẮP XẾP (MCP FLIGHT) ---")

    sf                = state.get("search_filters", {})
    current_search_id = state.get("current_search_id")
    tasks             = state.get("tasks", [])
    remaining         = consume_task(tasks, "filter_sort_flights")

    if not current_search_id or current_search_id == "CLEAR":
        return {
            "current_search_id": "CLEAR",
            "tasks": consume_task(
                tasks, "filter_sort_flights",
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT),
            ),
        }

    sort_pref = sf.get("sort_preference")
    sort_val  = (
        sort_pref.value if hasattr(sort_pref, "value")
        else str(sort_pref) if sort_pref else None
    )

    try:
        result_text = await flight_mcp.call_tool("get_filtered_flights", {
            "search_id":          current_search_id,
            "maxPrice":           sf.get("maxPrice"),
            "preferred_airlines": sf.get("preferred_airlines"),
            "nonStop":            sf.get("nonStop"),
            "travelClass":        sf.get("travelClass"),
            "start_hour":         sf.get("start_hour"),
            "end_hour":           sf.get("end_hour"),
            "sort_preference":    sort_val,
        })
    except Exception as e:
        print(f"❌ [filter MCP error]: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Lỗi kết nối Flight Server khi lọc vé."],
            "tasks":        remaining,
        }

    filtered_id = _extract_value(result_text, "filtered_id")

    action = None
    if filtered_id and filtered_id != "NONE":
        action = {
            "type":    "apply_filters",
            "payload": {
                "search_id":   current_search_id,
                "filtered_id": filtered_id,
            },
        }

    return {
        "node_results": [result_text],
        "action":       action,
        "tasks":        remaining,
    }


def _extract_value(text: str, key: str) -> str | None:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(f"{key}="):
            val = line.split("=", 1)[1].strip()
            return None if val in ("None", "NONE", "") else val
    return None