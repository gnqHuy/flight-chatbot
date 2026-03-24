from typing import TypedDict, Annotated, List, Dict, Any, Optional
from app.schemas.chat_state import Task
from app.utils.helpers import merge_chat_history, merge_dicts, merge_node_results, merge_saved_flights, merge_search_id

class ChatState(TypedDict):
    user_message: str  
    tasks: List[Task] 
    node_results: Annotated[list[str], merge_node_results]
    user_prefs: Annotated[Dict[str, Any], merge_dicts]
    language: str
    action: Optional[dict]     
    error_msg: Optional[str]
    response_text: str
    current_search_id: Annotated[Optional[str], merge_search_id]
    chat_history: Annotated[dict, merge_chat_history]
    saved_flights: Annotated[list[dict], merge_saved_flights]