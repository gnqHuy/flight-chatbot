from datetime import datetime
from typing import Tuple, List, Dict
from app.core.constants import CURRENT_TIME, SUPPORTED_AIRLINES_SET, ContextTag

def validate_flight_params(search_filters: dict) -> Tuple[bool, List[str], Dict]:
    """
    Kiểm tra tính hợp lệ của các tham số chuyến bay.
    """
    
    origin = search_filters.get("origin")
    destination = search_filters.get("destination")
    departureDate = search_filters.get("departureDate")
    returnDate = search_filters.get("returnDate")
    
    adults = int(search_filters.get("adults", 1))
    children = int(search_filters.get("children", 0))
    infants = int(search_filters.get("infants", 0))
    need_age_confirmation = search_filters.get("need_age_confirmation", False)
    roundTrip = search_filters.get("roundTrip", False)
    preferred_airlines = search_filters.get("preferred_airlines", [])

    raw_errors = []
    state_updates = {}

    missing_fields = []
    if not origin: missing_fields.append("điểm đi (origin)")
    if not destination: missing_fields.append("điểm đến (destination)")
    if not departureDate: missing_fields.append("ngày đi (departureDate)")

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        raw_errors.append(f"Khách chưa cung cấp đủ {missing_str}.")

    total_passengers = adults + children + infants
    has_kids = (children > 0 or infants > 0)

    if adults < 1:
        raw_errors.append("Mỗi lượt tìm kiếm bắt buộc phải có ít nhất 1 người lớn.")
        state_updates["adults"] = 1 

    if has_kids and need_age_confirmation:
        raw_errors.append("Cần xác nhận lại độ tuổi chính xác của trẻ em để áp dụng giá vé ưu đãi nhất.")
    
    if total_passengers > 9:
        raw_errors.append("Vượt quá số khách. Hệ thống chỉ hỗ trợ đặt tối đa 9 khách có ghế. Vui lòng liên hệ bộ phận đoàn.")
    
    if infants > adults:
        raw_errors.append("Số lượng trẻ sơ sinh (infants) không được vượt quá số lượng người lớn (adults).")
        state_updates["infants"] = 0 

    if roundTrip and not returnDate:
        raw_errors.append("Khách muốn bay khứ hồi nhưng chưa cung cấp ngày về.")
    
    for airline in preferred_airlines:
        if airline not in SUPPORTED_AIRLINES_SET:
            return False, [f"{ContextTag.INVALID_AIRLINE}:\n- '{airline}'"], {"preferred_airlines": "CLEAR"}

    if departureDate: 
        try:
            dep_dt = datetime.strptime(departureDate, "%Y-%m-%d")
            today = CURRENT_TIME
            
            if dep_dt.date() < today.date():
                raw_errors.append("Ngày đi (departureDate) nằm trong quá khứ.")
                state_updates["departureDate"] = "CLEAR"
                
            if returnDate:
                ret_dt = datetime.strptime(returnDate, "%Y-%m-%d")
                if ret_dt.date() < today.date():
                    raw_errors.append("Ngày về (returnDate) nằm trong quá khứ.")
                    state_updates["returnDate"] = "CLEAR"
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