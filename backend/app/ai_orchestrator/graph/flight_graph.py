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
from app.ai_orchestrator.graph.tools.flight_tool import (
    search_flights, filter_flights, analyze_flights
)
from app.ai_orchestrator.graph.tools.knowledge_tool import search_policies, get_promotions

TOOLS = [search_flights, filter_flights, analyze_flights, search_policies, get_promotions]

flight_graph = None


def _should_continue(state: FlightAgentState) -> str:
    """Nếu LLM ra tool_calls → chạy tools. Không thì post_process."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return "post_process"


async def build_graph_for_llm(llm, checkpointer):
    """Build graph với LLM bất kỳ — dùng cho multi-model test."""
    from app.ai_orchestrator.graph.tools.flight_tool import (
        search_flights, filter_flights, analyze_flights
    )
    from app.ai_orchestrator.graph.tools.knowledge_tool import search_policies, get_promotions

    tools          = [search_flights, filter_flights, analyze_flights, search_policies, get_promotions]
    llm_with_tools = llm.bind_tools(tools)
    tool_node      = ToolNode(tools)

    graph = StateGraph(FlightAgentState)
    graph.add_node("agent",        functools.partial(agent_node, llm_with_tools=llm_with_tools))
    graph.add_node("tools",        tool_node)
    graph.add_node("post_process", post_process_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", _should_continue,
                                {"tools": "tools", "post_process": "post_process"})
    graph.add_edge("tools", "agent")
    graph.add_edge("post_process", END)
    return graph.compile(checkpointer=checkpointer)


async def init_flight_graph(checkpointer):
    """Gọi trong on_startup sau khi checkpointer pool đã open."""
    global flight_graph

    from app.core.llm_setup import llm
    from app.database.checkpointer import get_checkpointer

    llm_with_tools = llm.bind_tools(TOOLS)
    tool_node      = ToolNode(TOOLS)

    graph = StateGraph(FlightAgentState)

    graph.add_node(
        "agent",
        functools.partial(agent_node, llm_with_tools=llm_with_tools),
    )
    graph.add_node("tools",        tool_node)
    graph.add_node("post_process", post_process_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent", _should_continue,
        {"tools": "tools", "post_process": "post_process"},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("post_process", END)

    flight_graph = graph.compile(checkpointer=checkpointer)
    print("[Graph] ReAct flight_graph compiled")
    return flight_graph