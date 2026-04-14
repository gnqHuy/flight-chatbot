import os, json, logging
from datetime import datetime
from sqlmodel import Session, select, or_, and_
from models.airline import Airline
from models.flight_promotion import FlightPromotion
from services.rag.vector_store import get_embeddings
from utils.database import engine

logger = logging.getLogger(__name__)
PROMO_TAG = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"


def retrieve_promo(query: str, target_airline_code: str | None = None) -> str:
    embeddings   = get_embeddings()
    query_vector = embeddings.embed_query(query)
    today        = datetime.now().date()

    with Session(engine) as session:
        stmt = select(FlightPromotion)
        if target_airline_code:
            airline = session.exec(
                select(Airline).where(Airline.code == target_airline_code.upper())
            ).first()
            if airline:
                stmt = stmt.where(FlightPromotion.airline_id == airline.id)
        stmt = stmt.where(
            or_(FlightPromotion.booking_end_date == None,
                FlightPromotion.booking_end_date >= today)
        ).order_by(FlightPromotion.embedding.cosine_distance(query_vector)).limit(3)
        docs = list(session.exec(stmt).all())

    if not docs: return ""

    result = f"{PROMO_TAG}\n- CÂU HỎI: '{query}'\n- NGÀY: {today.strftime('%Y-%m-%d')}\n"
    for idx, p in enumerate(docs, 1):
        b_end = p.booking_end_date.strftime("%d/%m/%Y") if p.booking_end_date else "Không giới hạn"
        result += f"\n▶ {idx}. {p.promo_name}\n"
        result += f"   - Mã: {p.promo_code or 'Tự động áp dụng'}\n"
        result += f"   - Hạn: {b_end}\n"
        result += f"   - Chi tiết: {p.description}\n"
        result += f"   - Điều kiện: {p.conditions}\n"
        result += f"   - [Link]: {p.url}\n"
    return result.strip()


def inject_promos(search_id: str, redis_host: str = "localhost", redis_port: int = 6379) -> str:
    import redis as redis_lib
    r = redis_lib.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    raw = r.get(search_id)
    if not raw: return ""

    flights = json.loads(raw)
    if not flights: return ""

    found_codes = {str(a).upper() for f in flights[:5] for a in f.get("airlines", [])}
    if not found_codes: return ""

    with Session(engine) as session:
        airlines = session.exec(
            select(Airline).where(Airline.code.in_(list(found_codes)))
        ).all()
        promo_msgs = []
        for airline in airlines:
            promos = session.exec(
                select(FlightPromotion)
                .where(FlightPromotion.airline_id == airline.id)    # FIX [18]: tách .where()
                .where(or_(FlightPromotion.booking_end_date == None,
                           FlightPromotion.booking_end_date >= datetime.now().date()))
                .limit(2)
            ).all()
            for p in promos:
                code_str = f" (Mã: {p.promo_code})" if p.promo_code else " (Áp dụng trực tiếp)"
                promo_msgs.append(f"  + Hãng {airline.code}: {p.promo_name}{code_str}. ĐK: {p.conditions}")

    if not promo_msgs: return ""
    return (
        "[THÔNG TIN GỢI Ý KHÁCH HÀNG VỀ KHUYẾN MÃI]\n"
        "Các hãng bay trong danh sách ĐANG CÓ KHUYẾN MÃI:\n"
        + "\n".join(promo_msgs)
        + "\n\n[YÊU CẦU CHO AI]: Khéo léo lồng ghép 1-2 khuyến mãi phù hợp vào câu trả lời."
    )