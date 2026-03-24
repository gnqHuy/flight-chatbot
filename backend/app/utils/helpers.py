from typing import Optional

def consume_task(tasks: list, expected_intents: str | list) -> list:
    """
    Kiểm tra task đầu tiên trong danh sách.
    Nếu đúng là nhiệm vụ của Node hiện tại (nằm trong expected_intents), thì "nuốt" nó (xóa đi).
    Nếu không phải, giữ nguyên danh sách để Router xử lý tiếp.
    """
    if not tasks:
        return []
    
    if isinstance(expected_intents, str):
        expected_intents = [expected_intents]
        
    current_task = tasks[0]
    
    intent_val = current_task.intent.value if hasattr(current_task.intent, 'value') else str(current_task.intent)
    
    if intent_val in expected_intents:
        return tasks[1:]
        
    return tasks.copy()

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

def merge_search_id(left: Optional[str], right: Optional[str]) -> Optional[str]:
    if right == "CLEAR":
        return None
    return right if right is not None else left

def merge_node_results(left: list, right: list) -> list:
    """Hàm gộp node_results: Nếu nhận được cờ CLEAR thì xóa sạch, ngược lại thì cộng dồn"""
    if right == ["CLEAR"]: 
        return []
    return (left or []) + (right or [])