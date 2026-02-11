from app.ai.graph.state import ChatState
from app.services.flight_service import flight_service
from app.core.i18n_service import i18n

def search_flights_node(state: ChatState):
    origin = state.origin
    destination = state.destination
    departureDate = state.departureDate
    lang = state.language
    
    city_origin = i18n.get_city(origin, lang)
    city_dest = i18n.get_city(destination, lang)
    
    try:
        flights = flight_service.search_flights(origin, destination, departureDate)
        
        if not flights:
             return {
                "flight_offers": [], 
                "response_text": i18n.get_msg("flight_not_found", lang=lang, origin=city_origin, dest=city_dest, date=departureDate)
            }
            
        return {
            "flight_offers": flights,
            "response_text": i18n.get_msg("flight_found", lang=lang, count=len(flights), origin=city_origin, dest=city_dest, date=departureDate)
        }

    except Exception as e:
        print(f"Lỗi tìm vé: {e}")
        return {
            "flight_offers": [],
            "response_text": i18n.get_msg("search_error", lang=lang)
        }