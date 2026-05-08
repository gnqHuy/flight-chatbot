import os
from datetime import datetime

SUPPORTED_AIRLINES = ["VN", "VJ", "QH"]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL   = os.getenv("DATABASE_URL", "")

class ContextTag:
    PROMO_INFO    = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"
    POLICY_INFO   = "[KIẾN THỨC NGHIỆP VỤ CHÍNH SÁCH]"
    SYS_NOT_FOUND = "[KHÔNG TÌM THẤY DỮ LIỆU]"
    SYS_ERROR     = "[TRỤC TRẶC HỆ THỐNG]"

COST_PER_TOKEN = 0.0000003

def get_current_time():
    from datetime import datetime
    import os
    raw = os.getenv("TEST_DATE", "").strip()
    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            pass
    return datetime.now()

def get_current_time_str():
    return get_current_time().strftime("%Y-%m-%d %H:%M")
