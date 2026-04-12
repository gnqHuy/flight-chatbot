from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass

class ArrayAction(BaseModel):
    field_name: Literal["preferred_airlines"] = Field(..., description="Tên mảng cần thao tác (chỉ hỗ trợ preferred_airlines).")
    action: Literal["ADD", "REMOVE"] = Field(..., description="Thêm (ADD) hoặc Xóa (REMOVE).")
    values: List[str] = Field(..., description="Mã hãng bay. VD: ['VJ', 'VN']")

class SearchFiltersParams(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    roundTrip: Optional[bool] = Field(None, description="True nếu là vé khứ hồi.")
    
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế (ECONOMY, BUSINESS).")
    
    adults: Optional[int] = Field(None, ge=1, description="Số lượng người lớn.")
    children: Optional[int] = Field(None, description="Số lượng trẻ em (2-11 tuổi).")
    infants: Optional[int] = Field(None, description="Số lượng em bé / trẻ sơ sinh (dưới 2 tuổi).")
    need_age_confirmation: Optional[bool] = Field(None, description="True NẾU có trẻ em mà KHÔNG rõ tuổi cụ thể. False hoặc Null nếu đã rõ tuổi.")
    preferred_airlines: Optional[List[str]] = Field(None, description="Mã hãng bay khách CHỈ ĐỊNH lọc (VD: ['VN']).")
    maxPrice: Optional[int] = Field(None, description="Mức giá tối đa (VNĐ).")
    nonStop: Optional[bool] = Field(None, description="True nếu tìm chuyến bay thẳng.")
    start_hour: Optional[int] = Field(None, description="Giờ bay sớm nhất (0-23).")
    end_hour: Optional[int] = Field(None, description="Giờ bay muộn nhất (0-23).")
    
    sort_preference: Optional[SortPreference] = Field(
        None, description="Tiêu chí sắp xếp: price_asc, price_desc, departure_time..."
    )
    clear_fields: Optional[List[str]] = Field(None, description="Các biến muốn HỦY. VD: ['maxPrice']")
    array_actions: Optional[List[ArrayAction]] = Field(None, description="THÊM/BỚT hãng bay.")

class ActionTargetsParams(BaseModel):
    compare_flights: Optional[List[str]] = Field(
        default=None, 
        description="MÃ CHUYẾN BAY (VD: VN123). ĐỂ NULL nếu khách không đọc mã số cụ thể. KHÔNG TỰ BỊA MÃ."
    )
    compare_airlines: Optional[List[str]] = Field(
        default=None, description="Mã hãng bay cần so sánh (VD: ['VN', 'VJ'])."
    )
    analysis_criteria: Optional[List[AnalysisCriteria]] = Field(
        default=None, description="Chủ đề hỏi (hành lý, chỗ ngồi...)."
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    
    search_filters: Optional[SearchFiltersParams] = Field(None, description="Điều kiện TÌM KIẾM, LỌC & SẮP XẾP.")
    action_targets: Optional[ActionTargetsParams] = Field(None, description="Đối tượng để SO SÁNH (Mã chuyến, Mã hãng).")
    query_context: Optional[str] = Field(None, description="Trích nguyên văn câu nói của khách hàng.")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ bóc tách.")