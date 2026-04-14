from app.ai_orchestrator.graph.state import ChatState
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

# Import MCP Client Manager (Singleton instance)
from app.ai_orchestrator.graph.tools.mcp_client import knowledge_mcp

async def promo_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM KHUYẾN MÃI (QUA MCP) ---")
    
    search_filters = state.get("search_filters", {})
    action_targets = state.get("action_targets", {})
    user_message = state.get("user_message", "")
    
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "promo_search") 
    
    query = user_message 
    
    # Lấy hãng bay ưu tiên (ưu tiên action_targets trước, sau đó đến search_filters)
    target_airline_list = action_targets.get("compare_airlines") or search_filters.get("preferred_airlines") or []
    
    # Lọc bỏ giá trị "CLEAR" (nếu có) trước khi gửi sang MCP Promo
    valid_airlines = [al.upper() for al in target_airline_list if al.upper() != "CLEAR"]
    target_airline_code = valid_airlines[0] if valid_airlines else None

    if not query:
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không xác định được nhu cầu tìm khuyến mãi."],
            "tasks": remaining_tasks
        }

    try:
        # Gọi sang Knowledge Server qua MCP
        result_text = await knowledge_mcp.call_tool(
            tool_name="get_active_promotions",
            arguments={
                "query": query,
                "airline_code": target_airline_code
            }
        )
        
        print(f"👉 [MCP PROMO SUCCESS]: Đã lấy được dữ liệu khuyến mãi.")
        return {
            "node_results": [result_text], 
            "tasks": remaining_tasks 
        }
    
    except Exception as e:
        print(f"❌ ERROR - Promo MCP Node: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống mất kết nối tới Knowledge Server khi tra cứu khuyến mãi. Chi tiết: {str(e)}"],
            "tasks": remaining_tasks
        }