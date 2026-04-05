from pydantic import BaseModel, Field
from typing import Optional, List
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass

class FlightParameters(BaseModel):
    # ==========================================
    # 1. CORE PARAMS (Hành trình cốt lõi)
    # ==========================================
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI (VD: HAN).")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN (VD: SGN). Nếu khách nói 'đi Sài Gòn' -> SGN là destination.")
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    is_roundtrip: bool = Field(False, description="True nếu khách nhắc đến vé khứ hồi, chiều về.")
    travelClass: Optional[TravelClass] = Field(
        default=None, 
        description=(
            "Hạng ghế khách yêu cầu. "
            "Quy đổi: 'phổ thông' -> ECONOMY, 'thương gia' -> BUSINESS, 'hạng nhất' -> FIRST, 'phổ thông đặc biệt' -> PREMIUM_ECONOMY. "
            "Nếu khách không nhắc đến, bắt buộc để null."
        )
    )
    adults: int = Field(
        default=1, 
        ge=1,
        description="Số lượng người lớn (từ 12 tuổi). LUÔN MẶC ĐỊNH LÀ 1. Nếu khách không nhắc số lượng, TUYỆT ĐỐI GIỮ LÀ 1."
    )
    children: int = Field(0, description="Số lượng trẻ em (2-11 tuổi).")
    infants: int = Field(0, description="Số lượng em bé (dưới 2 tuổi).")
    
    need_age_confirmation: bool = Field(
        default=False, 
        description="Đánh dấu TRUE NGAY LẬP TỨC nếu khách nói mang theo 'trẻ em', 'trẻ nhỏ' NHƯNG KHÔNG CUNG CẤP TUỔI. (VD: 'bé 3 tuổi' -> FALSE)."
    )

    # ==========================================
    # 2. SOFT PARAMS (Bộ lọc Local Cache)
    # ==========================================
    target_airline: Optional[List[str]] = Field(
        default=None, 
        description=(
            "Mã hãng khách MUỐN ĐI hoặc MUỐN TRA CỨU quy định/khuyến mãi (VD: ['VN', 'VJ']). "
            "QUY TẮC CẬP NHẬT TRẠNG THÁI (Rất quan trọng): "
            "- Khách KHÔNG nhắc đến hãng: Trả về null (Không cập nhật). "
            "- Khách muốn THÊM hãng: Output mảng gồm hãng cũ + hãng mới. "
            "- Khách muốn LOẠI BỎ 1 hãng (VD đang có VN, VJ, khách nói 'Bỏ VN'): Output mảng chỉ còn hãng giữ lại (['VJ']). "
            "- Khách nói 'Hãng nào cũng được' / 'Xóa bộ lọc hãng': Output mảng rỗng []."
        )
    )
    
    excludedAirlines: Optional[List[str]] = Field(
        default=None,
        description="Mã hãng khách KIÊN QUYẾT TRÁNH, KHÔNG MUỐN ĐI (VD: 'Tránh Vietjet' -> ['VJ'])."
    )

    maxPrice: Optional[int] = Field(
        default=None, 
        description="Ngân sách/Giá tối đa (VNĐ). Nếu khách nói 'Hủy lọc giá', trả về 0."
    )
    
    nonStop: Optional[bool] = Field(None, description="True nếu chỉ muốn bay thẳng.")
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa.")
    start_hour: Optional[int] = Field(
        None, 
        description="Giờ bay sớm nhất (0-23). Quy đổi: 'Sáng' (06), 'Chiều' (12), 'Tối' (18)."
    )
    end_hour: Optional[int] = Field(
        None, 
        description="Giờ bay muộn nhất (0-23). Quy đổi: 'Sáng' (12), 'Chiều' (18), 'Tối' (23)."
    )
    
    sort_preference: Optional[SortPreference] = Field(
        default=None, 
        description=(
            "CHỈ DÙNG 1 TIÊU CHÍ DUY NHẤT để sắp xếp danh sách vé. "
            "Quy đổi: 'Rẻ nhất' / 'Giá tăng dần' -> price_asc, "
            "'Đắt nhất' / 'Giá giảm dần' -> price_desc, "
            "'Cất cánh sớm' -> departure_time, "
            "'Hạ cánh muộn' -> arrival_time."
        )
    )

    # ==========================================
    # 3. ANALYSIS PARAMS (Cho tác vụ So sánh/Phân tích)
    # ==========================================
    target_flight: Optional[List[str]] = Field(
        default=None, 
        description="Mã chuyến bay cụ thể (VD: VN208) để phân tích chi tiết. KHÔNG điền mã hãng vào đây."
    )
    
    criteria: Optional[List[AnalysisCriteria]] = Field(
        default=None,
        description=(
            "Các khía cạnh khách muốn BỘ PHẬN TƯ VẤN so sánh/đánh giá giữa các vé. "
            "Có thể chọn nhiều tiêu chí cùng lúc (VD: ['PRICE', 'BAGGAGE', 'LEGROOM']). "
            "Phân biệt: sort_preference dùng để XẾP HÀNG, criteria dùng để PHÂN TÍCH ƯU NHƯỢC ĐIỂM."
        )
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    parameters: Optional[FlightParameters] = Field(None, description="Các tham số đã trích xuất.")
    query_context: Optional[str] = Field(None, description="Nội dung cần RAG (quy định, chính sách, v.v.).")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ.")