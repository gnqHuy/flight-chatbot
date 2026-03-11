from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import ChatIntent, TravelClass  

class FlightParameters(BaseModel):
    origin: str = Field(description="Mã IATA sân bay đi (VD: HAN, SGN)")
    destination: str = Field(description="Mã IATA sân bay đến")
    departureDate: str = Field(description="Ngày đi định dạng YYYY-MM-DD")
    returnDate: Optional[str] = Field(None, description="Ngày về định dạng YYYY-MM-DD")
    adults: int = Field(1, description="Số lượng người lớn")
    includedAirlines: Optional[List[str]] = Field(None, description="Danh sách mã IATA hãng bay KHÁCH MUỐN ĐI (VD: ['VN', 'VJ'])")
    excludedAirlines: Optional[List[str]] = Field(None, description="Danh sách hãng KHÔNG MUỐN ĐI")
    nonStop: Optional[bool] = Field(False, description="True nếu khách chỉ muốn bay thẳng")
    travelClass: Optional[TravelClass] = Field(None)
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa của khách")
    comparison_target: Optional[List[str]] = Field(
        None, description="Danh sách các đối tượng cần so sánh. Ví dụ: ['VN', 'VJ'] nếu khách so sánh 2 hãng."
    )
    sort_preference: Optional[Literal["price", "duration", "departure_time"]] = Field(
        None, 
        description="Tiêu chí khách muốn ưu tiên so sánh: 'price' (rẻ nhất), 'duration' (thời gian bay ngắn nhất/nhanh nhất), 'departure_time' (bay sớm nhất)."
    )

    start_hour: Optional[int] = Field(
        None, 
        description=(
            "Giờ bắt đầu mong muốn (0-23). "
            "QUY TẮC QUY ĐỔI: "
            "- 'Sáng' (Morning) -> start_hour=6. "
            "- 'Trưa' (Noon) -> start_hour=11. "
            "- 'Chiều' (Afternoon) -> start_hour=13. "
            "- 'Tối/Đêm' (Evening/Night) -> start_hour=18. "
            "- Nếu nói giờ cụ thể (VD: 'khoảng 15h') -> start_hour=14 (trừ đi 1 tiếng). "
            "- Bỏ lọc giờ -> trả về 'CLEAR'."
        )
    )
    end_hour: Optional[int] = Field(
        None, 
        description=(
            "Giờ kết thúc mong muốn (0-23). "
            "QUY TẮC QUY ĐỔI: "
            "- 'Sáng' -> end_hour=11. "
            "- 'Trưa' -> end_hour=13. "
            "- 'Chiều' -> end_hour=18. "
            "- 'Tối/Đêm' -> end_hour=23. "
            "- Nếu nói giờ cụ thể (VD: 'khoảng 15h') -> end_hour=16 (cộng thêm 1 tiếng). "
            "- Bỏ lọc giờ -> trả về 'CLEAR'."
        )
    )

    target_flights: Optional[List[str]] = Field(
        None, 
        description=(
            "Danh sách MÃ CHUYẾN BAY CỤ THỂ khách muốn phân tích hoặc so sánh. "
            "Ví dụ: Khách nói 'so sánh VN157 và VJ501' -> ['VN157', 'VJ501']. "
            "Khách nói 'chuyến VJ503 có hành lý chưa' -> ['VJ503']. "
            "Bỏ lọc -> trả về ['CLEAR']."
        )
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại chính xác ý định. Nếu chỉ hỏi chính sách mà không tìm vé, KHÔNG ĐƯỢC tạo task search_flight.")
    parameters: Optional[FlightParameters] = Field(
        default=None, 
        description="Chỉ điền khi intent liên quan đến tìm vé"
    )
    query_context: Optional[str] = Field(
        default=None, 
        description="Nội dung câu hỏi gốc của người dùng dùng cho RAG (VD: 'Bầu 30 tuần bay được không?')."
    )

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(
        ..., 
        description="Danh sách các tác vụ. Lưu ý: KHÔNG tự tạo thêm các task tìm kiếm nếu người dùng chỉ hỏi thông tin chung."
    )

    target_flights: Optional[List[str]] = Field(
        None, description="Danh sách mã chuyến bay khách muốn lưu, phân tích hoặc so sánh. VD: ['VN123', 'VJ501']"
    )