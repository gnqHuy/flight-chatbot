from langchain_core.tools import tool
from app.ai_orchestrator.graph.prompts.analyze_prompt import ANALYZE_SYSTEM_PROMPT
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.graph.tools.flight_tools import fetch_airline_info, fetch_flight_details
from app.utils.helpers import consume_task
from app.core.constants import ContextTag
from app.core.llm_setup import llm

llm_with_tools = llm.bind_tools([fetch_airline_info, fetch_flight_details])

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH (TOOL CALLING AGENT) ---")
    
    user_message = state.get("user_message", "")
    action_targets = state.get("action_targets", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "analyze_flights")
    comp_airlines = action_targets.get("compare_airlines", [])
    comp_flights = action_targets.get("compare_flights", [])
    
    if not current_search_id or current_search_id in ["CLEAR", "NOT_FOUND"]:
        return _build_error("Vui lòng tìm kiếm chuyến bay trước khi phân tích.", remaining_tasks)

    if not comp_airlines and not comp_flights:
        return {
            "node_results": ["[THÔNG BÁO]: Bạn chưa chọn chuyến bay hoặc hãng bay nào để phân tích. Vui lòng tick chọn ít nhất 1 chuyến hoặc 1 hãng."],
            "action": {"type": "require_flight_selection", "payload": {"search_id": current_search_id}},
            "tasks": [], 
        }
    
    ai_msg = llm_with_tools.invoke([
        ("system", ANALYZE_SYSTEM_PROMPT),
        ("human", user_message)
    ])

    gathered_data = []
    
    if not ai_msg.tool_calls:
        print("⚠️ LLM không gọi tool, tự động fallback gọi tool bằng Python...")
        if comp_airlines: gathered_data.append(fetch_airline_info.invoke({"airline_codes": comp_airlines, "search_id": current_search_id}))
        if comp_flights: gathered_data.append(fetch_flight_details.invoke({"flight_ids": comp_flights, "search_id": current_search_id}))
    else:
        for tool_call in ai_msg.tool_calls:
            print(f"🧠 [AGENT GỌI TOOL]: {tool_call['name']} với args: {tool_call['args']}")
            
            if tool_call["name"] == "fetch_airline_info":
                res = fetch_airline_info.invoke(tool_call["args"])
                gathered_data.append(res)
                
            elif tool_call["name"] == "fetch_flight_details":
                res = fetch_flight_details.invoke(tool_call["args"])
                gathered_data.append(res)

    final_context = "\n\n".join(gathered_data) if gathered_data else "Không lấy được dữ liệu."
    
    report = (
        f"{ContextTag.FLIGHT_ANALYSIS}:\n"
        f"--- DỮ LIỆU ĐƯỢC GOM TỪ AGENT ---\n"
        f"{final_context}\n\n"
        f"⚠️ CHỈ THỊ: Dựa vào Dữ liệu trên và Yêu cầu của khách, hãy viết một bài phân tích/so sánh khách quan, rõ ràng. Không tự bịa số liệu."
    )

    print("👉 [DEBUG]: Kết quả phân tích sơ bộ từ Agent:\n", report)

    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "action_targets": {}
    }

def _build_error(msg: str, tasks: list) -> dict:
    return {
        "node_results": [f"{ContextTag.SYS_ERROR}: {msg}"],
        "tasks": tasks,
        "action_targets": {}
    }