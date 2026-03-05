import json
from app.ai.graph.state import ChatState
from app.services.flight_service import flight_service
from app.services.redis_service import redis_service
from app.core.i18n_service import i18n

def analyze_flights_for_comparison(flights: list) -> str:
    if not flights: return ""
    try:
        def get_price(f):
            p = f.get('price', {})
            return float(p.get('total', 0)) if isinstance(p, dict) else float(f.get('price', 0))

        def get_airline(f):
            airlines = f.get('validatingAirlineCodes', ['Unknown'])
            return airlines[0] if airlines else 'Unknown'

        sorted_flights = sorted(flights, key=get_price)
        cheapest = sorted_flights[0]
        
        airline_cheapest = {}
        for f in sorted_flights:
            airline = get_airline(f)
            if airline not in airline_cheapest:
                airline_cheapest[airline] = f

        report = ["[BÁO CÁO PHÂN TÍCH SO SÁNH]"]
        report.append(f"- RẺ NHẤT TOÀN CHUYẾN: Hãng {get_airline(cheapest)}, Giá: {get_price(cheapest)}")
        report.append("- RẺ NHẤT THEO TỪNG HÃNG:")
        for airline, f in airline_cheapest.items():
            report.append(f"  + {airline}: {get_price(f)}")
            
        return "\n".join(report)
    except Exception as e:
        print(f"Lỗi phân tích so sánh: {e}")
        return "Hệ thống đang đối chiếu dữ liệu các chuyến bay..."

def compare_flights_node(state: ChatState) -> dict:
    user_prefs = state.get("user_prefs", {})
    lang = state.get("language", "vi")
    
    origin = user_prefs.get("origin")
    dest = user_prefs.get("destination")
    date = user_prefs.get("departureDate")

    missing_fields = []
    if not origin: missing_fields.append(i18n.get_field_name("origin", lang))
    if not dest: missing_fields.append(i18n.get_field_name("destination", lang))
    if not date: missing_fields.append(i18n.get_field_name("departureDate", lang))

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        return {
            "node_results": [f"[SLOT_FILLING_REQUIRED]: {missing_str}"],
            "action": None
        }

    current_search_id = user_prefs.get("current_search_id")
    flights = []
    
    if current_search_id:
        cached_data = redis_service.get_flight_offers(current_search_id)
        if cached_data:
            flights = json.loads(cached_data) if isinstance(cached_data, str) else cached_data

    if not flights:
        flights = flight_service.search_flights(origin, dest, date)
        if flights:
            current_search_id = redis_service.save_flight_offers(flights)
            
    if not flights:
        not_found_msg = i18n.get_msg("flight_not_found", lang=lang, origin=origin, dest=dest, date=date)
        return {"node_results": [not_found_msg]}

    analysis_report = analyze_flights_for_comparison(flights)
    
    return {
        "node_results": [analysis_report],
        "action": {
            "type": "flight_list",
            "payload": {"search_id": current_search_id}
        },
        "user_prefs": {"current_search_id": current_search_id} 
    }