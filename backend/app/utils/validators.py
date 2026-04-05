from datetime import datetime
from typing import Tuple, List, Dict
from app.core.constants import SUPPORTED_AIRLINES_SET, ContextTag

def validate_flight_params(user_prefs: dict) -> Tuple[bool, List[str], Dict]:
    """
    Kiểm tra tính hợp lệ của các tham số chuyến bay.
    """
    
    origin = user_prefs.get("origin")
    destination = user_prefs.get("destination")
    departureDate = user_prefs.get("departureDate")
    returnDate = user_prefs.get("returnDate")
    included = user_prefs.get("includedAirlines", [])
    
    adults = int(user_prefs.get("adults", 1))
    children = int(user_prefs.get("children", 0))
    infants = int(user_prefs.get("infants", 0))
    pax_confirmed = user_prefs.get("pax_confirmed", False)
    is_roundtrip = user_prefs.get("is_roundtrip", False)

    raw_errors = []
    state_updates = {}

    if included and isinstance(included, list):
        unsupported = [air for air in included if air not in SUPPORTED_AIRLINES_SET]
        if unsupported:
            raw_errors.append(f"Khách yêu cầu hãng ngoài luồng ({', '.join(unsupported)}). Hệ thống chỉ hỗ trợ VN, VJ, QH.")
            state_updates["includedAirlines"] = "CLEAR"

    missing_fields = []
    if not origin: missing_fields.append("điểm đi (origin)")
    if not destination: missing_fields.append("điểm đến (destination)")
    if not departureDate: missing_fields.append("ngày đi (departureDate)")

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        raw_errors.append(f"Khách chưa cung cấp đủ {missing_str}.")

    total_passengers = adults + children
    has_kids = (children > 0 or infants > 0)

    if adults < 1:
        raw_errors.append("Mỗi lượt tìm kiếm bắt buộc phải có ít nhất 1 người lớn.")
        state_updates["adults"] = 1 

    if has_kids and not pax_confirmed:
        raw_errors.append("Cần xác nhận lại độ tuổi chính xác của trẻ em để áp dụng giá vé ưu đãi nhất.")
    
    if total_passengers > 9:
        raw_errors.append("Vượt quá số khách. Hệ thống chỉ hỗ trợ đặt tối đa 9 khách có ghế. Vui lòng liên hệ bộ phận đoàn.")
    
    if infants > adults:
        raw_errors.append("Số lượng trẻ sơ sinh (infants) không được vượt quá số lượng người lớn (adults).")
        state_updates["infants"] = 0 

    if is_roundtrip and not returnDate:
        raw_errors.append("Khách muốn bay khứ hồi nhưng chưa cung cấp ngày về.")

    if departureDate: 
        try:
            dep_dt = datetime.strptime(departureDate, "%Y-%m-%d")
            today = datetime.now()
            
            if dep_dt.date() < today.date():
                raw_errors.append("Ngày đi (departureDate) nằm trong quá khứ.")
                state_updates["departureDate"] = "CLEAR"
                
            if returnDate:
                ret_dt = datetime.strptime(returnDate, "%Y-%m-%d")
                if ret_dt.date() < dep_dt.date():
                    raw_errors.append("Ngày về diễn ra trước ngày đi.")
                    state_updates["returnDate"] = "CLEAR"
                
        except ValueError:
            raw_errors.append("Định dạng ngày tháng không hợp lệ (phải là YYYY-MM-DD).")
            state_updates["departureDate"] = "CLEAR"
            if returnDate:
                state_updates["returnDate"] = "CLEAR"

    error_msgs = []
    
    if raw_errors:
        print(f"VALIDATION FAILED: {len(raw_errors)} errors found.")
        combined_error = f"{ContextTag.VALIDATION}:\n" + "\n".join([f"- {err}" for err in raw_errors])
        error_msgs.append(combined_error)

    is_valid = len(raw_errors) == 0
    return is_valid, error_msgs, state_updates