import json
from app.ai.graph.state import ChatState
from app.services.flight_service import flight_service
from app.core.i18n_service import i18n
from app.services.redis_service import redis_service

def search_flights_node(state: ChatState) -> dict:
    user_prefs = state.get("user_prefs", {})
    lang = state.get("language", "vi")
    
    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")

    missing_fields = []
    if not origin: missing_fields.append(i18n.get_field_name("origin", lang))
    if not destination: missing_fields.append(i18n.get_field_name("destination", lang))
    if not departureDate: missing_fields.append(i18n.get_field_name("departureDate", lang))

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        return {
            "node_results": [f"[SLOT_FILLING_REQUIRED]: {missing_str}"],
            "action": None
        }

    city_origin = i18n.get_city(origin, lang)
    city_dest = i18n.get_city(destination, lang)
    
    try:
        flights = flight_service.search_flights(origin, destination, departureDate)
        
        if not flights:
            not_found_msg = i18n.get_msg(
                "flight_not_found", lang=lang, origin=city_origin, dest=city_dest, date=departureDate
            )
            return {"node_results": [not_found_msg], "action": None}
        
        search_id = redis_service.save_flight_offers(flights)
        
        found_msg = i18n.get_msg(
            "flight_found", lang=lang, count=len(flights), origin=city_origin, dest=city_dest, date=departureDate
        )
        
        return {
            "node_results": [found_msg],
            "action": {
                "type": "flight_list",
                "payload": {"search_id": search_id}
            },
            "user_prefs": {"current_search_id": search_id}
        }

    except Exception as e:
        print(f"Lỗi tìm vé: {e}")
        return {
            "node_results": [i18n.get_msg("search_error", lang=lang)], 
            "error_msg": str(e)
        }