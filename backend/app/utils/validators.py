from datetime import datetime
from typing import Tuple, List, Dict

def validate_flight_params(user_prefs: dict) -> Tuple[bool, List[str], Dict]:
    """
    Kiểm tra tính hợp lệ của các tham số chuyến bay.
    Trả về: 
    - is_valid (bool): True nếu mọi thứ hợp lệ.
    - error_msgs (list): Danh sách log hệ thống (tiếng Anh) gửi cho LLM.
    - state_updates (dict): Các biến cần reset (gán None) để xóa khỏi user_prefs.
    """
    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    returnDate = user_prefs.get("returnDate")

    missing_fields = []
    if not origin: missing_fields.append("origin")
    if not destination: missing_fields.append("destination")
    if not departureDate: missing_fields.append("departureDate")

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        return False, [f"[SLOT_FILLING_REQUIRED]: {missing_str}"], {}

    try:
        dep_dt = datetime.strptime(departureDate, "%Y-%m-%d")
        today = datetime.now()
        
        if dep_dt.date() < today.date():
            return False, ["[INVALID_DATE]: departureDate is in the past."], {"departureDate": None}
            
        if returnDate:
            ret_dt = datetime.strptime(returnDate, "%Y-%m-%d")
            if ret_dt < dep_dt:
                return False, ["[INVALID_DATE]: returnDate is before departureDate."], {"returnDate": None}
                
    except ValueError:
        return False, ["[INVALID_FORMAT]: Date format is invalid."], {"departureDate": None, "returnDate": None}

    return True, [], {}