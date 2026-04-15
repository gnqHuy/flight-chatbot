from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import CURRENT_TIME_STR, MAX_HISTORY_TURNS, ContextTag
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

prompt_template = ChatPromptTemplate.from_messages([
    ("system", EXTRACT_SYSTEM_PROMPT),
    ("human", "{query}")
])
extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

async def extract_intent_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM NHẬN DIỆN Ý ĐỊNH ---")

    if state.get("tasks"):
        return {}

    all_tasks, node_result = [], []
    old_search_filters = state.get("search_filters", {})
    new_search_filters, new_action_targets = {}, {}
    global_clear_fields = set()
    core_changed = False

    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str  = "\n".join(history_list[-MAX_HISTORY_TURNS:]) if history_list else "Chưa có lịch sử trò chuyện."

    try:
        result: ExtractionOutput = await extraction_chain.ainvoke({  # FIX: ainvoke
            "query":        state.get("user_message", ""),
            "current_time": CURRENT_TIME_STR,
            "chat_history": history_str,
        })
        print(f"👉 [DEBUG - EXTRACTED RESULT]: {result}")

        if result and result.tasks:
            all_tasks = result.tasks
            all_tasks.sort(key=lambda t: (t.intent.value if hasattr(t.intent, "value") else str(t.intent)) == "out_of_scope")

            valid_intents = [
                ChatIntent.SEARCH_FLIGHT.value, ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, ChatIntent.PROMO_SEARCH.value,
                ChatIntent.POLICY_QUESTION.value,
            ]
            filtered_tasks = []

            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, "value") else str(task.intent)

                if intent_str == "out_of_scope":
                    ctx = f"Chủ đề: '{task.query_context}'" if getattr(task, "query_context", None) else ""
                    node_result.append(
                        f"{ContextTag.OUT_OF_SCOPE}: {ctx} nằm ngoài phạm vi hỗ trợ. Bắt buộc từ chối lịch sự."
                    )
                    continue

                filtered_tasks.append(task)
                if intent_str in valid_intents:
                    if task.search_filters:
                        raw = task.search_filters.model_dump(exclude_unset=True, exclude_none=True)
                        global_clear_fields.update(raw.pop("clear_fields", []))
                        array_actions = raw.pop("array_actions", [])
                        for k, v in raw.items():
                            new_search_filters[k] = v
                        for action in array_actions:
                            field = action.get("field_name")
                            if field != "preferred_airlines":
                                continue
                            act  = action.get("action")
                            vals = action.get("values", [])
                            cur  = set(str(x).upper().replace(" ", "") for x in (
                                new_search_filters.get(field) or old_search_filters.get(field) or []
                            ))
                            tgt = [str(x).upper().replace(" ", "") for x in vals]
                            if act == "ADD":    cur.update(tgt)
                            elif act == "REMOVE": cur.difference_update(tgt)
                            new_search_filters[field] = list(cur) if cur else None

                    if task.action_targets:
                        raw_t = task.action_targets.model_dump(exclude_unset=True, exclude_none=True)
                        for k, v in raw_t.items():
                            new_action_targets[k] = (
                                [str(i).upper().replace(" ", "") for i in v if i]
                                if isinstance(v, list) else v
                            )

            for field in global_clear_fields:
                new_search_filters[field] = "CLEAR"
            for k, v in old_search_filters.items():
                if k not in new_search_filters and k not in global_clear_fields:
                    new_search_filters[k] = v

            CORE = ["origin","destination","departureDate","returnDate","roundTrip","adults","children","infants","travelClass"]
            core_str, filter_str = [], []
            for k, v in new_search_filters.items():
                if v != old_search_filters.get(k):
                    (core_str if k in CORE else filter_str).append(f"{k}: {v}")
                    if k in CORE: core_changed = True
            for k, v in old_search_filters.items():
                if k not in new_search_filters and v is not None:
                    (core_str if k in CORE else filter_str).append(f"{k}: Đã Hủy")
                    if k in CORE: core_changed = True

            if core_changed:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi thông số cốt lõi ({', '.join(core_str)}). Yêu cầu gọi API mới.")
            elif filter_str:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi bộ lọc ({', '.join(filter_str)}).")

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: {e}")
        filtered_tasks = all_tasks

    result_dict = {
        "tasks":          filtered_tasks if "filtered_tasks" in locals() else all_tasks,
        "search_filters": new_search_filters,
        "action_targets": new_action_targets,
        "node_results":   node_result,
    }
    if core_changed:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW FILTERS]:", new_search_filters)
    print("👉 [DEBUG - NEW TARGETS]:", new_action_targets)
    print("🔹🔹🔹 ------------------------------------")
    return result_dict