"""
app/ai_orchestrator/graph/state.py
FlightAgentState — custom state cho ReAct agent.
"""
from typing import Annotated, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class FlightAgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    search_filters:    dict
    current_search_id: Optional[str]
    action:            Optional[dict]