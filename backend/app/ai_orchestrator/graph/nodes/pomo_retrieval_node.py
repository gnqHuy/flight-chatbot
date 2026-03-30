from app.ai_orchestrator.graph.state import ChatState
from sqlmodel import Session
from app.database.database import engine
from app.repositories.flight_promotion_repo import FlightPromotionRepository
from app.database.models.airline import Airline
from app.utils.helpers import consume_task
from datetime import datetime
from sqlmodel import select

def promo_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TÌM KIẾM KHUYẾN MÃI (SQL REPO) ---")
    
    user_prefs = state.get("user_prefs", {})
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "promo_search") 
    
    target_airline_list = user_prefs.get("target_airline")
    
    target_airline_code = None
    if target_airline_list and isinstance(target_airline_list, list) and target_airline_list[0] != "CLEAR":
        target_airline_code = target_airline_list[0].upper()
    elif isinstance(target_airline_list, str) and target_airline_list != "CLEAR":
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
                    print(f"👉 [GỠ LỖI]: Đang tìm khuyến mãi của hãng {target_airline_code} (ID: {target_airline_id})")
                else:
                    print(f"👉 [GỠ LỖI]: Không tìm thấy ID của hãng {target_airline_code} trong Database.")
            else:
                print("👉 [GỠ LỖI]: Không chỉ định hãng, đang quét TẤT CẢ khuyến mãi còn hiệu lực...")

            docs = repo.get_active_promotions(target_airline_id=target_airline_id)
            
        if not docs:
            return {
                "node_results": ["[KHÔNG_TÌM_THẤY] Hiện tại không có chương trình khuyến mãi nào đang diễn ra phù hợp với yêu cầu của khách hàng."],
                "tasks": remaining_tasks 
            }
        
        docs = docs[:5] 
        
        current_date_str = datetime.now().strftime("%d/%m/%Y")
        result_string = (
            f"[TRA CỨU KHUYẾN MÃI]\n"
            f"- NGÀY HÔM NAY: {current_date_str}\n"
            f"- DANH SÁCH KHUYẾN MÃI CÒN HIỆU LỰC TỪ HỆ THỐNG:\n"
        )
        
        for idx, promo in enumerate(docs, 1):
            b_end = promo.booking_end_date.strftime("%d/%m/%Y") if promo.booking_end_date else "Không giới hạn"
            t_start = promo.travel_start_date.strftime("%d/%m/%Y") if promo.travel_start_date else "N/A"
            t_end = promo.travel_end_date.strftime("%d/%m/%Y") if promo.travel_end_date else "N/A"
            
            result_string += f"\n▶ ƯU ĐÃI {idx}: {promo.promo_name}\n"
            result_string += f"  - Mã áp dụng: {promo.promo_code or 'Không cần mã nhập tay'}\n"
            result_string += f"  - Hạn đặt vé: Đến hết ngày {b_end}\n"
            result_string += f"  - Giai đoạn bay: Từ {t_start} đến {t_end}\n"
            result_string += f"  - Mô tả: {promo.description}\n"
            result_string += f"  - Điều kiện: {promo.conditions}\n"
            result_string += f"  - [Link tham khảo]: {promo.url}\n"
                
        print(f"\n👉 [GỠ LỖI - KẾT QUẢ KHUYẾN MÃI]: Đã tìm thấy {len(docs)} chương trình ưu đãi bằng SQL.")
        
        return {
            "node_results": [result_string.strip()], 
            "tasks": remaining_tasks 
        }
    
    except Exception as e:
        print(f"❌ [LỖI SQL]: Lỗi khi truy xuất dữ liệu khuyến mãi: {e}")
        return {
            "node_results": ["[LỖI] Hệ thống tra cứu khuyến mãi đang bảo trì, vui lòng xin lỗi khách hàng."],
            "tasks": remaining_tasks
        }