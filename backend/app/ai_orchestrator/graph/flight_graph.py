from typing import List, Literal
from langgraph.graph import StateGraph, START, END

from app.ai_orchestrator.graph.state import ChatState
from app.core.enums import ChatIntent
from app.database.checkpointer import get_checkpointer

from app.ai_orchestrator.graph.nodes.extract_intent_node import extract_intent_node
from app.ai_orchestrator.graph.nodes.search_flight_node import search_flights_node
from app.ai_orchestrator.graph.nodes.analyze_flights_node import analyze_flights_node
from app.ai_orchestrator.graph.nodes.rag_node import rag_node
from app.ai_orchestrator.graph.nodes.final_response_node import final_response_node

def route_tasks(state: ChatState) -> str:
    tasks = state.get("tasks", [])
    
    if not tasks:
        return "final_response"
    
    current_task = tasks[0]
    intent = current_task.intent

    if intent == ChatIntent.SEARCH_FLIGHT:
        return "search_flights"
        
    if intent in [ChatIntent.ANALYZE_FLIGHTS, ChatIntent.PRICE_ANALYSIS]:
        return "analyze_flights"
        
    if intent == ChatIntent.GENERAL_QUESTION:
        return "rag_node"
            
    return "final_response"

def build_flight_graph():
    checkpointer = get_checkpointer()
    graph = StateGraph(ChatState)

    graph.add_node("extract_intent", extract_intent_node) 
    graph.add_node("search_flights", search_flights_node) 
    graph.add_node("analyze_flights", analyze_flights_node)
    graph.add_node("rag_node", rag_node)                
    graph.add_node("final_response", final_response_node) 

    graph.add_edge(START, "extract_intent")
    
    graph.add_conditional_edges(
        "extract_intent",
        route_tasks,
        {
            "search_flights": "search_flights",
            "analyze_flights": "analyze_flights",
            "rag_node": "rag_node",
            "final_response": "final_response"
        }
    )

    graph.add_edge("search_flights", "extract_intent")
    graph.add_edge("analyze_flights", "extract_intent")
    graph.add_edge("rag_node", "extract_intent")
    
    graph.add_edge("final_response", END)

    return graph.compile(checkpointer=checkpointer)

flight_graph = build_flight_graph()