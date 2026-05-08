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
    """
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
            logger.debug(f"[extract_context] Tool result parsed: {entry}")

    if not tool_results:
        logger.debug("[extract_context] Không tìm thấy search_id hay filtered_id trong tool messages")
        return None, None

    # Ưu tiên filtered_id
    for entry in reversed(tool_results):
        if "filtered_id" in entry:
            last_search_id = next(
                (e["search_id"] for e in reversed(tool_results)
                 if "search_id" in e and "filtered_id" not in e),
                entry.get("search_id"),
            )
            action = {
                "type":    "apply_filters",
                "payload": {
                    "search_id":   last_search_id,
                    "filtered_id": entry["filtered_id"],
                },
            }
            logger.debug(f"[extract_context] → action=apply_filters search_id={last_search_id} filtered_id={entry['filtered_id']}")
            return last_search_id, action

    for entry in reversed(tool_results):
        if "search_id" in entry:
            action = {
                "type":    "flight_list",
                "payload": {"search_id": entry["search_id"]},
            }
            logger.debug(f"[extract_context] → action=flight_list search_id={entry['search_id']}")
            return entry["search_id"], action

    return None, None


from langchain_core.runnables import RunnableConfig

async def agent_node(
    state: FlightAgentState,
    llm_with_tools,
    config: RunnableConfig | None = None,
) -> dict:
    from langchain_core.messages import SystemMessage
    from app.ai_orchestrator.graph.prompts import build_system_prompt

    test_date = None
    if config:
        test_date = config.get("configurable", {}).get("test_date")

    current_sid = state.get("current_search_id")
    msg_count   = len(state.get("messages", []))

    logger.info(f"[agent_node] CALL — {msg_count} messages in state | current_search_id={current_sid}")

    system_content = build_system_prompt(state, test_date=test_date)
    system_msg     = SystemMessage(content=system_content)

    history = [
        m for m in state["messages"]
        if getattr(m, "type", "") != "system"
    ]

    messages  = [system_msg] + history
    logger.debug(f"[agent_node] Gửi {len(messages)} messages tới LLM (1 system + {len(history)} history)")

    response = await llm_with_tools.ainvoke(messages)

    tool_calls = getattr(response, "tool_calls", [])
    if tool_calls:
        logger.info(f"[agent_node] LLM gọi {len(tool_calls)} tool(s):")
        for tc in tool_calls:
            name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "?")
            args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
            logger.info(f"  → {name}({args})")
    else:
        content_preview = (response.content or "")[:100]
        logger.info(f"[agent_node] LLM không gọi tool, trả lời trực tiếp: '{content_preview}...'")

    return {"messages": [response]}


async def post_process_node(state: FlightAgentState) -> dict:
    messages = state.get("messages", [])
    sf       = dict(state.get("search_filters") or {})
    prev_id  = state.get("current_search_id")

    logger.info(f"[post_process] CALL — prev_search_id={prev_id}")

    new_search_id, action = _extract_context(messages)

    current_search_id = new_search_id or prev_id
    if current_search_id == "CLEAR":
        current_search_id = None

    if new_search_id and new_search_id != prev_id:
        logger.info(f"[post_process] search_id thay đổi: {prev_id} → {new_search_id}")
    elif new_search_id == prev_id:
        logger.info(f"[post_process] search_id giữ nguyên: {current_search_id}")
    else:
        logger.info(f"[post_process] Không có search_id mới, giữ prev: {current_search_id}")

    if action:
        logger.info(f"[post_process] action={action['type']} payload={action.get('payload')}")
    else:
        logger.info("[post_process] action=None")

    return {
        "search_filters":    sf,
        "current_search_id": current_search_id,
        "action":            action,
    }