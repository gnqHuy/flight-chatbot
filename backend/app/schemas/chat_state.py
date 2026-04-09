from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass

class ArrayAction(BaseModel):
    field_name: Literal["preferred_airlines"] = Field(..., description="Tên mảng cần thao tác (chỉ hỗ trợ preferred_airlines).")
    action: Literal["ADD", "REMOVE"] = Field(..., description="Thêm (ADD) hoặc Xóa (REMOVE).")
    values: List[str] = Field(..., description="Mã hãng bay. VD: ['VJ']")

class SearchFiltersParams(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    roundTrip: Optional[bool] = Field(None, description="True nếu là vé khứ hồi.")
    
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế (ECONOMY, BUSINESS).")
    
    adults: Optional[int] = Field(None, ge=1, description="Số lượng người lớn.")
    children: Optional[int] = Field(None, description="Số lượng trẻ em (2-11 tuổi).")
    infants: Optional[int] = Field(None, description="Số lượng em bé (dưới 2 tuổi).")
    need_age_confirmation: Optional[bool] = Field(None, description="True nếu khách có trẻ em nhưng chưa rõ tuổi.")
    
    preferred_airlines: Optional[List[str]] = Field(None, description="Mã hãng bay khách CHỈ ĐỊNH lọc (VD: ['VN']).")
    maxPrice: Optional[int] = Field(None, description="Mức giá tối đa (VNĐ) khách yêu cầu.")
    nonStop: Optional[bool] = Field(None, description="True nếu chỉ tìm chuyến bay thẳng.")
    start_hour: Optional[int] = Field(None, description="Giờ bay sớm nhất (0-23).")
    end_hour: Optional[int] = Field(None, description="Giờ bay muộn nhất (0-23).")
    
    sort_preference: Optional[SortPreference] = Field(
        None, 
        description="Tiêu chí sắp xếp vé sau khi lọc: GIÁ (price), THỜI GIAN BAY (duration), GIỜ BAY (departure_time)."
    )

    reset_search: Optional[bool] = Field(None, description="True nếu khách muốn TÌM LẠI TỪ ĐẦU / Xóa sạch bộ lọc cũ.")
    clear_fields: Optional[List[str]] = Field(None, description="Tên các biến muốn HỦY BỎ. VD: Bỏ lọc giá -> ['maxPrice'].")
    array_actions: Optional[List[ArrayAction]] = Field(None, description="Dùng để THÊM/BỚT hãng bay. VD: Bỏ VJ -> action: REMOVE, values: ['VJ']")

class ActionTargetsParams(BaseModel):
    compare_flights: Optional[List[str]] = Field(
        default=None, 
        description="Mã chuyến bay CỤ THỂ khách muốn hỏi/so sánh (VD: ['VN208']). TUYỆT ĐỐI không điền chữ chung chung vào đây."
    )
    compare_airlines: Optional[List[str]] = Field(
        default=None, 
        description="Mã hãng bay khách muốn hỏi chính sách/so sánh (VD: ['VN', 'VJ'])."
    )
    analysis_criteria: Optional[List[AnalysisCriteria]] = Field(
        default=None, 
        description="Chủ đề khách muốn hỏi (hành lý, chỗ ngồi...)."
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    
    search_filters: Optional[SearchFiltersParams] = Field(
        None, 
        description="CHỨA ĐIỀU KIỆN TÌM KIẾM, LỌC & SẮP XẾP. VD: Giá tiền (maxPrice), ngày tháng, sắp xếp (sort_preference), hãng bay."
    )
    
    action_targets: Optional[ActionTargetsParams] = Field(
        None, 
        description="CHỈ CHỨA ĐỐI TƯỢNG ĐỂ SO SÁNH (Mã chuyến bay, Mã hãng bay). TUYỆT ĐỐI KHÔNG điền giá tiền hay bộ lọc vào giỏ này."
    )
    
    query_context: Optional[str] = Field(
        None, 
        description="Trích xuất NGUYÊN VĂN đoạn chat của khách hàng tương ứng với tác vụ này. BẮT BUỘC giữ nguyên từng chữ, từng dấu câu. TUYỆT ĐỐI KHÔNG tóm tắt, diễn đạt lại hay sửa lỗi chính tả."
    )

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ bóc tách.")