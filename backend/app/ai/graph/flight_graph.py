from typing import List, Literal
from langgraph.graph import StateGraph, START, END

from app.ai.graph.state import ChatState
from app.core.enums import ChatIntent
from app.database.checkpointer import get_checkpointer

from app.ai.graph.nodes.splitter_node import splitter_node
from app.ai.graph.nodes.extract_intent_node import extract_intent_node
from app.ai.graph.nodes.search_flight_node import search_flights_node
from app.ai.graph.nodes.compare_flights_node import compare_flights_node
from app.ai.graph.nodes.rag_node import rag_node
from app.ai.graph.nodes.final_response_node import final_response_node

def route_tasks(state: ChatState) -> List[str]:
    tasks = state.get("tasks", [])
    next_nodes = set()
    
    if not tasks:
        return ["final_response"]
    
    intents = [t.intent for t in tasks]
    
    if ChatIntent.COMPARE_FLIGHTS in intents or ChatIntent.PRICE_ANALYSIS in intents:
        next_nodes.add("compare_flights")
    elif ChatIntent.SEARCH_FLIGHT in intents:
        next_nodes.add("search_flights")
                
    if ChatIntent.GENERAL_QUESTION in intents:
        next_nodes.add("rag_node")
            
    if not next_nodes:
        next_nodes.add("final_response")
            
    return list(next_nodes)

def build_flight_graph():
    checkpointer = get_checkpointer()
    graph = StateGraph(ChatState)

    graph.add_node("splitter", splitter_node)           
    graph.add_node("extract_intent", extract_intent_node) 
    graph.add_node("search_flights", search_flights_node) 
    graph.add_node("compare_flights", compare_flights_node)
    graph.add_node("rag_node", rag_node)                
    graph.add_node("final_response", final_response_node) 

    graph.add_edge(START, "splitter")
    graph.add_edge("splitter", "extract_intent")
    
    graph.add_conditional_edges(
        "extract_intent",
        route_tasks,
        {
            "search_flights": "search_flights",
            "compare_flights": "compare_flights",
            "rag_node": "rag_node",
            "final_response": "final_response"
        }
    )

    graph.add_edge("search_flights", "final_response")
    graph.add_edge("compare_flights", "final_response")
    graph.add_edge("rag_node", "final_response")
    
    graph.add_edge("final_response", END)

    return graph.compile(checkpointer=checkpointer)

flight_graph = build_flight_graph()