# mcp_knowledge/services/data_pipeline/crawling/url_classifier.py
"""
Dùng LLM để:
1. Lọc URL không liên quan (category=GENERAL → bỏ)
2. Phân loại URL vào đúng category
"""
import json
import logging
from openai import OpenAI
from constants import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """Bạn là chuyên gia phân loại URL website hàng không.
Phân loại mỗi URL vào đúng category sau:
- baggage: hành lý
- check_in: thủ tục check-in
- fare_conditions: điều kiện vé, phí, hoàn/hủy/đổi vé
- special_services: dịch vụ đặc biệt (trẻ em, thú cưng, người khuyết tật, bà bầu)
- experience: trải nghiệm bay, hạng ghế, suất ăn, wifi
- airport: sân bay, phòng chờ, transit
- legal: điều kiện vận chuyển, bảo mật, cookie, điều khoản
- support: FAQ, hướng dẫn, liên hệ, help desk
- additional: dịch vụ bổ trợ (chọn ghế, suất ăn thêm, bảo hiểm, nâng hạng)
- promotion: khuyến mãi, ưu đãi, offers, tích điểm, dặm thưởng
- travel_info: thông tin du lịch, giấy tờ, visa, travel advice, travel guide, cẩm nang
- booking: hướng dẫn mua vé, thanh toán, quản lý đặt chỗ
- general: CHỈ loại các URL sau:
  * Tin tức công ty, tuyển dụng, nhà đầu tư, quan hệ báo chí
  * Đội tàu bay (our-fleet, our-fleets)
  * Trang tìm vé SEO (from-X-to-Y, ve-may-bay-di-X, ve-may-bay-tu-X)
  * Điểm đến du lịch thuần túy (explore/destinations/*)
  * Trang hành trình SEO (domestic-journeys/*, international-journeys/*)
  * Mã tracking (txtp25lv*, chuỗi chữ-số không có nghĩa)
  * Trang cá nhân (my-account, my-profile, my-profile-corp)
  * Sitemap, enewsletter, test-data, quảng cáo

Nguyên tắc: khi không chắc chắn thì KHÔNG loại — gán category gần nhất.
Trả về JSON object: {"url": "category"}
Không giải thích thêm."""


def classify_urls(urls: list[str]) -> dict[str, str]:
    if not urls:
        return {}
    
    logger.info(f"[classifier] Classifying {len(urls)} URLs...")
    url_list = "\n".join(urls)
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": url_list},
            ],
        )
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(raw)
        logger.info(f"[classifier] Done: {len(result)} URLs classified")
        return result
    except Exception as e:
        logger.error(f"[classifier] Error: {e}")
        return {u: "general" for u in urls}