from app.ai_orchestrator.graph.state import ChatState
from app.core.enums import ChatIntent
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

from app.ai_orchestrator.graph.tools.mcp_client import knowledge_mcp

async def policy_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TRA CỨU CHÍNH SÁCH (QUA MCP) ---")
    
    search_filters = state.get("search_filters", {})
    action_targets = state.get("action_targets", {})
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "policy_question")
    
    query = ""
    for task in tasks:
        intent_val = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
        if intent_val == ChatIntent.POLICY_QUESTION.value or intent_val == "POLICY_QUESTION":
            query = getattr(task, 'query_context', "")
            break
            
    if not query:
        query = state.get("user_message", "")

    if not query:
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không xác định được câu hỏi để tra cứu chính sách."],
            "tasks": remaining_tasks
        }

    target_airlines = []
    if action_targets.get("compare_airlines"):
        target_airlines = action_targets.get("compare_airlines")
    elif search_filters.get("preferred_airlines"):
        target_airlines = search_filters.get("preferred_airlines")

    if isinstance(target_airlines, str):
        target_airlines = [target_airlines]
    
    try:
        result_text = await knowledge_mcp.call_tool(
            tool_name="search_airline_policies",
            arguments={
                "query": query,
                "airline_codes": target_airlines if target_airlines else []
            }
        )
        
        return {
            "node_results": [result_text], 
            "tasks": remaining_tasks 
        }
        
    except Exception as e:
        print(f"ERROR - Policy MCP Node: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống mất kết nối tới Knowledge Server khi tra cứu chính sách."],
            "tasks": remaining_tasks
        }