from langgraph.graph import StateGraph, END
from app.ai.graph.nodes.final_response_node import final_response_node
from app.ai.graph.nodes.extract_intent_node import extract_intent_node
from app.ai.graph.nodes.search_flight_node import search_flights_node
from app.ai.graph.nodes.rag_node import rag_node
from app.ai.graph.state import ChatState
from app.database.checkpointer import get_checkpointer

def route_check_slots(state: ChatState) -> str:
    if state.intent in ["greeting", "out_of_scope"]:
        return "final_response"
        
    if state.intent == "general_question":
        return "rag_node"
        
    if state.intent in ["search_flight", "provide_info"]:
        required_slots = ["origin", "destination", "departureDate"]
        
        for slot in required_slots:
            if not getattr(state, slot, None):
                return "final_response"
                
        return "search_flights"
        
    return "final_response"

def build_flight_graph():
    checkpointer = get_checkpointer()
    graph = StateGraph(ChatState)

    graph.add_node("extract_intent", extract_intent_node)
    graph.add_node("search_flights", search_flights_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("final_response", final_response_node)

    graph.set_entry_point("extract_intent")
    graph.add_conditional_edges(
        "extract_intent",
        route_check_slots,
        {
            "final_response": "final_response",
            "search_flights": "search_flights",
            "rag_node": "rag_node"
        }
    )
    graph.add_edge("search_flights", "final_response")
    graph.add_edge("rag_node", "final_response")
    graph.add_edge("final_response", END)

    return graph.compile(checkpointer=checkpointer)

flight_graph = build_flight_graph()