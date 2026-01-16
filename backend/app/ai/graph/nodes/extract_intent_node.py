from app.ai.graph.state import ChatState
from app.ai.llm.intent_extractor import extract_intent_and_slots

def extract_intent_node(state: ChatState) -> ChatState:
    result = extract_intent_and_slots(state.user_message)

    return state.copy(update={
        "intent": result.intent,
        "origin": result.origin,
        "destination": result.destination,
        "departureDate": result.departureDate,
        "returnDate": result.returnDate,
        "adults": result.adults,
    })
