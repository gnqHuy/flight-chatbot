import json
from langchain_core.tools import tool
from app.services.redis_service import redis_service
from app.services.airline_service import airline_service
from app.utils.flight_analysis import format_flights_to_text

@tool
def fetch_airline_info(airline_codes: list[str], search_id: str) -> str:
    """Gọi tool này khi cần lấy thông tin chính sách, uy tín, dịch vụ của các Hãng bay để so sánh."""
    try:
        db_info = airline_service.get_airlines_analysis_context(airline_codes)
        
        example_text = "Không tìm thấy vé ví dụ."
        if search_id and search_id not in ["CLEAR", "NOT_FOUND"]:
            cached_data = redis_service.get_flight_offers(search_id)
            if cached_data:
                all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
                example_flights = []
                
                if isinstance(all_flights, list):
                    for code in airline_codes:
                        flights_of_airline = [f for f in all_flights if code in [str(a).upper() for a in f.get('airlines', [])]]
                        if flights_of_airline:
                            flights_of_airline.sort(key=lambda x: float(x.get('price', 99999999)))
                            example_flights.append(flights_of_airline[0])
                            
                if example_flights:
                    example_text = format_flights_to_text(example_flights)

        return f"[THÔNG TIN HÃNG BAY (SQL)]:\n{db_info}\n\n[VÉ MINH HỌA (REDIS)]:\n{example_text}"
    
    except Exception as e:
        return f"Lỗi khi lấy thông tin hãng bay: {str(e)}"


@tool
def fetch_flight_details(flight_numbers: list[str], search_id: str) -> str:
    """Gọi tool này khi cần lấy thông tin chi tiết các hạng vé/tùy chọn của MỘT HOẶC NHIỀU MÃ CHUYẾN BAY (VD: VN135, VJ197)."""
    
    if not search_id or search_id in ["CLEAR", "NOT_FOUND"]:
        return "Lỗi: Yêu cầu khách tìm kiếm chuyến bay trước."

    try:
        cached_data = redis_service.get_flight_offers(search_id)
        if not cached_data:
            return "Lỗi: Không tìm thấy dữ liệu vé trong bộ nhớ. Phiên tìm kiếm có thể đã hết hạn."

        all_flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data
        
        if not isinstance(all_flights, list):
            return "Lỗi: Dữ liệu vé không hợp lệ."

        if isinstance(flight_numbers, str):
            flight_numbers = [fn.strip() for fn in flight_numbers.split(',')]
        elif not isinstance(flight_numbers, list):
            flight_numbers = [str(flight_numbers)]

        target_flights = [str(fn).strip().upper().replace(" ", "").replace("-", "") for fn in flight_numbers]
    
        matched_flights = []
        
        for f in all_flights:
            itineraries = f.get('itineraries', [])
            if not itineraries:
                continue
                
            flight_num_raw = str(itineraries[0].get('flightNumber', '')).strip().upper().replace(" ", "")

            if flight_num_raw in target_flights:
                matched_flights.append(f)
                
        if not matched_flights:
            return f"Không tìm thấy thông tin cho các mã chuyến bay: {target_flights}. (Hệ thống hiện đang có {len(all_flights)} vé)."
            
        matched_flights.sort(key=lambda x: float(x.get('price', 0)))
            
        return f"[CHI TIẾT CÁC HẠNG VÉ CỦA CHUYẾN BAY {target_flights}]:\n\n{format_flights_to_text(matched_flights)}"
        
    except Exception as e:
        return f"Lỗi khi kéo chi tiết chuyến bay: {str(e)}"