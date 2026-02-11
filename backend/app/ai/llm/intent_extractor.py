from typing import Optional, Literal
from datetime import datetime
from app.ai.llm.llm import llm
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

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
    origin: Optional[str] = Field(default=None, description="Mã IATA 3 chữ cái của điểm đi (VD: HAN, SGN, DAD)")
    destination: Optional[str] = Field(default=None, description="Mã IATA 3 chữ cái của điểm đến (VD: HAN, SGN, DAD)")
    departureDate: Optional[str] = Field(default=None, description="Ngày đi định dạng YYYY-MM-DD")
    returnDate: Optional[str] = Field(default=None, description="Ngày về định dạng YYYY-MM-DD")
    adults: Optional[int] = Field(default=None, ge=1)

structured_llm = llm.with_structured_output(IntentExtractionResult)

system_prompt = """
Bạn là trợ lý AI chuyên trích xuất thông tin đặt vé máy bay.
Thời gian hiện tại: {current_time}

QUY TẮC BẮT BUỘC:
1. Điểm đi (origin) và Điểm đến (destination) PHẢI là MÃ IATA 3 CHỮ CÁI VIẾT HOA (Ví dụ: Hà Nội -> HAN, Hồ Chí Minh/Sài Gòn -> SGN, Đà Nẵng -> DAD, Phú Quốc -> PQC). Không được trả về tên thành phố.
2. Ngày tháng (departureDate, returnDate) PHẢI theo định dạng YYYY-MM-DD dựa vào thời gian hiện tại.
3. Nếu thông tin không có trong câu, bắt buộc trả về null.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    ("human", "{message}")
])

extraction_chain = prompt | structured_llm

def extract_intent_and_slots(message: str) -> IntentExtractionResult:
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        result = extraction_chain.invoke({
            "message": message,
            "current_time": current_time
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