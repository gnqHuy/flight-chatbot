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