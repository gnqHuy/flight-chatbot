from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from app.core.enums import AnalysisCriteria, ChatIntent, SortPreference, TravelClass  

class FlightParameters(BaseModel):
    origin: Optional[str] = Field(None, description="Mã IATA điểm ĐI. Dấu hiệu: Thường đứng sau chữ 'từ', 'khởi hành tại'. NẾU KHÁCH NÓI 'đi Sài Gòn', 'đến Hà Nội' thì đó KHÔNG PHẢI origin. Bỏ qua nếu không rõ.")
    destination: Optional[str] = Field(None, description="Mã IATA điểm ĐẾN. Dấu hiệu: Thường đứng sau chữ 'đi', 'đến', 'vào', 'bay ra'. VD: 'đi công tác Sài Gòn' -> destination='SGN'.")
    
    departureDate: Optional[str] = Field(None, description="Ngày đi (YYYY-MM-DD).")
    returnDate: Optional[str] = Field(None, description="Ngày về (YYYY-MM-DD).")
    is_roundtrip: bool = Field(
        False, 
        description="Đặt là True nếu khách nhắc đến 'khứ hồi', 'bay về', 'đi và về'. Mặc định là False."
    )

    adults: int = Field(1, description="Số lượng người lớn (trên 12 tuổi).")
    children: int = Field(0, description="Số lượng trẻ em (2-12 tuổi).")
    infants: int = Field(0, description="Số lượng trẻ sơ sinh (dưới 2 tuổi).")
    pax_confirmed: bool = Field(
        True, 
        description=(
            "Đặt là False nếu khách nhắc đến 'trẻ em', 'con nhỏ' nhưng KHÔNG nói rõ tuổi hoặc năm sinh. "
            "Đặt là True nếu khách đã nói rõ tuổi (VD: 'bé 3 tuổi', 'con chị 5 tuổi') hoặc chỉ có người lớn."
        )
    )

    includedAirlines: Optional[List[str]] = Field(
        default=None, 
        description=(
            "CHỈ DÙNG KHI TÌM KIẾM HOẶC LỌC VÉ. "
            "Dùng khi khách KHẲNG ĐỊNH, YÊU CẦU hoặc CHỈ ĐỊNH rõ hãng muốn đi. "
            "Hỗ trợ: VN (Vietnam Airlines), VJ (VietJet Air), QH (Bamboo Airways). "
            "VD: 'Chỉ tìm vé VN', 'Sếp thích bay Vietnam Airlines' -> Trả về ['VN']. "
            "TUYỆT ĐỐI KHÔNG DÙNG biến này nếu khách nói câu phủ định (như 'tránh', 'không đi'). "
            "KHÔNG điền vào đây nếu Intent là ANALYZE_FLIGHTS (hãy điền vào analysis_targets)."
        )
    )
    
    excludedAirlines: Optional[List[str]] = Field(
        default=None,
        description=(
            "CHỈ DÙNG KHI TÌM KIẾM HOẶC LỌC VÉ. "
            "Dùng khi khách có ý PHỦ ĐỊNH, KHÔNG MUỐN hoặc TRÁNH một hãng nào đó. "
            "VD: 'Tránh VJ ra nhé', 'Sếp không bay Vietjet đâu' -> Trả về chính xác mã hãng bị ghét ['VJ']. "
            "TUYỆT ĐỐI KHÔNG tự suy luận hay làm toán trừ danh sách (không được tự đổi thành include VN, QH). "
            "Cứ thấy khách chê/ghét hãng nào là ném thẳng mã hãng đó vào biến này. "
            "KHÔNG điền vào đây nếu Intent là ANALYZE_FLIGHTS."
        )
    )

    cleared_filters: Optional[List[str]] = Field(
        default=None,
        description=(
            "QUAN TRỌNG: Danh sách các 'TÊN BIẾN' cần XÓA BỎ khỏi State khi khách đổi ý (Undo/Quay xe). "
            "VD 1: Khách từng chê 'tránh VJ', nay đổi ý 'thôi cứ tìm cả Vietjet đi xem sao' (tức là xóa lệnh cấm) -> Trả về ['excludedAirlines']. "
            "VD 2: Khách từng chốt 'chỉ bay VN', nay nói 'đi hãng nào cũng được' (xóa mọi bộ lọc) -> Trả về ['includedAirlines', 'excludedAirlines']. "
            "VD 3: Khách nói 'Bỏ lọc giá đi' -> Trả về ['maxPrice']. "
            "TUYỆT ĐỐI KHÔNG ghi giá trị vào includedAirlines/excludedAirlines nếu đã điền tên chúng vào biến cleared_filters này."
        )
    )

    nonStop: Optional[bool] = Field(None, description="True nếu chỉ muốn bay thẳng, không quá cảnh.")
    travelClass: Optional[TravelClass] = Field(None, description="Hạng ghế.")
    maxPrice: Optional[int] = Field(None, description="Ngân sách tối đa.")
    sort_preference: Optional[SortPreference] = Field(
        SortPreference.PRICE, 
        description=(
            "Tiêu chí ưu tiên sắp xếp danh sách: "
            "'price' (khi khách muốn rẻ), "
            "'duration' (khi khách muốn bay nhanh), "
            "'departure_time' (khi khách muốn bay sớm)."
        )
    )
    start_hour: Optional[int] = Field(None, description="Giờ đi: Sáng=6, Trưa=11, Chiều=13, Tối=18.")
    end_hour: Optional[int] = Field(None, description="Giờ đến: Sáng=11, Trưa=13, Chiều=18, Tối=23.")
    
    analysis_targets: Optional[List[str]] = Field(
        default=None, 
        description=(
            "Mã chuyến bay (VD: VN123) hoặc Mã hãng bay (VD: VN, VJ, QH) mà khách muốn SO SÁNH hoặc PHÂN TÍCH. "
            "LƯU Ý SỐNG CÒN: Nếu khách nói 'So sánh VN và QH', BẮT BUỘC điền ['VN', 'QH'] vào ĐÂY. "
            "KHÔNG ĐƯỢC điền vào biến includedAirlines."
        )
    )

    criteria: List[AnalysisCriteria] = Field(
        default=[AnalysisCriteria.PRICE, AnalysisCriteria.TIME],
        description="Các khía cạnh khách muốn tập trung so sánh. Nếu khách không nói rõ, mặc định so sánh giá và giờ giấc."
    )

class Task(BaseModel):
    intent: ChatIntent = Field(..., description="Phân loại ý định.")
    parameters: Optional[FlightParameters] = Field(None, description="Tham số chuyến bay (nếu có).")
    query_context: Optional[str] = Field(None, description="Câu hỏi RAG.")

class ExtractionOutput(BaseModel):
    tasks: List[Task] = Field(..., description="Danh sách tác vụ.")