from datetime import datetime

SUPPORTED_AIRLINES   = ["VN", "VJ", "QH"]
CURRENT_TIME         = datetime.now()
CURRENT_TIME_STR     = CURRENT_TIME.strftime("%Y-%m-%d %H:%M")

class ContextTag:
    PROMO_INFO    = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"
    POLICY_INFO   = "[KIẾN THỨC NGHIỆP VỤ CHÍNH SÁCH]"
    SYS_NOT_FOUND = "[KHÔNG TÌM THẤY DỮ LIỆU]"
    SYS_ERROR     = "[TRỤC TRẶC HỆ THỐNG]"