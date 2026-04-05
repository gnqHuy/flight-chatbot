import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.utils.flight_analysis import format_flights_to_text
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH CHUYẾN BAY ---")
    print("\n👉 [DEBUG - NODE]: ", state.get("node_results", {}))
    print("\n🔹🔹🔹 ------------------------------------")
    
    user_prefs = state.get("user_prefs", {})
    current_search_id = state.get("current_search_id")
    tasks = state.get("tasks", [])
    
    remaining_tasks = consume_task(tasks, "analyze_flights")
    
    raw_target_flights = user_prefs.get("target_flight", [])
    raw_target_airlines = user_prefs.get("target_airline", [])
    raw_criteria = user_prefs.get("criteria", [])
    
    if not current_search_id or current_search_id in ["CLEAR", "NOT_FOUND"]:
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Không có danh sách chuyến bay hiện tại để so sánh. Vui lòng tìm kiếm trước."],
            "tasks": remaining_tasks,
            "user_prefs": {"target_flight": "CLEAR", "target_airline": "CLEAR", "criteria": "CLEAR"}
        }

    cached_data = redis_service.get_flight_offers(current_search_id)
    if not cached_data:
        return {
            "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Dữ liệu chuyến bay đã hết hạn. Vui lòng yêu cầu khách tìm kiếm lại."],
            "tasks": remaining_tasks,
            "user_prefs": {"target_flight": "CLEAR", "target_airline": "CLEAR", "criteria": "CLEAR"}
        }

    all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
    t_flights_clean = [str(t).upper().replace(" ", "") for t in raw_target_flights if t and str(t).upper() != "CLEAR"]
    t_airlines_clean = [str(t).upper().replace(" ", "") for t in raw_target_airlines if t and str(t).upper() != "CLEAR"]
    criteria_clean = [c.value if hasattr(c, 'value') else str(c) for c in raw_criteria if str(c).upper() != "CLEAR"]
    
    if not criteria_clean:
        criteria_clean = ["giá vé", "thời gian bay"]

    target_flights_to_analyze = []
    
    if not t_flights_clean and not t_airlines_clean:
        target_flights_to_analyze = all_flights[:3] if isinstance(all_flights, list) else []
    elif isinstance(all_flights, list):
        if t_flights_clean:
            for target_f in t_flights_clean:
                for f in all_flights:
                    if str(f.get('flightNumber', '')).upper() == target_f:
                        target_flights_to_analyze.append(f)
                        break
        if t_airlines_clean:
            for target_a in t_airlines_clean:
                count = 0
                for f in all_flights:
                    flight_num = str(f.get('flightNumber', '')).upper()
                    airlines = [str(a).upper() for a in f.get('airlines', [])]
                    if target_a in airlines or flight_num.startswith(target_a):
                        target_flights_to_analyze.append(f)
                        count += 1
                        if count >= 2: break

    unique_targets = list({f.get('id'): f for f in target_flights_to_analyze if f.get('id')}.values())

    if unique_targets:
        flights_text = format_flights_to_text(unique_targets)
        criteria_str = ", ".join(criteria_clean)
        
        report = (
            f"{ContextTag.FLIGHT_ANALYSIS}:\n"
            f"Dưới đây là dữ liệu thực tế về các chuyến bay khách đang quan tâm.\n"
            f"**TIÊU CHÍ ƯU TIÊN**: {criteria_str}\n\n"
            f"{flights_text}\n\n"
            "CHỈ THỊ: Sử dụng số liệu này để so sánh ưu/nhược điểm. Tuyệt đối không bịa thêm thông tin ngoài danh sách."
        )
    else:
        req_summary = f"Mã chuyến: {t_flights_clean} | Hãng: {t_airlines_clean}"
        report = f"{ContextTag.SYS_NOT_FOUND}: Không tìm thấy chuyến bay khớp với yêu cầu ({req_summary}) trong bộ nhớ tạm."

    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "user_prefs": {
            "target_flight": "CLEAR",
            "target_airline": "CLEAR",
            "criteria": "CLEAR"
        }
    }