from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass  

class FlightParameters(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI. NẾU KHÁCH NÓI 'đi Sài Gòn' thì đó là destination, KHÔNG PHẢI origin.")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN. VD: 'bay vào Đà Nẵng' -> DAD.")
    
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    is_roundtrip: bool = Field(False, description="True nếu là vé khứ hồi.")

    adults: int = Field(1, description="Số lượng người lớn.")
    children: int = Field(0, description="Số lượng trẻ em.")
    infants: int = Field(0, description="Số lượng trẻ sơ sinh.")
    pax_confirmed: bool = Field(True, description="False nếu chưa rõ số tuổi trẻ em.")

    includedAirlines: Optional[List[str]] = Field(
        default=None, 
        description=(
            "CHỈ DÙNG khi khách muốn TÌM/MUA vé (intent: search_flight). "
            "VD: 'Tìm vé Vietjet' -> ['VJ']. "
            "KHÔNG dùng cho hỏi quy định/khuyến mãi."
        )
    )
    
    excludedAirlines: Optional[List[str]] = Field(
        default=None,
        description="Mã hãng khách muốn tránh (intent: search_flight/filter_sort)."
    )

    cleared_filters: Optional[List[str]] = Field(
        default=None,
        description="Các biến cần xóa khỏi State."
    )

    nonStop: Optional[bool] = Field(None, description="True nếu chỉ bay thẳng.")
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế.")
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa.")
    sort_preference: Optional[SortPreference] = Field(
        SortPreference.PRICE, 
        description="Tiêu chí sắp xếp."
    )
    start_hour: Optional[int] = Field(None, description="Giờ đi.")
    end_hour: Optional[int] = Field(None, description="Giờ đến.")
        
    target_flight: Optional[List[str]] = Field(
        default=None, 
        description="Mã chuyến bay cụ thể (VN208) để phân tích. KHÔNG điền mã hãng vào đây."
    )

    target_airline: Optional[List[str]] = Field(
        default=None, 
        description=(
            "BẮT BUỘC ĐIỀN khi khách nhắc tên hãng trong các tác vụ: Tra cứu quy định (general_question), "
            "Khuyến mãi (promo_search), So sánh (analyze_flights). "
            "Đây là 'Airline Filter' cho RAG. "
            "VD: 'Bà bầu đi Vietjet có sao không?' -> intent='general_question', target_airline=['VJ']."
        )
    )
    
    criteria: List[AnalysisCriteria] = Field(
        default=[AnalysisCriteria.PRICE, AnalysisCriteria.TIME],
        description="Tiêu chí so sánh."
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    
    parameters: Optional[FlightParameters] = Field(
        None, 
        description=(
            "Tham số chi tiết. NẾU khách nhắc tên hãng (Vietjet, VN Airlines...) trong câu hỏi quy định/khuyến mãi, "
            "BẮT BUỘC trích xuất mã hãng vào parameters.target_airline thay vì bỏ qua."
        )
    )
    
    query_context: Optional[str] = Field(
        None, 
        description="Nội dung cốt lõi để tra cứu (VD: 'phụ nữ mang thai 32 tuần', 'hành lý xách tay')."
    )

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ.")