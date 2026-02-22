from typing import Optional, Literal
from datetime import datetime
from app.ai.llm.llm import llm
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from app.core.i18n_service import i18n

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
    origin: Optional[str] = Field(default=None, description="3-letter uppercase IATA code of origin (e.g., HAN, SGN, DAD)")
    destination: Optional[str] = Field(default=None, description="3-letter uppercase IATA code of destination (e.g., HAN, SGN, DAD)")
    departureDate: Optional[str] = Field(default=None, description="Departure date in YYYY-MM-DD format")
    returnDate: Optional[str] = Field(default=None, description="Return date in YYYY-MM-DD format")
    adults: Optional[int] = Field(default=None, ge=1)

structured_llm = llm.with_structured_output(IntentExtractionResult)

def extract_intent_and_slots(message: str, lang: str = "vi") -> IntentExtractionResult:
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        system_prompt_text = i18n.get_msg("extractor_system_prompt", lang=lang, current_time=current_time)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt_text),
            ("human", "{message}")
        ])

        extraction_chain = prompt | structured_llm

        result = extraction_chain.invoke({
            "message": message
        })

        print("INTENT EXTRACTION RESULT:", result)
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