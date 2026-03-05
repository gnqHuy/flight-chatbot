from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai.graph.state import ChatState
from app.ai.llm.llm import llm
from app.schemas.chat_state import ExtractionOutput

SYSTEM_PROMPT = """You are an AI intent classifier for a flight booking system. 
Current time: {current_time}.

TASK: Classify the user's message into one of the following Intents:
1. 'search_flight': Searching for flights, checking prices.
2. 'provide_info': Providing departure/destination or dates.
3. 'greeting': Basic greetings, thanks (e.g., Hello, thank you, bye).
4. 'general_question': Questions about flight policies, luggage, documents, pregnant passengers, or airline regulations. (Use this for RAG).
5. 'out_of_scope': STRICTLY FOR NON-AVIATION TOPICS.

CRITICAL: 
- Use the 'current_time' provided to resolve relative dates like 'tomorrow', 'next Monday', etc.
- If the user asks about rules, baggage, or "can I...", use 'general_question'.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    all_tasks = []
    current_prefs = {}
    
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[DEBUG] Current Time for Intent Extraction: {current_time_str}")
    for query in state["sub_queries"]:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": query,
            "current_time": current_time_str
        })
        
        if result.tasks:
            for task in result.tasks:
                all_tasks.append(task)
                if task.intent == "search_flight" and task.parameters:
                    params_dict = task.parameters.model_dump(exclude_none=True)
                    current_prefs.update(params_dict)
                    
    print(f"\n[DEBUG] Current Time Sent to AI: {current_time_str}")
    print("Extracted Tasks:", all_tasks)
    print("Current User Preferences:", current_prefs)
    
    return {
        "tasks": all_tasks,
        "user_prefs": current_prefs
    }