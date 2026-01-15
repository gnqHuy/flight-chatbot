from typing import Optional, Literal

from app.ai.llm.llm import llm
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

ChatIntent = Literal[
    "search_flight",
    "provide_info",
    "filter_result",
    "compare_flights",
    "ask_detail",
    "general_question",
    "out_of_scope",
]

class IntentExtractionResult(BaseModel):
    intent: ChatIntent
    origin: Optional[str] = None
    destination: Optional[str] = None
    departureDate: Optional[str] = None
    returnDate: Optional[str] = None
    adults: Optional[int] = Field(default=None, ge=1)


structured_llm = llm.with_structured_output(IntentExtractionResult)

def extract_intent_and_slots(message: str) -> IntentExtractionResult:
    try:
        result = structured_llm.invoke(message)
        return result

    except Exception as e:
        print("INTENT EXTRACTION ERROR:", e)

        return IntentExtractionResult(
            intent="out_of_scope",
            origin=None,
            destination=None,
            departureDate=None,
            returnDate=None,
            adults=None,
        )
