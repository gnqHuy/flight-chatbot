SUPPORTED_AIRLINES = ["VN", "VJ", "QH"]
SUPPORTED_AIRLINES_SET = set(SUPPORTED_AIRLINES)

AIRLINE_BASE_URLS = {
    "VN": "https://www.vietnamairlines.com",
    "VJ": "https://www.vietjetair.com",
    "QH": "https://www.bambooairways.com"
}

AIRLINE_PROMO_LIST_URLS = {
    "VN": "https://www.vietnamairlines.com/vn/vi/monthly-offers",
    "VJ": "https://www.vietjetair.com/vi/news/khuyen-mai-1697696806643/",
    "QH": "https://www.bambooairways.com/vn/vi/explore/offers"
}

MAX_FLIGHTS_RETURNED = 100

class ContextTag:
    """Quy chuẩn Thẻ (Tags) nhúng vào Context cho LLM đọc trong Final Node"""
    FLIGHT_FOUND = "[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]"
    FILTER_APPLIED = "[BỘ LỌC ĐƯỢC ÁP DỤNG]"
    FLIGHT_ANALYSIS = "[DỮ LIỆU SO SÁNH CHUYẾN BAY]"
    PROMO_INFO = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"
    POLICY_INFO = "[KIẾN THỨC NGHIỆP VỤ CHÍNH SÁCH]"
    
    USER_UPDATE = "[CẬP NHẬT TỪ KHÁCH HÀNG]"
    VALIDATION = "[THÔNG TIN ĐẶT VÉ CẦN KHÁCH KIỂM TRA LẠI]"
    SYS_NOT_FOUND = "[KHÔNG TÌM THẤY CHUYẾN BAY]"
    SYS_ERROR = "[TRỤC TRẶC HỆ THỐNG]"
    MISC_INFO = "[THÔNG TIN BỔ SUNG]"

class ValidationTag:
    """Quy chuẩn phân loại lỗi khi Validate (Dùng chung với LLMTag.VALIDATION_ISSUE)"""
    MISSING_INFO = "[THIẾU THÔNG TIN]"
    INVALID_AIRLINE = "[HÃNG KHÔNG HỖ TRỢ]"
    NEED_AGE = "[CẦN XÁC NHẬN TUỔI]"
    LIMIT_EXCEEDED = "[VƯỢT QUÁ SỐ KHÁCH]"
    INVALID_PAX = "[SỐ KHÁCH KHÔNG HỢP LỆ]"
    INVALID_DATE = "[NGÀY BAY KHÔNG HỢP LỆ]"