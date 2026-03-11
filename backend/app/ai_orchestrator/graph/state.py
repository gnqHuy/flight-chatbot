from typing import TypedDict, Annotated, List, Dict, Any, Optional
from app.schemas.chat_state import Task

def merge_dicts(left: dict, right: dict) -> dict:
    if not left: return right or {}
    if not right: return left or {}
    merged = left.copy()
    for k, v in right.items():
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

def merge_chat_history(left: list, right: list) -> list:
    """
    Giữ lại tối đa 6 tin nhắn gần nhất (3 lượt chat).
    Nếu nhận cờ ["CLEAR"], xóa sạch lịch sử.
    """
    if right == ["CLEAR"]:
        return []
    
    combined = (left or []) + (right or [])
    return combined[-6:]

class ChatState(TypedDict):
    user_message: str  
    tasks: List[Task] 
    node_results: Annotated[list[str], merge_list_with_clear]
    user_prefs: Annotated[Dict[str, Any], merge_dicts]
    language: str
    action: Optional[dict]     
    error_msg: Optional[str]
    response_text: str
    chat_history: Annotated[list[str], merge_chat_history]