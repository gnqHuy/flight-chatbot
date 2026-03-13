import json
from app.services.redis_service import redis_service
from app.utils.flight_analysis import analyze_flights_for_comparison, analyze_specific_flights

def handle_general_analysis(grouped_data: dict | list, sort_preference: str) -> str:
    """Xử lý kịch bản 1: Phân tích mặt bằng chung (Không có mục tiêu)"""
    if not grouped_data:
        return "[ANALYZE_ERROR]: Không có dữ liệu chuyến bay trên màn hình để phân tích. Hãy yêu cầu khách cung cấp lại điểm đi/đến để tìm vé mới."

    final_pool = []
    if isinstance(grouped_data, dict):
        unique_pool = {}
        for bucket in grouped_data.values():
            if isinstance(bucket, list):
                for f in bucket:
                    unique_pool[str(f.get("flightNumber"))] = f
        final_pool = list(unique_pool.values())
    elif isinstance(grouped_data, list):
        final_pool = grouped_data

    if not final_pool:
        return "[ANALYZE_ERROR]: Danh sách chuyến bay trống."

    return analyze_flights_for_comparison(final_pool, sort_pref=sort_preference)


def handle_airline_comparison(grouped_data: dict, targets: list, sort_preference: str) -> str:
    """Xử lý kịch bản 2: So sánh Hãng bay (VD: VN vs VJ)"""
    if not isinstance(grouped_data, dict):
        return "[LỖI HỆ THỐNG]: Dữ liệu cache không đúng định dạng chia giỏ để so sánh hãng."

    best_flights_to_compare = []
    
    for airline_code in targets:
        bucket = grouped_data.get(airline_code, [])
        if bucket:
            if sort_preference == "duration":
                best_f = min(bucket, key=lambda x: int(x.get("duration_minutes", 9999)))
            else:
                best_f = min(bucket, key=lambda x: float(x.get("price", 0)))
            best_flights_to_compare.append(best_f)
            
    if best_flights_to_compare:
        report_core = analyze_specific_flights(best_flights_to_compare, targets)
        return f"[BÁO CÁO SO SÁNH CÁC HÃNG {', '.join(targets)} - ĐẠI DIỆN BỞI CHUYẾN TỐT NHẤT]\n" + report_core
    
    return f"[LỖI]: Không tìm thấy dữ liệu của hãng {', '.join(targets)} để so sánh lúc này."


def handle_specific_flight_comparison(current_search_id: str, saved_flights: list, recent_ids: list, targets: list) -> str:
    """Xử lý kịch bản 3: So sánh Chuyến bay cụ thể (Tìm lùi Fallback Search)"""
    found_flights = []
    missing_targets = set(targets)

    def _extract_from_grouped(g_data):
        if not isinstance(g_data, dict): return
        targets_to_remove = []
        for target_fn in missing_targets:
            airline_code = target_fn[:2]
            bucket = g_data.get(airline_code, [])
            for f in bucket:
                fn = str(f.get("flightNumber", "")).upper().replace(" ", "")
                if fn == target_fn:
                    found_flights.append(f)
                    targets_to_remove.append(target_fn)
                    break
        for t in targets_to_remove: missing_targets.remove(t)

    def _extract_from_flat(flat_list):
        if not flat_list: return
        targets_to_remove = []
        for f in flat_list:
            fn = str(f.get("flightNumber", "")).upper().replace(" ", "")
            if fn in missing_targets:
                found_flights.append(f)
                targets_to_remove.append(fn)
        for t in targets_to_remove: missing_targets.remove(t)

    if current_search_id and missing_targets:
        c_data = redis_service.get_flight_offers(current_search_id)
        g_data = json.loads(c_data) if isinstance(c_data, str) else c_data
        _extract_from_grouped(g_data)

    if missing_targets and saved_flights:
        _extract_from_flat(saved_flights)

    if missing_targets:
        for sid in reversed(recent_ids):
            if not missing_targets: break
            if sid == current_search_id: continue
            c_data = redis_service.get_flight_offers(sid)
            g_data = json.loads(c_data) if isinstance(c_data, str) else c_data
            _extract_from_grouped(g_data)

    return analyze_specific_flights(found_flights, targets)