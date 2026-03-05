import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional
from app.schemas.chat_state import Task

def merge_dicts(left: dict, right: dict) -> dict:
    """
    Hàm gộp dữ liệu: Giúp user_prefs nhớ được các tham số qua nhiều lượt hội thoại.
    Nếu lượt 1 có origin, lượt 2 có destination, hàm này sẽ gộp cả 2 lại.
    """
    if not left: return right or {}
    if not right: return left or {}
    merged = left.copy()
    merged.update({k: v for k, v in right.items() if v is not None})
    return merged

def merge_list_with_clear(left: list, right: list) -> list:
    """
    Hàm gộp dành riêng cho node_results (xử lý song song):
    - Nếu nhận được cờ ["CLEAR"], xóa trắng mảng (dùng khi bắt đầu lượt chat mới).
    - Ngược lại, cộng dồn kết quả như bình thường để không làm mất dữ liệu của các luồng song song.
    """
    if right == ["CLEAR"]:
        return []
    
    left_list = left or []
    right_list = right or []
    return left_list + right_list

class ChatState(TypedDict):
    user_message: str 
    sub_queries: List[str] 
    tasks: List[Task] 
    node_results: Annotated[list[str], merge_list_with_clear]
    user_prefs: Annotated[Dict[str, Any], merge_dicts]
    language: str
    action: Optional[dict]     
    error_msg: Optional[str]
    response_text: str         