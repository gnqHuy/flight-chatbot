import traceback
from app.ai.graph.state import ChatState
from app.ai.llm.intent_extractor import extract_intent_and_slots

def extract_intent_node(state: ChatState) -> ChatState:
    print("\n--- NODE: EXTRACTING INTENT AND SLOTS ---", state, "\n")   
    result = extract_intent_and_slots(state.user_message, state.language)

    return state.copy(update={
        "intent": result.intent,
        "origin": result.origin if result.origin else state.origin,
        "destination": result.destination if result.destination else state.destination,
        "departureDate": result.departureDate if result.departureDate else state.departureDate,
        "returnDate": result.returnDate if result.returnDate else state.returnDate,
        "adults": result.adults if result.adults else state.adults,
    })