import json
from sqlmodel import Session, select
from app.database.database import engine
from app.repositories.flight_promotion_repo import FlightPromotionRepository
from app.database.models.airline import Airline
from app.services.redis_service import redis_service

def check_and_inject_promos(current_search_id: str) -> str:
    """
    Hàm lén kiểm tra xem các chuyến bay trong kết quả tìm kiếm có đang
    được áp dụng chương trình khuyến mãi nào không để mớm cho AI.
    """
    if not current_search_id or current_search_id == "CLEAR":
        return ""

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return ""

    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
    if not all_flights:
        return ""

    top_flights = all_flights[:5]
    
    found_airline_codes = set()
    for f in top_flights:
        for a in f.get('airlines', []):
            found_airline_codes.add(str(a).upper())

    if not found_airline_codes:
        return ""

    injected_text = ""
    
    with Session(engine) as session:
        repo = FlightPromotionRepository(session)
        
        statement = select(Airline).where(Airline.code.in_(list(found_airline_codes)))
        airlines = session.exec(statement).all()
        
        promo_messages = []
        for airline in airlines:
            promos = repo.get_active_promotions(target_airline_id=airline.id)
            
            for promo in promos[:2]:
                code_str = f" (Mã nhập lúc thanh toán: {promo.promo_code})" if promo.promo_code else " (Áp dụng trực tiếp)"
                promo_messages.append(f"  + Hãng {airline.code}: {promo.promo_name}{code_str}. Điều kiện: {promo.conditions}")
        
        if promo_messages:
            injected_text = (
                "[THÔNG TIN GỢI Ý KHÁCH HÀNG VỀ KHUYẾN MÃI]\n"
                "Hệ thống phát hiện các hãng bay trong danh sách Gợi ý phía trên ĐANG CÓ KHUYẾN MÃI CÒN HẠN:\n"
                + "\n".join(promo_messages) +
                "\n\n[YÊU CẦU CHO AI]: Hãy ĐÓNG VAI NHÂN VIÊN TƯ VẤN, khéo léo lồng ghép 1-2 khuyến mãi "
                "phù hợp nhất vào câu trả lời cuối cùng để kích thích khách hàng chốt vé. "
                "Đừng liệt kê như một cái máy, hãy nói kiểu: 'Bật mí cho bạn là hãng X đang có mã Y...'"
            )

    return injected_text