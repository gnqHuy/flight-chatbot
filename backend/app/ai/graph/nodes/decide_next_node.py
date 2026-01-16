from app.ai.graph.state import ChatState

def decide_next_node(state: ChatState) -> str:
    if state.intent != "search_flight":
        return "final_response"

    if not state.origin or not state.destination:
        return "ask_missing_info"

    if not state.departureDate:
        return "ask_missing_info"

    return "search_flights"
