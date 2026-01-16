from langgraph.graph import StateGraph

from app.ai.graph.nodes.final_response_node import final_response_node
from app.ai.graph.nodes.ask_missing_info_node import ask_missing_info_node
from app.ai.graph.nodes.decide_next_node import decide_next_node
from app.ai.graph.nodes.extract_intent_node import extract_intent_node
from app.ai.graph.nodes.search_flight_node import search_flights_node
from app.ai.graph.state import ChatState


def build_flight_graph():
    graph = StateGraph(ChatState)

    graph.add_node("extract_intent", extract_intent_node)
    graph.add_node("ask_missing_info", ask_missing_info_node)
    graph.add_node("search_flights", search_flights_node)
    graph.add_node("final_response", final_response_node)

    graph.set_entry_point("extract_intent")

    graph.add_conditional_edges(
        "extract_intent",
        decide_next_node,
        {
            "ask_missing_info": "ask_missing_info",
            "search_flights": "search_flights",
            "final_response": "final_response",
        }
    )

    graph.add_edge("ask_missing_info", "final_response")
    graph.add_edge("search_flights", "final_response")

    return graph.compile()

flight_graph = build_flight_graph()
