"""
app/ai_orchestrator/graph/flight_graph.py
Build và init ReAct agent graph.
Chỉ chứa graph assembly — logic nằm ở các modules riêng.
"""
import functools
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.ai_orchestrator.graph.state import FlightAgentState
from app.ai_orchestrator.graph.nodes import agent_node, post_process_node
from app.core.llm_setup import llm

from app.ai_orchestrator.graph.tools.flight_tool import (
    search_flights, filter_flights, analyze_flights
)
from app.ai_orchestrator.graph.tools.knowledge_tool import (
    get_airline_info, search_policies, get_promotions
)

TOOLS = [
    search_flights, 
    filter_flights, 
    analyze_flights, 
    search_policies, 
    get_promotions, 
    get_airline_info
]

flight_graph = None

def _should_continue(state: FlightAgentState) -> str:
    """Nếu LLM ra tool_calls → chạy tools. Không thì post_process."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "post_process"

llm_with_tools = llm.bind_tools(TOOLS)
tool_node      = ToolNode(TOOLS)

builder = StateGraph(FlightAgentState)
builder.add_node("agent", functools.partial(agent_node, llm_with_tools=llm_with_tools))
builder.add_node("tools", tool_node)
builder.add_node("post_process", post_process_node)

builder.add_edge(START, "agent")
builder.add_conditional_edges(
    "agent", 
    _should_continue,
    {"tools": "tools", "post_process": "post_process"}
)
builder.add_edge("tools", "agent")
builder.add_edge("post_process", END)


def build_graph_for_llm(custom_llm, checkpointer):
    """Build graph với LLM bất kỳ — dùng cho multi-model test."""
    custom_llm_with_tools = custom_llm.bind_tools(TOOLS)
    custom_tool_node      = ToolNode(TOOLS)

    graph = StateGraph(FlightAgentState)
    graph.add_node("agent", functools.partial(agent_node, llm_with_tools=custom_llm_with_tools))
    graph.add_node("tools", custom_tool_node)
    graph.add_node("post_process", post_process_node)
    
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", 
        _should_continue,
        {"tools": "tools", "post_process": "post_process"}
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("post_process", END)
    
    return graph.compile(checkpointer=checkpointer)