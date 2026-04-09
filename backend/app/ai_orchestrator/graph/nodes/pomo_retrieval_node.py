import os
from datetime import datetime
from sqlmodel import Session, select, or_

from app.ai_orchestrator.graph.state import ChatState
from app.database.database import engine
from app.database.models.airline import Airline
from app.database.models.flight_promotion import FlightPromotion
from app.utils.helpers import consume_task
from app.core.constants import ContextTag
from app.ai_orchestrator.rag.vector_store import shared_embeddings

def promo_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM KHUYẾN MÃI (HYBRID RAG + SQL) ---")
    
    search_filters = state.get("search_filters", {})
    action_targets = state.get("action_targets", {})
    user_message = state.get("user_message", "")
    
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "promo_search") 
    
    query = user_message 
    
    target_airline_list = action_targets.get("compare_airlines") or search_filters.get("preferred_airlines") or []
    target_airline_code = target_airline_list[0].upper() if target_airline_list else None

    docs = []
    
    try:
        query_vector = shared_embeddings.embed_query(query)
        
        with Session(engine) as session:
            stmt = select(FlightPromotion)
            
            if target_airline_code:
                airline_obj = session.exec(select(Airline).where(Airline.code == target_airline_code)).first()
                if airline_obj:
                    stmt = stmt.where(FlightPromotion.airline_id == airline_obj.id)
            
            today = datetime.now().date()
            stmt = stmt.where(
                or_(
                    FlightPromotion.booking_end_date == None,
                    FlightPromotion.booking_end_date >= today
                )
            )
            
            stmt = stmt.order_by(FlightPromotion.embedding.cosine_distance(query_vector)).limit(3)
            
            docs = session.exec(stmt).all()
            
        if not docs:
            airline_msg = f" của hãng {target_airline_code}" if target_airline_code else ""
            return {
                "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Hiện tại không có chương trình khuyến mãi nào phù hợp{airline_msg}."],
                "tasks": remaining_tasks 
            }
        
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        result_string = (
            f"{ContextTag.PROMO_INFO}\n"
            f"--- KẾT QUẢ TRA CỨU KHUYẾN MÃI TƯƠNG ĐỒNG ---\n"
            f"- CÂU HỎI: '{query}'\n"
            f"- NGÀY HỆ THỐNG: {current_date_str}\n"
        )
        
        for idx, promo in enumerate(docs, 1):
            b_end = promo.booking_end_date.strftime("%d/%m/%Y") if promo.booking_end_date else "Không giới hạn"
            
            result_string += f"\n▶ {idx}. {promo.promo_name}\n"
            result_string += f"   - Mã code: {promo.promo_code or 'Tự động áp dụng'}\n"
            result_string += f"   - Hạn đặt: {b_end}\n"
            result_string += f"   - Nội dung: {promo.description}\n"
            result_string += f"   - Điều kiện: {promo.conditions}\n"
            result_string += f"   - [Link chi tiết]: {promo.url}\n"
                
        return {
            "node_results": [result_string.strip()], 
            "tasks": remaining_tasks 
        }
    
    except Exception as e:
        print(f"ERROR - Promo Hybrid RAG Node: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống tra cứu khuyến mãi đang gặp sự cố kết nối."],
            "tasks": remaining_tasks
        }