import asyncio
from app.ai_orchestrator.graph.state import ChatState
from app.utils.helpers import consume_task
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent
from app.core.constants import ContextTag
from app.services.redis_service import redis_service

async def filter_sort_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM LỌC & SẮP XẾP ---")

    search_filters    = state.get("search_filters", {})
    current_search_id = state.get("current_search_id")
    tasks             = state.get("tasks", [])
    print(f"👉 [DEBUG] filters: {search_filters}, search_id: {current_search_id}")

    if not current_search_id or current_search_id == "CLEAR":
        return {
            "current_search_id": "CLEAR",
            "tasks": consume_task(
                tasks, "filter_sort_flights",
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT),
            ),
        }

    loop = asyncio.get_running_loop()
    cached_data = await loop.run_in_executor(
        None, redis_service.get_flight_offers, current_search_id
    )
    if not cached_data:
        print(f"❌ Phiên {current_search_id} hết hạn trên Redis")
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Phiên tìm kiếm đã hết hạn. Hệ thống sẽ tự động tìm lại."],
            "current_search_id": "CLEAR",
            "tasks": consume_task(
                tasks, "filter_sort_flights",
                next_task=Task(intent=ChatIntent.SEARCH_FLIGHT),
            ),
        }

    fe_filter_keys = ["maxPrice", "start_hour", "end_hour", "nonStop", "preferred_airlines", "travelClass"]
    fe_filters = {k: search_filters[k] for k in fe_filter_keys if k in search_filters}

    sort_pref = search_filters.get("sort_preference")
    sort_val  = (
        sort_pref.value if hasattr(sort_pref, "value")
        else str(sort_pref) if sort_pref
        else None
    )

    print(f"Type: apply_filters | ID: {current_search_id} | Filters: {fe_filters} | Sort: {sort_val}")

    return {
        "node_results": [f"{ContextTag.FILTER_APPLIED}: Đã gửi lệnh điều chỉnh bộ lọc lên giao diện."],
        "action": {
            "type": "apply_filters",
            "payload": {"search_id": current_search_id, "filters": fe_filters, "sort": sort_val},
        },
        "tasks": consume_task(tasks, "filter_sort_flights"),
    }