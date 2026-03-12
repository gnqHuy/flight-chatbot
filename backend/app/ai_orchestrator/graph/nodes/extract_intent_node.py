from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.llm.llm import llm
from app.schemas.chat_state import ExtractionOutput, Task
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """You are an AI intent classifier for a flight booking system. 
Current time: {current_time}.

RECENT CHAT HISTORY (For context reference only):
{chat_history}

TASK: Classify the user's message into one of the following Intents:
1. 'search_flight': Searching for flights, checking prices.
2. 'analyze_flights': Comparing prices, duration, or airlines between different flight options.
3. 'provide_info': Providing departure/destination, dates, or answering bot's follow-up questions.
4. 'greeting': Basic greetings, thanks (e.g., Hello, thank you, bye).
5. 'general_question': Questions about flight policies, luggage, documents, pregnant passengers, or airline regulations. (Use this for RAG).
6. 'out_of_scope': STRICTLY FOR NON-AVIATION TOPICS.

CRITICAL RULES & CLUSTERING:
- [ANTI-HALLUCINATION - VERY IMPORTANT]: DO NOT guess, assume, or auto-fill ANY parameters (especially departureDate, returnDate). ONLY extract information EXPLICITLY stated by the user. If the user does not mention a date or a location, you MUST leave it as null/None.
- If the user's message contains multiple distinct requests (e.g., searching for a flight AND asking a general question), output MULTIPLE tasks in the tasks list, one for each request.
- GROUP FLIGHT INFO: All flight-related parameters (origin, destination, date, airline preferences, filters) MUST be grouped into a SINGLE 'search_flight' or 'analyze_flights' task.
- SEPARATE RAG/GREETINGS: General policy questions MUST be separated into distinct tasks.
- Use the 'current_time' provided ONLY to resolve explicitly mentioned relative dates like 'tomorrow', 'next Monday', etc. Format dates as YYYY-MM-DD.
- [IMPORTANT]: If the user explicitly asks to CANCEL, REMOVE, or CLEAR a specific filter, you MUST output the exact string "CLEAR" for that specific parameter.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE EXTRACT INTENT ---")
    
    if state.get("tasks"):
        return {} 

    all_tasks = []
    node_result = [] 
    current_prefs = {}
    old_prefs = state.get("user_prefs", {}) 
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "No previous history."
    
    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": state.get("user_message", ""),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "chat_history": history_str
        })

        if result and result.tasks:
            all_tasks = result.tasks
            flight_intents = ["search_flight", "analyze_flights", "provide_info", "price_analysis"]
            
            clean_params = {}
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                if intent_str in flight_intents and task.parameters:
                    for k, v in task.parameters.model_dump(exclude_none=True).items():
                        if v == "CLEAR" or v == ["CLEAR"]:
                            clean_params[k] = v
                        elif v is not None and v != "" and v != []:
                            clean_params[k] = v

            core_search_params = [
                "origin", "destination", "departureDate", "returnDate", 
                "includedAirlines", "excludedAirlines", "nonStop", 
                "travelClass", "maxPrice", "start_hour", "end_hour"
            ]
            
            changed_details = []
            for param in core_search_params:
                if param in clean_params and clean_params[param] != old_prefs.get(param):
                    changed_details.append(f"{param}: {clean_params[param]}")
                    clean_params["current_search_id"] = "CLEAR"

            if changed_details:
                change_info = ", ".join(changed_details)
                node_result.append(f"[Cập nhật thông tin]: Hệ thống đã ghi nhận thay đổi tham số ({change_info}) và tìm kiếm lại kết quả mới nhất cho khách hàng.")

            if "target_flights" in clean_params:
                raw_targets = clean_params["target_flights"]
                if isinstance(raw_targets, list):
                    clean_params["target_flights"] = [str(t).upper().replace(" ", "") for t in raw_targets if t]

            current_prefs.update(clean_params)

            if changed_details:
                has_search = any(
                    (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) == ChatIntent.SEARCH_FLIGHT.value
                    for t in all_tasks
                )
                if not has_search:
                    ref_params = next((t.parameters for t in all_tasks if (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) in flight_intents), None)
                    all_tasks.insert(0, Task(intent=ChatIntent.SEARCH_FLIGHT, parameters=ref_params, query_context="Auto-refresh search"))

    except Exception as e:
        print(f"Lỗi extract intent: {e}")
        
    saved_intents = [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in all_tasks]

    print(f"\n Extracted Tasks: {saved_intents}")
    print(f" Current User Preferences: {current_prefs}")
    
    return {
        "tasks": all_tasks,
        "user_prefs": current_prefs,
        "executed_intents": saved_intents,
        "node_results": node_result
    }