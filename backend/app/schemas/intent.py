from pydantic import BaseModel
from typing import Optional, Literal

class IntentResult(BaseModel):
    intent: Literal[
        "search_flight",
        "provide_info",
        "filter_result",
        "compare_flights",
        "ask_detail",
        "general_question",
        "out_of_scope"
    ]
    origin: Optional[str]
    destination: Optional[str]
    departureDate: Optional[str]
    returnDate: Optional[str]
    adults: Optional[int]
