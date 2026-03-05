from pydantic import BaseModel, Field
from typing import Optional, List
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
    comparison_metric: Optional[str] = Field(
        None, description="Tiêu chí so sánh: 'price' (giá), 'duration' (thời gian bay), 'time' (giờ khởi hành), 'class' (hạng ghế), 'all' (tổng hợp)."
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