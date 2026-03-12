from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import ChatIntent, TravelClass  

class FlightParameters(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI. Dấu hiệu: Thường đứng sau chữ 'từ', 'khởi hành tại'. NẾU KHÁCH NÓI 'đi Sài Gòn', 'đến Hà Nội' thì đó KHÔNG PHẢI origin. Bỏ qua nếu không rõ.")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN. Dấu hiệu: Thường đứng sau chữ 'đi', 'đến', 'vào', 'bay ra'. VD: 'đi công tác Sài Gòn' -> destination='SGN'.")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    adults: Optional[int] = Field(None, description="Số lượng hành khách (người lớn).")
    includedAirlines: Optional[List[str]] = Field(None, description="Mã IATA hãng bay muốn đi (VD: ['VN', 'VJ']).")
    excludedAirlines: Optional[List[str]] = Field(None, description="Mã IATA hãng bay không muốn đi.")
    nonStop: Optional[bool] = Field(None, description="True nếu chỉ muốn bay thẳng, không quá cảnh.")
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế.")
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa.")
    sort_preference: Optional[Literal["price", "duration", "departure_time"]] = Field(None, description="Tiêu chí ưu tiên: price, duration, departure_time.")
    start_hour: Optional[int] = Field(None, description="Giờ đi: Sáng=6, Trưa=11, Chiều=13, Tối=18.")
    end_hour: Optional[int] = Field(None, description="Giờ đến: Sáng=11, Trưa=13, Chiều=18, Tối=23.")
    
    cleared_filters: Optional[List[str]] = Field(
        default_factory=list,
        description="Danh sách các TÊN BIẾN mà khách yêu cầu gỡ bỏ. VD: khách nói 'hủy chiều về' -> ['returnDate']. 'Bỏ lọc hãng' -> ['includedAirlines']."
    )

    target_flights: Optional[List[str]] = Field(
        default=None, 
        description=(
            "Danh sách các MÃ CHUYẾN BAY (Flight Number) CỤ THỂ mà khách muốn xem chi tiết hoặc so sánh. "
            "Dấu hiệu: Các mã có cả chữ và số (VD: VN123, VJ501). "
            "Ví dụ: Khách nói 'So sánh chuyến VN157 và VJ501' -> ['VN157', 'VJ501']. "
            "KHÔNG dùng biến này để chứa mã Hãng bay (như VN, VJ)."
        )
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    parameters: Optional[FlightParameters] = Field(None, description="Tham số chuyến bay (nếu có).")
    query_context: Optional[str] = Field(None, description="Câu hỏi RAG.")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ.")