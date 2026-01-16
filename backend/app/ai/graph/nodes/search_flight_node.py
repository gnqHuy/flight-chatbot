from app.ai.graph.state import ChatState

def search_flights_node(state: ChatState) -> ChatState:
    # TODO: gọi Amadeus
    state.flight_offers = [
        {"price": 120, "airline": "VN"},
        {"price": 100, "airline": "VJ"},
    ]

    return state.copy(update={
        "response_text": f"Tìm thấy {len(state.flight_offers)} chuyến bay phù hợp."
    })
