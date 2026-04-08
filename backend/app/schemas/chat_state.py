from pydantic import BaseModel, Field
from typing import Literal, Optional, List, TypedDict
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass

class ArrayAction(BaseModel):
    """Công cụ chuyên trị để thêm/bớt phần tử trong mảng (List)"""
    field_name: Literal["preferred_airlines"] = Field(..., description="Tên của mảng cần thao tác.")
    action: Literal["ADD", "REMOVE"] = Field(..., description="ADD (thêm vào) hoặc REMOVE (bỏ đi).")
    values: List[str] = Field(..., description="Giá trị cần thao tác. VD: Mã hãng bay ['VJ']")

class SearchFiltersParams(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI (VD: HAN).")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN (VD: SGN).")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    roundTrip: Optional[bool] = Field(None, description="True nếu khách nhắc đến vé khứ hồi.")
    
    travelClass: Optional[TravelClass] = Field(
        None, 
        description="Hạng ghế khách yêu cầu (ECONOMY, BUSINESS...)."
    )
    
    adults: Optional[int] = Field(None, ge=1, description="Số lượng người lớn.")
    children: Optional[int] = Field(None, description="Số lượng trẻ em (2-11 tuổi).")
    infants: Optional[int] = Field(None, description="Số lượng em bé (dưới 2 tuổi).")
    need_age_confirmation: Optional[bool] = Field(None, description="Đánh dấu TRUE nếu khách nói có trẻ em nhưng không báo tuổi.")
    
    preferred_airlines: Optional[List[str]] = Field(
        default=None, 
        description="Mã hãng bay khách MUỐN CHỌN MỚI (VD: ['VN', 'VJ']). Chỉ dùng khi khách chọn mới hoàn toàn."
    )
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa (VNĐ).")
    nonStop: Optional[bool] = Field(None, description="True nếu chỉ muốn bay thẳng.")
    start_hour: Optional[int] = Field(None, description="Giờ bay sớm nhất (0-23).")
    end_hour: Optional[int] = Field(None, description="Giờ bay muộn nhất (0-23).")
    
    sort_preference: Optional[SortPreference] = Field(
        None, 
        description=(
            "Tiêu chí sắp xếp. CHỈ ĐƯỢC CHỌN: "
            "'price_asc' (giá tăng/rẻ nhất), "
            "'price_desc' (giá giảm/đắt nhất), "
            "'departure_time' (giờ cất cánh sớm), "
            "'arrival_time' (giờ hạ cánh)."
        )
    )

    reset_search: Optional[bool] = Field(
        default=False, 
        description="Đánh dấu True BẮT BUỘC nếu khách nói 'Tìm vé khác', 'Làm lại từ đầu'. Sẽ xóa sạch mọi thông số trước đó."
    )
    
    clear_fields: Optional[List[str]] = Field(
        default=None, 
        description="TÊN CÁC BIẾN khách muốn HỦY BỎ. VD: Khách nói 'Bỏ sắp xếp, bỏ hạng ghế' -> ['sort_preference', 'travelClass']."
    )
    
    array_actions: Optional[List[ArrayAction]] = Field(
        default=None,
        description="Dùng khi khách muốn THÊM/BỚT 1 hãng bay khỏi danh sách ĐANG CÓ. VD: 'Thôi bỏ VJ đi' -> [{'field_name': 'preferred_airlines', 'action': 'REMOVE', 'values': ['VJ']}]"
    )

class ActionTargetsParams(BaseModel):
    compare_flights: Optional[List[str]] = Field(default=None, description="Chứa ID DUY NHẤT của vé khách muốn hỏi/phân tích. (VD: Khách nói '[ID: 2]' -> Điền ['2']). TUYỆT ĐỐI KHÔNG điền mã chuyến bay (như VN100) hay mã hãng vào đây.")
    compare_airlines: Optional[List[str]] = Field(default=None, description="Mã hãng bay khách muốn ĐEM LÊN BÀN CÂN SO SÁNH / HỎI CHÍNH SÁCH.")
    analysis_criteria: Optional[List[AnalysisCriteria]] = Field(default=None, description="Các khía cạnh khách muốn phân tích/đánh giá.")

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    search_filters: Optional[SearchFiltersParams] = Field(None, description="Các tham số lọc hiển thị dài hạn.")
    action_targets: Optional[ActionTargetsParams] = Field(None, description="Các tham số mục tiêu phân tích ngắn hạn.")
    query_context: Optional[str] = Field(None, description="Nội dung cần RAG.")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ cần xử lý.")