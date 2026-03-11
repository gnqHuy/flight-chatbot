import re
from datetime import datetime

def get_price(f):
    p = f.get('price', {})
    return float(p.get('total', 0)) if isinstance(p, dict) else float(f.get('price', 0))

def get_airline(f):
    airlines_list = f.get('airlines')
    if airlines_list and isinstance(airlines_list, list) and len(airlines_list) > 0:
        return airlines_list[0]
    if f.get('airline'): return f.get('airline')
    if f.get('airlineCode'): return f.get('airlineCode')
    return 'Unknown'

def parse_duration_to_minutes(duration_str: str) -> int:
    """Chuyển đổi chuỗi '1h 20m' hoặc 'PT1H20M' thành tổng số phút để dễ so sánh"""
    if not duration_str or not isinstance(duration_str, str): return 9999
    
    h_match = re.search(r'(\d+)\s*h', duration_str.lower())
    m_match = re.search(r'(\d+)\s*m', duration_str.lower())
    
    hours = int(h_match.group(1)) if h_match else 0
    minutes = int(m_match.group(1)) if m_match else 0
    
    return hours * 60 + minutes

def get_departure_time(f) -> str:
    dep_time = f.get('departure', {}).get('at', '')
    if 'T' in dep_time: return dep_time.split('T')[1]
    return '23:59:59' # Nếu không có, đẩy xuống cuối

def analyze_flights_for_comparison(flights: list, sort_pref: str = "price") -> str:
    """So sánh tổng quát mảng chuyến bay dựa trên tiêu chí khách chọn"""
    if not flights: return ""
    
    try:
        if sort_pref == "duration":
            sorted_flights = sorted(flights, key=lambda x: parse_duration_to_minutes(x.get('duration', '')))
            criteria_name = "THỜI GIAN BAY NGẮN NHẤT"
        elif sort_pref == "departure_time":
            sorted_flights = sorted(flights, key=get_departure_time)
            criteria_name = "BAY SỚM NHẤT"
        else:
            sorted_flights = sorted(flights, key=get_price)
            criteria_name = "GIÁ RẺ NHẤT"

        best_overall = sorted_flights[0]
        
        airline_best = {}
        for f in sorted_flights:
            airline = get_airline(f)
            if airline not in airline_best:
                airline_best[airline] = f

        report = [f"[BÁO CÁO PHÂN TÍCH SO SÁNH - TIÊU CHÍ: {criteria_name}]"]
        report.append(f"- TỐT NHẤT TOÀN CHUYẾN: Mã {best_overall.get('flightNumber')} (Hãng {get_airline(best_overall)})")
        report.append(f"  + Giá: {get_price(best_overall):,.0f} VND | Thời gian bay: {best_overall.get('duration', 'N/A')} | Cất cánh: {get_departure_time(best_overall)[:5]}")
        
        report.append("- TỐT NHẤT THEO TỪNG HÃNG:")
        for airline, f in airline_best.items():
            report.append(f"  + Hãng {airline} (Chuyến {f.get('flightNumber')}): Giá {get_price(f):,.0f} VND | Bay: {f.get('duration', 'N/A')} | Cất cánh: {get_departure_time(f)[:5]}")
            
        return "\n".join(report)
    except Exception as e:
        print(f"Lỗi phân tích tổng quát: {e}")
        return "[LỖI HỆ THỐNG]: Không thể thực hiện phân tích so sánh."

def analyze_specific_flights(flights: list, target_flight_numbers: list) -> str:
    """So sánh chi tiết các chuyến bay cụ thể bằng mã chuyến bay"""
    if not flights or not target_flight_numbers: return ""
        
    try:
        targets = [str(f).upper().replace(" ", "") for f in target_flight_numbers]
        found_flights = [f for f in flights if str(f.get('flightNumber', '')).upper().replace(" ", "") in targets]
                
        if not found_flights:
            return f"[FLIGHTS_NOT_FOUND]: Không tìm thấy dữ liệu cho các mã {', '.join(targets)}."

        report = ["[BÁO CÁO PHÂN TÍCH CHUYẾN BAY CỤ THỂ]"]
        for f in found_flights:
            fname = f.get('flightNumber', 'Unknown')
            price = get_price(f)
            dur = f.get('duration', 'N/A')
            dep = get_departure_time(f)[:5]
            baggage = f.get('baggage', 'N/A')
            
            report.append(f"- Chuyến {fname}: Bay lúc {dep}. Giá: {price:,.0f} VND. Hành lý: {baggage}. Thời gian bay: {dur}.")
            
        if len(found_flights) >= 2:
            sorted_by_price = sorted(found_flights, key=get_price)
            report.append(f"\n[KẾT LUẬN NHANH]: Chuyến {sorted_by_price[0].get('flightNumber')} có giá rẻ hơn.")

        return "\n".join(report)
    except Exception as e:
        print(f"Lỗi phân tích cụ thể: {e}")
        return "[LỖI HỆ THỐNG]: Lỗi trích xuất dữ liệu chuyến bay."