import json
import os
from typing import Optional

from typing import Union, List

from typing import Union

def consume_task(tasks: list, expected_intents: Union[str, list], next_task=None) -> list:
    """
    Tìm và "nuốt" (xóa) task ĐẦU TIÊN trong hàng đợi khớp với expected_intents (Bất kể vị trí nào).
    Nếu không tìm thấy, giữ nguyên danh sách.
    ĐẶC BIỆT: Nếu có next_task (Dùng cho Fallback), chèn nó vào vị trí ưu tiên cao nhất (index 0).
    """
    if not tasks:
        remaining_tasks = []
    else:
        if isinstance(expected_intents, str):
            expected_intents = [expected_intents]
            
        remaining_tasks = tasks.copy()
        
        for i, task in enumerate(remaining_tasks):
            intent_val = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
            
            if intent_val in expected_intents:
                remaining_tasks.pop(i)
                break
            
    if next_task:
        remaining_tasks.insert(0, next_task)
        
    return remaining_tasks

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

def overwrite_dict(left: dict, right: dict) -> dict:
    if not right:
        return {}
    return right


def load_test_cases(file_path: str):
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def evaluate_turn_with_llm(judge_chain, user_query, exp_behavior, exp_intent, actual_intent, bot_action, bot_response) -> dict:
    try:
        safe_data = {
            "user_query": str(user_query or "None"),
            "expected_behavior": str(exp_behavior or "None"),
            "expected_intent": str(exp_intent or "None"),
            "actual_intent": str(actual_intent or "None"),
            "bot_action": json.dumps(bot_action, ensure_ascii=False) if bot_action else "None",
            "bot_response": "\n".join([str(x) for x in bot_response]) if isinstance(bot_response, list) else str(bot_response or "None")
        }
        result = judge_chain.invoke(safe_data)
        return {"score": result.score, "reason": result.reason}
    except Exception as e:
        return {"score": 0, "reason": f"Lỗi chấm điểm lượt: {str(e)}"}

def evaluate_scenario_with_llm(scenario_judge_chain, description, conversation_history) -> dict:
    try:
        result = scenario_judge_chain.invoke({"description": description, "conversation_history": conversation_history})
        return {"scenario_score": result.scenario_score, "scenario_reason": result.scenario_reason}
    except Exception as e:
        return {"scenario_score": 0, "scenario_reason": f"Lỗi chấm điểm kịch bản: {str(e)}"}