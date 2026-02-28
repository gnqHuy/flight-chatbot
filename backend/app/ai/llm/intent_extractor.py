from typing import Optional, Literal
from datetime import datetime
from app.ai.llm.llm import llm
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

ChatIntent = Literal[
    "search_flight",
    "provide_info",
    "filter_result",
    "compare_flights",
    "ask_detail",
    "general_question",
    "out_of_scope",
    "greeting"
]

class IntentExtractionResult(BaseModel):
    intent: ChatIntent
    origin: Optional[str] = Field(default=None, description="3-letter IATA code")
    destination: Optional[str] = Field(default=None, description="3-letter IATA code")
    departureDate: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    returnDate: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    adults: Optional[int] = Field(default=None, ge=1)

structured_llm = llm.with_structured_output(IntentExtractionResult)

SYSTEM_PROMPT = """You are an AI intent classifier for a flight booking system. Current time: {current_time}.

TASK: Classify the user's message into one of the following Intents:
1. 'search_flight': Searching for flights, checking prices.
2. 'provide_info': Providing departure/destination or dates.
3. 'greeting': Basic greetings, thanks (e.g., Hello, thank you, bye).
4. 'general_question': Questions about flight policies, luggage, documents, pregnant passengers, or airline regulations. (Use this for RAG).
5. 'out_of_scope': STRICTLY FOR NON-AVIATION TOPICS. (e.g., weather forecasts, coding, math, recipes, news...).

CRITICAL: 
- If the user asks about rules, baggage, or "can I...", use 'general_question'.
- If the query is completely unrelated to flights or aviation, you MUST return 'out_of_scope'."""

def extract_intent_and_slots(message: str) -> IntentExtractionResult:
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "{message}")
        ])

        extraction_chain = prompt | structured_llm

        result = extraction_chain.invoke({
            "current_time": current_time,
            "message": message
        })
        
        return result

    except Exception as e:
        print("INTENT EXTRACTION ERROR:", e)
        return IntentExtractionResult(intent="out_of_scope")