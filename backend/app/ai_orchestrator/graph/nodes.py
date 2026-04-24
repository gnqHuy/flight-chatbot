"""
app/ai_orchestrator/graph/nodes.py
"""
import logging
from langchain_core.messages import AnyMessage
from app.ai_orchestrator.graph.state import FlightAgentState

logger = logging.getLogger(__name__)


def _extract_context(messages: list[AnyMessage]) -> tuple[str | None, dict | None]:
    """
    Duyệt tool messages, extract search_id và action.

    Ưu tiên action theo thứ tự:
      apply_filters > flight_list > None

    Mỗi tool message được parse riêng để pair đúng
    search_id với filtered_id của cùng 1 tool call.
    """
    # Parse từng tool message riêng
    # Mỗi entry: {"search_id": ..., "filtered_id": ...}
    tool_results = []
    for msg in messages:
        if getattr(msg, "type", "") != "tool":
            continue
        content = getattr(msg, "content", "")
        if not isinstance(content, str):
            continue
        entry = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("search_id="):
                val = line.split("=", 1)[1].strip()
                if val not in ("NONE", "None", ""):
                    entry["search_id"] = val
            elif line.startswith("filtered_id="):
                val = line.split("=", 1)[1].strip()
                if val not in ("NONE", "None", ""):
                    entry["filtered_id"] = val
        if entry:
            tool_results.append(entry)

    if not tool_results:
        return None, None

    # Tìm entry có filtered_id (ưu tiên nhất)
    for entry in reversed(tool_results):
        if "filtered_id" in entry:
            action = {
                "type":    "apply_filters",
                "payload": {
                    "search_id":   entry.get("search_id"),
                    "filtered_id": entry["filtered_id"],
                },
            }
            # search_id trả về: dùng cái từ search call (không phải filter call)
            last_search_id = next(
                (e["search_id"] for e in reversed(tool_results) if "search_id" in e and "filtered_id" not in e),
                entry.get("search_id"),
            )
            return last_search_id, action

    # Không có filter → lấy search_id mới nhất
    for entry in reversed(tool_results):
        if "search_id" in entry:
            action = {
                "type":    "flight_list",
                "payload": {"search_id": entry["search_id"]},
            }
            return entry["search_id"], action

    return None, None


from langchain_core.runnables import RunnableConfig

async def agent_node(state: FlightAgentState, llm_with_tools, config: RunnableConfig | None = None) -> dict:
    """
    LLM quyết định gọi tool nào dựa trên messages và context.
    System prompt được build tại đây để:
    1. Luôn reflect state mới nhất (search_id, filters)
    2. Tránh lỗi 'multiple non-consecutive system messages' với Claude
    3. Nhận test_date từ config khi chạy test
    """
    from langchain_core.messages import SystemMessage
    from app.ai_orchestrator.graph.prompts import build_system_prompt

    # Đọc test_date từ config nếu có (dùng khi chạy test automation)
    test_date = None
    if config:
        test_date = config.get("configurable", {}).get("test_date")

    # Build system prompt với state hiện tại
    system_content = build_system_prompt(state, test_date=test_date)
    system_msg     = SystemMessage(content=system_content)

    # Lọc bỏ SystemMessage cũ trong history, chỉ giữ Human + AI + Tool
    history = [
        m for m in state["messages"]
        if getattr(m, "type", "") != "system"
    ]

    messages = [system_msg] + history
    response = await llm_with_tools.ainvoke(messages)
    return {"messages": [response]}


async def post_process_node(state: FlightAgentState) -> dict:
    """
    Chạy sau khi LLM trả lời xong.
    Extract search_id và action từ tool messages → persist vào state.
    """
    messages = state.get("messages", [])
    sf       = dict(state.get("search_filters") or {})
    prev_id  = state.get("current_search_id")

    new_search_id, action = _extract_context(messages)

    current_search_id = new_search_id or prev_id
    if current_search_id == "CLEAR":
        current_search_id = None

    if new_search_id:
        logger.info(f"[post_process] search_id={new_search_id} action={action['type'] if action else None}")

    return {
        "search_filters":    sf,
        "current_search_id": current_search_id,
        "action":            action,
    }