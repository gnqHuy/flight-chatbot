from typing import TypedDict, Annotated, List, Dict, Any, Optional
from app.schemas.chat_state import Task
from app.utils.helpers import merge_chat_history, merge_dicts, merge_node_results, merge_saved_flights, merge_search_id, overwrite_dict


class SearchFiltersState(TypedDict, total=False):
    origin: Optional[str]
    destination: Optional[str]
    departureDate: Optional[str]
    returnDate: Optional[str]
    roundTrip: bool
    travelClass: Optional[str]
    adults: int
    children: int
    infants: int
    need_age_confirmation: bool
    preferred_airlines: Optional[List[str]]
    maxPrice: Optional[int]
    nonStop: Optional[bool]
    start_hour: Optional[int]
    end_hour: Optional[int]
    sort_preference: Optional[str]

class ActionTargetsState(TypedDict, total=False):
    compare_flights: Optional[List[str]]
    compare_airlines: Optional[List[str]]
    analysis_criteria: Optional[List[str]]


class ChatState(TypedDict):
    user_message: str  
    tasks: List[Task] 
    node_results: Annotated[list[str], merge_node_results]
    search_filters: Annotated[SearchFiltersState, merge_dicts]
    action_targets: Annotated[ActionTargetsState, overwrite_dict]
    language: str
    action: Optional[dict]     
    error_msg: Optional[str]
    response_text: str
    current_search_id: Annotated[Optional[str], merge_search_id]
    chat_history: Annotated[dict, merge_chat_history]
    saved_flights: Annotated[list[dict], merge_saved_flights]