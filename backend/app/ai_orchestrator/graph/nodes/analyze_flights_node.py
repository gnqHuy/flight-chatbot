import json
from app.ai_orchestrator.graph.state import ChatState
from app.services.redis_service import redis_service
from app.services.airline_service import airline_service
from app.utils.flight_analysis import format_flights_to_text
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

def analyze_flights_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM PHÂN TÍCH CHUYẾN BAY & HÃNG BAY ---")
    
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
        criteria_clean = ["giá vé", "thời gian bay", "chính sách hãng"]

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
                    airlines_in_flight = [str(a).upper() for a in f.get('airlines', [])]
                    if target_a in airlines_in_flight:
                        target_flights_to_analyze.append(f)
                        count += 1
                        if count >= 2: break

    unique_targets = list({f.get('id'): f for f in target_flights_to_analyze if f.get('id')}.values())

    codes_for_db = set(t_airlines_clean)
    for f in unique_targets:
        for a in f.get('airlines', []):
            codes_for_db.add(str(a).upper())
    
    airline_info_context = airline_service.get_airlines_analysis_context(list(codes_for_db))

    if unique_targets:
        flights_text = format_flights_to_text(unique_targets)
        criteria_str = ", ".join(criteria_clean)
        
        report = (
            f"{ContextTag.FLIGHT_ANALYSIS}:\n"
            f"### DỮ LIỆU CHUYẾN BAY THỰC TẾ (REAL-TIME):\n"
            f"{flights_text}\n\n"
            f"### KIẾN THỨC NỀN TẢNG VỀ HÃNG (DATABASE):\n"
            f"{airline_info_context}\n\n"
            f"**YÊU CẦU PHÂN TÍCH**: Hãy dựa vào dữ liệu trên để so sánh theo các tiêu chí: {criteria_str}.\n"
            "Chỉ ra chuyến nào rẻ nhất, chuyến nào giờ bay đẹp nhất và ưu thế của từng hãng để khách hàng dễ dàng lựa chọn."
        )
    else:
        report = f"{ContextTag.SYS_NOT_FOUND}: Không tìm thấy chuyến bay khớp với yêu cầu để so sánh."

    return {
        "node_results": [report],
        "tasks": remaining_tasks,
        "user_prefs": {
            "target_flight": "CLEAR",
            "target_airline": "CLEAR",
            "criteria": "CLEAR"
        }
    }