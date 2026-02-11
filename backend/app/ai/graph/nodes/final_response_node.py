from app.ai.graph.state import ChatState
from app.core.i18n_service import i18n

def final_response_node(state: ChatState):
    lang = state.language
    missing_slots = []

    if not state.origin:
        missing_slots.append(i18n.get_field_name("origin", lang))
    if not state.destination:
        missing_slots.append(i18n.get_field_name("destination", lang))
    if not state.departureDate:
        missing_slots.append(i18n.get_field_name("departureDate", lang))

    if missing_slots:
        missing_str = ", ".join(missing_slots)
        return {
            "response_text": i18n.get_msg("ask_missing_info", lang=lang, missing_str=missing_str)
        }

    city_origin = i18n.get_city(state.origin, lang)
    city_dest = i18n.get_city(state.destination, lang)

    response = i18n.get_msg(
        "searching_flights", 
        lang=lang, 
        origin=city_origin, 
        dest=city_dest, 
        date=state.departureDate
    )

    return {
        "response_text": response
    }