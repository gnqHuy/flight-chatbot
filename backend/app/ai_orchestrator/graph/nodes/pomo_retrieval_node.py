import os
from datetime import datetime
from sqlmodel import Session, select
from app.ai_orchestrator.graph.state import ChatState
from app.database.database import engine
from app.repositories.flight_promotion_repo import FlightPromotionRepository
from app.database.models.airline import Airline
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

def promo_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM KHUYẾN MÃI (SQL REPO) ---")
    
    search_filters = state.get("search_filters", {})
    action_targets = state.get("action_targets", {})
    
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "promo_search") 
    
    target_airline_list = []
    if action_targets.get("compare_airlines"):
        target_airline_list = action_targets.get("compare_airlines")
    elif search_filters.get("preferred_airlines"):
        target_airline_list = search_filters.get("preferred_airlines")
    
    target_airline_code = None
    if target_airline_list and isinstance(target_airline_list, list) and len(target_airline_list) > 0:
        target_airline_code = target_airline_list[0].upper()
    elif isinstance(target_airline_list, str):
        target_airline_code = target_airline_list.upper()
        
    docs = []
    
    try:
        with Session(engine) as session:
            repo = FlightPromotionRepository(session)
            target_airline_id = None
            
            if target_airline_code:
                airline_obj = session.exec(select(Airline).where(Airline.code == target_airline_code)).first()
                if airline_obj:
                    target_airline_id = airline_obj.id
            
            docs = repo.get_active_promotions(target_airline_id=target_airline_id)
            
        if not docs:
            airline_msg = f" của hãng {target_airline_code}" if target_airline_code else ""
            return {
                "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Hiện tại không có chương trình khuyến mãi nào đang diễn ra{airline_msg}."],
                "tasks": remaining_tasks 
            }
        
        docs = docs[:5] 
        
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        result_string = (
            f"{ContextTag.PROMO_INFO}\n"
            f"- NGÀY HỆ THỐNG: {current_date_str}\n"
            f"- DANH SÁCH ƯU ĐÃI HIỆU LỰC:\n"
        )
        
        for idx, promo in enumerate(docs, 1):
            b_end = promo.booking_end_date.strftime("%d/%m/%Y") if promo.booking_end_date else "Không giới hạn"
            t_start = promo.travel_start_date.strftime("%d/%m/%Y") if promo.travel_start_date else "N/A"
            t_end = promo.travel_end_date.strftime("%d/%m/%Y") if promo.travel_end_date else "N/A"
            
            result_string += f"\n▶ {idx}. {promo.promo_name}\n"
            result_string += f"   - Mã code: {promo.promo_code or 'Tự động áp dụng'}\n"
            result_string += f"   - Hạn đặt: {b_end}\n"
            result_string += f"   - Bay từ {t_start} đến {t_end}\n"
            result_string += f"   - Nội dung: {promo.description}\n"
            result_string += f"   - Điều kiện: {promo.conditions}\n"
            result_string += f"   - [Link chi tiết]: {promo.url}\n"
                
        return {
            "node_results": [result_string.strip()], 
            "tasks": remaining_tasks 
        }
    
    except Exception as e:
        print(f"ERROR - Promo SQL Node: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống tra cứu khuyến mãi đang gặp sự cố kết nối."],
            "tasks": remaining_tasks
        }