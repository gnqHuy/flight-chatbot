import os
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.prompts.extract_prompt import EXTRACT_SYSTEM_PROMPT
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import ContextTag
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

prompt_template = ChatPromptTemplate.from_messages([
    ("system", EXTRACT_SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO TRẠM NHẬN DIỆN Ý ĐỊNH (EXTRACT INTENT) ---")
    
    if state.get("tasks"):
        return {} 

    all_tasks = []
    node_result = [] 
    
    old_search_filters = state.get("search_filters", {}) or {}
    new_search_filters = {}
    new_action_targets = {}
    
    global_clear_fields = set()
    global_reset = False
    core_changed = False
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "Chưa có lịch sử trò chuyện."

    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": state.get("user_message", ""),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
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
                ChatIntent.GENERAL_QUESTION.value
            ]
            
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                
                if intent_str in valid_intents:
                    if task.search_filters:
                        raw_filters = task.search_filters.model_dump(exclude_unset=True, exclude_none=True)
                        
                        if raw_filters.pop("reset_search", False):
                            global_reset = True
                            
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
                            if global_reset: current_array = new_search_filters.get(field) or [] 
                            
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
                
            if not global_reset:
                for k, v in old_search_filters.items():
                    if k not in new_search_filters and k not in global_clear_fields:
                        new_search_filters[k] = v
            else:
                core_changed = True

            CORE_FIELDS = ["origin", "destination", "departureDate", "returnDate", "roundTrip", "adults", "children", "infants"]
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
                
            if new_action_targets:
                targets_info = []
                if new_action_targets.get("compare_airlines"): targets_info.append(f"Hãng: {new_action_targets['compare_airlines']}")
                if new_action_targets.get("compare_flights"): targets_info.append(f"Chuyến: {new_action_targets['compare_flights']}")
                if targets_info:
                    node_result.append(f"{ContextTag.USER_UPDATE}: Yêu cầu thao tác trên mục tiêu: {', '.join(targets_info)}.")

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: Không thể bóc tách dữ liệu: {e}")
        
    result_dict = {
        "tasks": all_tasks,
        "search_filters": new_search_filters,
        "action_targets": new_action_targets,
        "node_results": node_result
    }

    if core_changed:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW FILTERS]: ", new_search_filters)
    print("👉 [DEBUG - NEW TARGETS]: ", new_action_targets)
    print("👉 [DEBUG - TASK]: ", [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in all_tasks])
    print("🔹🔹🔹 ------------------------------------")

    return result_dict