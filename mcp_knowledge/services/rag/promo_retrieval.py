# mcp_knowledge/services/rag/promo_retrieval.py
import os, json, logging
from sqlmodel import Session, select, or_
from models.airline import Airline
from models.flight_promotion import FlightPromotion
from services.rag.vector_store import get_embeddings
from utils.database import engine
from utils.time_utils import get_current_time

logger   = logging.getLogger(__name__)
PROMO_TAG = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"


def retrieve_promo(query: str, target_airline_code: str | None = None) -> str:
    embeddings   = get_embeddings()
    query_vector = embeddings.embed_query(query)
    today        = get_current_time().date()

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
