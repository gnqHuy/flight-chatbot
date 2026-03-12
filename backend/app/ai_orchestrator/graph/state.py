from typing import TypedDict, Annotated, List, Dict, Any, Optional
from app.schemas.chat_state import Task

def merge_dicts(left: dict, right: dict) -> dict:
    left_dict = left or {}
    right_dict = right or {}
    
    merged = left_dict.copy()
    
    for k, v in right_dict.items():
        if v == "CLEAR" or v == ["CLEAR"]:
            merged.pop(k, None)
        elif v is not None:
            merged[k] = v
            
    return merged

def merge_list_with_clear(left: list, right: list) -> list:
    if right == ["CLEAR"]:
        return []
    
    left_list = left or []
    right_list = right or []
    return left_list + right_list

def merge_chat_history(left: dict, right: dict) -> dict:
    """Hàm cộng dồn lịch sử chat: Gộp mảng vào mảng"""
    if right and right.get("CLEAR"): 
        return {"messages": [], "search_ids": []}
        
    left_dict = left or {"messages": [], "search_ids": []}
    right_dict = right or {"messages": [], "search_ids": []}
    
    merged_msgs = left_dict.get("messages", []) + right_dict.get("messages", [])
    
    merged_ids = left_dict.get("search_ids", []) + right_dict.get("search_ids", [])
    unique_ids = list(dict.fromkeys(merged_ids)) 
    
    return {
        "messages": merged_msgs,
        "search_ids": unique_ids
    }

def merge_saved_flights(left: list, right: list) -> list:
    """Hàm gộp: Tránh lưu trùng lặp một chuyến bay nhiều lần vào giỏ hàng"""
    if right == ["CLEAR"]: return []
    combined = (left or []) + (right or [])
    unique_flights = {str(f.get("flightNumber")): f for f in combined if isinstance(f, dict)}
    return list(unique_flights.values())

class ChatState(TypedDict):
    user_message: str  
    tasks: List[Task] 
    node_results: Annotated[list[str], merge_list_with_clear]
    user_prefs: Annotated[Dict[str, Any], merge_dicts]
    language: str
    action: Optional[dict]     
    error_msg: Optional[str]
    response_text: str
    chat_history: Annotated[dict, merge_chat_history]
    saved_flights: Annotated[list[dict], merge_saved_flights]