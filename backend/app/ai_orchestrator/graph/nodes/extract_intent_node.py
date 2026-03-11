from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.llm.llm import llm
from app.schemas.chat_state import ExtractionOutput

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
- If the user's message contains multiple distinct requests (e.g., searching for a flight AND asking a general question), output MULTIPLE tasks in the tasks list, one for each request.
- GROUP FLIGHT INFO: All flight-related parameters (origin, destination, date, airline preferences, filters) MUST be grouped into a SINGLE 'search_flight' or 'analyze_flights' task.
- SEPARATE RAG/GREETINGS: General policy questions (luggage, pets, pregnant passengers) or greetings MUST be separated into distinct tasks.
- Use the 'current_time' provided to resolve relative dates like 'tomorrow', 'next Monday', etc. Format dates as YYYY-MM-DD.
- [IMPORTANT]: If the user explicitly asks to CANCEL, REMOVE, or CLEAR a specific filter (e.g., "don't filter airlines anymore", "cancel return ticket", "any price is fine"), you MUST output the exact string "CLEAR" for that specific parameter.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE EXTRACT INTENT ---")
    print("Current State in Extract Intent Node: \n", state)
    all_tasks = []
    current_prefs = {}
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    old_prefs = state.get("user_prefs", {}) 
    
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "No previous history."
    
    user_message = state.get("user_message", "")

    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": user_message,
            "current_time": current_time_str,
            "chat_history": history_str
        })

        print("Extraction Result:", result)
        
        if result and result.tasks:
            for task in result.tasks:
                all_tasks.append(task)
                
                flight_intents = ["search_flight", "analyze_flights", "provide_info", "price_analysis"]
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                
                if intent_str in flight_intents and task.parameters:
                    params_dict = task.parameters.model_dump(exclude_none=True)

                    clean_params = {}
                    for k, v in params_dict.items():
                        if v == "CLEAR" or v == ["CLEAR"]:
                            clean_params[k] = v
                        elif v is not None and v != "" and v != [] and v != 0:
                            clean_params[k] = v

                    search_params = [
                        "origin", "destination", "departureDate", "returnDate", 
                        "includedAirlines", "excludedAirlines", "nonStop", 
                        "travelClass", "maxPrice", "comparison_target", "start_hour", "end_hour", "target_flights"
                    ]
                    
                    for param in search_params:
                        if param in clean_params and clean_params[param] != old_prefs.get(param):
                            clean_params["current_search_id"] = "CLEAR"
                            break
                        
                    if "target_flights" in clean_params:
                        raw_targets = clean_params["target_flights"]
                        if isinstance(raw_targets, list):
                            clean_params["target_flights"] = [str(t).upper().replace(" ", "") for t in raw_targets]

                    current_prefs.update(clean_params)
                    
    except Exception as e:
        print(f"Lỗi khi extract intent cho query '{user_message}': {e}")
        
    print("Extracted Tasks:", all_tasks)
    print("Current User Preferences:", current_prefs)
    
    return {
        "tasks": all_tasks,
        "user_prefs": current_prefs
    }