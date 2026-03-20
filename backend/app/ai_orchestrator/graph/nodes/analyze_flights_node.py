import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.flight_analysis import format_flights_to_text
from app.utils.helpers import consume_task 

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE PHÂN TÍCH CHUYẾN BAY ---")
    print("\n👉 [DEBUG - PREFS]: ", state.get("user_prefs", {}))
    print("\n🔹🔹🔹 ------------------------------------")
    
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "analyze_flights")
    
    raw_targets = user_prefs.get("analysis_targets", [])
    raw_criteria = user_prefs.get("criteria", [])
    
    if not current_search_id or current_search_id == "CLEAR":
        return {
            "node_results": ["[NGỮ CẢNH PHÂN TÍCH]: Không có danh sách chuyến bay hiện tại để so sánh."],
            "tasks": remaining_tasks,
            "user_prefs": {"analysis_targets": ["CLEAR"], "criteria": ["CLEAR"]}
        }

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return {
            "node_results": ["[NGỮ CẢNH PHÂN TÍCH]: Dữ liệu chuyến bay trống hoặc đã hết hạn."],
            "tasks": remaining_tasks,
            "user_prefs": {"analysis_targets": ["CLEAR"], "criteria": ["CLEAR"]}
        }

    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    targets_clean = [str(t).upper().replace(" ", "") for t in raw_targets if t and str(t).upper() != "CLEAR"]
    criteria_clean = [c.value if hasattr(c, 'value') else str(c) for c in raw_criteria if str(c).upper() != "CLEAR"]
    
    if not criteria_clean:
        criteria_clean = ["PRICE", "TIME"]

    target_flights = []
    
    if not targets_clean:
        target_flights = all_flights[:3] if isinstance(all_flights, list) else []
    elif isinstance(all_flights, list):
        for target in targets_clean:
            if len(target) == 2: 
                count = 0
                for f in all_flights:
                    flight_num = str(f.get('flightNumber', '')).upper()
                    airlines = [str(a).upper() for a in f.get('airlines', [])]
                    
                    if target in airlines or flight_num.startswith(target):
                        target_flights.append(f)
                        count += 1
                        if count >= 2:
                            break
            else: 
                for f in all_flights:
                    if str(f.get('flightNumber', '')).upper() == target:
                        target_flights.append(f)
                        break

    unique_targets = list({f.get('id'): f for f in target_flights if f.get('id')}.values())

    if unique_targets:
        flights_text = format_flights_to_text(unique_targets)
        criteria_str = ", ".join(criteria_clean)
        
        report = (
            "[[SYSTEM_CONTEXT: DỮ LIỆU PHÂN TÍCH CHUYẾN BAY]]\n"
            "Dưới đây là thông tin chi tiết các chuyến bay khách hàng đang quan tâm.\n"
            f"**TIÊU CHÍ KHÁCH YÊU CẦU TẬP TRUNG**: {criteria_str}\n\n"
            "**DỮ LIỆU THỰC TẾ:**\n"
            f"{flights_text}\n\n"
            "[[YÊU CẦU CHO AI]]: Hãy đóng vai chuyên gia tư vấn, sử dụng ĐÚNG các số liệu trên "
            "để phân tích, so sánh và trả lời câu hỏi của khách hàng bằng văn phong tự nhiên. KHÔNG ĐƯỢC BỊA ĐẶT THÔNG TIN."
        )
    else:
        report = f"[[SYSTEM_CONTEXT]]: Không tìm thấy chuyến bay nào khớp với yêu cầu ({targets_clean}) trong danh sách."

    print(f"👉 [DEBUG]: Đã đóng gói {len(unique_targets)} chuyến bay vào Context.")
    print("🔹🔹🔹 ------------------------------------")
    
    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "user_prefs": {
            "analysis_targets": ["CLEAR"], 
            "criteria": ["CLEAR"]
        }
    }