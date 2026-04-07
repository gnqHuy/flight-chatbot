from pydantic import BaseModel, Field
from typing import Literal, Optional, List, TypedDict
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass

class SearchFiltersParams(BaseModel):
    """Giỏ 1: Chứa các bộ lọc cố định, quyết định danh sách vé hiển thị trên UI"""
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI (VD: HAN).")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN (VD: SGN).")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    roundTrip: bool = Field(False, description="True nếu khách nhắc đến vé khứ hồi.")
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế khách yêu cầu.")
    adults: int = Field(1, ge=1, description="Số lượng người lớn. MẶC ĐỊNH LÀ 1.")
    children: int = Field(0, description="Số lượng trẻ em (2-11 tuổi).")
    infants: int = Field(0, description="Số lượng em bé (dưới 2 tuổi).")
    need_age_confirmation: bool = Field(False, description="Đánh dấu TRUE nếu khách nói có trẻ em nhưng không báo tuổi.")
    
    preferred_airlines: Optional[List[str]] = Field(
        default=None, 
        description=(
            "Mã hãng bay khách MUỐN LỌC ĐỂ HIỂN THỊ CHUYẾN BAY (VD: ['VN', 'VJ']). "
            "Nếu khách nói 'Hủy lọc hãng', trả về mảng rỗng []."
        )
    )
    maxPrice: Optional[int] = Field(None, description="Ngân sách/Giá tối đa (VNĐ).")
    nonStop: Optional[bool] = Field(None, description="True nếu chỉ muốn bay thẳng.")
    start_hour: Optional[int] = Field(None, description="Giờ bay sớm nhất (0-23).")
    end_hour: Optional[int] = Field(None, description="Giờ bay muộn nhất (0-23).")
    sort_preference: Optional[SortPreference] = Field(None, description="Tiêu chí sắp xếp bảng vé (price_asc, departure_time...).")

class ActionTargetsParams(BaseModel):
    """Giỏ 2: Chứa các mục tiêu tạm thời phục vụ cho câu hỏi So Sánh/Phân Tích hiện tại"""
    compare_flights: Optional[List[str]] = Field(
        default=None, 
        description="Mã chuyến bay CỤ THỂ khách muốn hỏi/phân tích (VD: ['VN208', 'VJ103']). KHÔNG điền mã hãng bay vào đây."
    )
    compare_airlines: Optional[List[str]] = Field(
        default=None,
        description=(
            "Mã hãng bay khách muốn ĐEM LÊN BÀN CÂN SO SÁNH / HỎI CHÍNH SÁCH. "
            "(VD: Khách nói 'So sánh vé VJ và VN' -> ['VJ', 'VN']). "
            "Lưu ý: Biến này độc lập với preferred_airlines ở trên."
        )
    )
    analysis_criteria: Optional[List[AnalysisCriteria]] = Field(
        default=None,
        description="Các khía cạnh khách muốn phân tích/đánh giá (VD: ['PRICE', 'BAGGAGE', 'LEGROOM'])."
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    search_filters: Optional[SearchFiltersParams] = Field(None, description="Các tham số lọc hiển thị dài hạn.")
    action_targets: Optional[ActionTargetsParams] = Field(None, description="Các tham số mục tiêu phân tích ngắn hạn.")
    query_context: Optional[str] = Field(None, description="Nội dung cần RAG.")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ cần xử lý.")
