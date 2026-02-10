from langgraph.graph import StateGraph

from app.ai.graph.nodes.final_response_node import final_response_node
from app.ai.graph.nodes.extract_intent_node import extract_intent_node
from app.ai.graph.nodes.search_flight_node import search_flights_node
from app.ai.graph.state import ChatState

from app.database.checkpointer import get_checkpointer

def route_check_slots(state):
    if not state.origin or not state.destination or not state.departureDate:
        return "final_response" 
    return "search_flights"

def build_flight_graph():
    checkpointer = get_checkpointer()
    graph = StateGraph(ChatState)

    graph.add_node("extract_intent", extract_intent_node)
    graph.add_node("search_flights", search_flights_node)
    graph.add_node("final_response", final_response_node)

    graph.set_entry_point("extract_intent")

    graph.add_conditional_edges(
        "extract_intent",
        route_check_slots,
        {
            "final_response": "final_response",
            "search_flights": "search_flights",
        }
    )

    graph.add_edge("search_flights", "final_response")

    app = graph.compile(checkpointer=checkpointer)
    return app

flight_graph = build_flight_graph()
