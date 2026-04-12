import os
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import CURRENT_TIME, CURRENT_TIME_STR, MAX_HISTORY_TURNS, ContextTag
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

prompt_template = ChatPromptTemplate.from_messages([
    ("system", EXTRACT_SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM NHẬN DIỆN Ý ĐỊNH (EXTRACT INTENT) ---")
    
    if state.get("tasks"):
        return {} 

    all_tasks = []
    node_result = [] 
    
    old_search_filters = state.get("search_filters", {})
    new_search_filters = {}
    new_action_targets = {}
    
    global_clear_fields = set()
    core_changed = False
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-MAX_HISTORY_TURNS:]) if history_list else "Chưa có lịch sử trò chuyện."

    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": state.get("user_message", ""),
            "current_time": CURRENT_TIME_STR,
            "chat_history": history_str
        })
        
        print (f"👉 [DEBUG - EXTRACTED RESULT]: {result}")

        if result and result.tasks:
            all_tasks = result.tasks
            all_tasks.sort(key=lambda t: (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) == "out_of_scope")

            valid_intents = [
                ChatIntent.SEARCH_FLIGHT.value, 
                ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, 
                ChatIntent.PROMO_SEARCH.value,
                ChatIntent.POLICY_QUESTION.value
            ]

            filtered_tasks = []
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)

                if intent_str == "out_of_scope" or (hasattr(ChatIntent, 'OUT_OF_SCOPE') and intent_str == getattr(ChatIntent, 'OUT_OF_SCOPE', '').value):
                    context_detail = f"Chủ đề khách hỏi: '{task.query_context}'" if getattr(task, 'query_context', None) else ""
                    
                    node_result.append(
                        f"{ContextTag.OUT_OF_SCOPE}: {context_detail} nằm ngoài phạm vi hỗ trợ "
                        f"(kiến thức chung, phiếm luận...). Bắt buộc phải từ chối trả lời lịch sự."
                    )
                    continue

                filtered_tasks.append(task)
                if intent_str in valid_intents:
                    if task.search_filters:
                        raw_filters = task.search_filters.model_dump(exclude_unset=True, exclude_none=True)
                            
                        global_clear_fields.update(raw_filters.pop("clear_fields", []))
                        array_actions = raw_filters.pop("array_actions", [])
                        
                        for k, v in raw_filters.items():
                            new_search_filters[k] = v
                            
                        for action in array_actions:
                            field = action.get("field_name")
                            if field != "preferred_airlines": continue
                            
                            act = action.get("action")
                            vals = action.get("values", [])
                            
                            current_array = new_search_filters.get(field) or old_search_filters.get(field) or []
                            
                            current_set = set([str(x).upper().replace(" ", "") for x in current_array])
                            target_vals = [str(x).upper().replace(" ", "") for x in vals]
                            
                            if act == "ADD":
                                current_set.update(target_vals)
                            elif act == "REMOVE":
                                current_set.difference_update(target_vals)
                                
                            new_search_filters[field] = list(current_set) if current_set else None

                    if task.action_targets:
                        raw_targets = task.action_targets.model_dump(exclude_unset=True, exclude_none=True)
                        for k, v in raw_targets.items():
                            if isinstance(v, list):
                                new_action_targets[k] = [str(i).upper().replace(" ", "") for i in v if i]
                            else:
                                new_action_targets[k] = v

            for field in global_clear_fields:
                new_search_filters[field] = "CLEAR"
                
            for k, v in old_search_filters.items():
                if k not in new_search_filters and k not in global_clear_fields:
                    new_search_filters[k] = v

            CORE_FIELDS = ["origin", "destination", "departureDate", "returnDate", "roundTrip", "adults", "children", "infants", "travelClass"]
            core_changes_str = []
            filter_changes_str = []
            
            for k, v in new_search_filters.items():
                if v != old_search_filters.get(k):
                    if k in CORE_FIELDS:
                        core_changed = True
                        core_changes_str.append(f"{k}: {v}")
                    else:
                        filter_changes_str.append(f"{k}: {v if v is not None else 'Đã Hủy'}")
                        
            for k, v in old_search_filters.items():
                if k not in new_search_filters and v is not None:
                    if k in CORE_FIELDS:
                        core_changed = True
                        core_changes_str.append(f"{k}: Đã Hủy")
                    else:
                        filter_changes_str.append(f"{k}: Đã Hủy")

            if core_changed:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi thông số cốt lõi ({', '.join(core_changes_str)}). Yêu cầu gọi API mới.")
            elif filter_changes_str:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi bộ lọc hiển thị ({', '.join(filter_changes_str)}).")

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: Không thể bóc tách dữ liệu: {e}")
        filtered_tasks = all_tasks 
        
    result_dict = {
        "tasks": filtered_tasks if 'filtered_tasks' in locals() else all_tasks, 
        "search_filters": new_search_filters,
        "action_targets": new_action_targets,
        "node_results": node_result
    }

    if core_changed:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW FILTERS]: ", new_search_filters)
    print("👉 [DEBUG - NEW TARGETS]: ", new_action_targets)
    
    tasks_to_print = filtered_tasks if 'filtered_tasks' in locals() else all_tasks
    print("👉 [DEBUG - TASK]: ", [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in tasks_to_print])
    print("🔹🔹🔹 ------------------------------------")

    return result_dict