from langgraph.graph import StateGraph, START, END
from app.ai_orchestrator.graph.state import ChatState
from app.core.enums import ChatIntent

from app.ai_orchestrator.graph.nodes.extract_intent_node import extract_intent_node
from app.ai_orchestrator.graph.nodes.search_flight_node import search_flights_node
from app.ai_orchestrator.graph.nodes.analyze_flights_node import analyze_flights_node
from app.ai_orchestrator.graph.nodes.filter_sort_flights_node import filter_sort_flights_node
from app.ai_orchestrator.graph.nodes.policy_retrieval_node import policy_retrieval_node
from app.ai_orchestrator.graph.nodes.final_response_node import final_response_node
from app.ai_orchestrator.graph.nodes.pomo_retrieval_node import promo_retrieval_node
from app.database.checkpointer import get_checkpointer

def route_tasks(state: ChatState) -> str:
    tasks = state.get("tasks", [])
    if not tasks:
        return "final_response"
    intent_val = tasks[0].intent.value if hasattr(tasks[0].intent, "value") else str(tasks[0].intent)
    return {
        ChatIntent.SEARCH_FLIGHT.value:       "search_flights",
        ChatIntent.FILTER_SORT_FLIGHTS.value: "filter_sort_flights",
        ChatIntent.ANALYZE_FLIGHTS.value:     "analyze_flights",
        ChatIntent.POLICY_QUESTION.value:     "policy_retrieval_node",
        ChatIntent.PROMO_SEARCH.value:        "promo_retrieval_node",
    }.get(intent_val, "final_response")


def _build_graph_skeleton():
    graph = StateGraph(ChatState)
    graph.add_node("extract_intent",       extract_intent_node)
    graph.add_node("search_flights",       search_flights_node)
    graph.add_node("filter_sort_flights",  filter_sort_flights_node)
    graph.add_node("analyze_flights",      analyze_flights_node)
    graph.add_node("policy_retrieval_node", policy_retrieval_node)
    graph.add_node("final_response",       final_response_node)
    graph.add_node("promo_retrieval_node", promo_retrieval_node)

    graph.add_edge(START, "extract_intent")

    routing_map = {
        "search_flights":        "search_flights",
        "filter_sort_flights":   "filter_sort_flights",
        "analyze_flights":       "analyze_flights",
        "policy_retrieval_node": "policy_retrieval_node",
        "promo_retrieval_node":  "promo_retrieval_node",
        "final_response":        "final_response",
    }
    graph.add_conditional_edges("extract_intent",        route_tasks, routing_map)
    graph.add_conditional_edges("search_flights",        route_tasks, routing_map)
    graph.add_conditional_edges("filter_sort_flights",   route_tasks, routing_map)
    graph.add_conditional_edges("analyze_flights",       route_tasks, routing_map)
    graph.add_conditional_edges("policy_retrieval_node", route_tasks, routing_map)
    graph.add_conditional_edges("promo_retrieval_node",  route_tasks, routing_map)
    graph.add_edge("final_response", END)
    return graph


flight_graph = None


async def init_flight_graph():
    """Gọi trong on_startup SAU KHI checkpointer pool đã open."""
    global flight_graph
    checkpointer = get_checkpointer()
    flight_graph = _build_graph_skeleton().compile(checkpointer=checkpointer)
    print("[Graph] flight_graph compiled with AsyncPostgresSaver")
    return flight_graph