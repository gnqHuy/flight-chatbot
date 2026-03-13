from datetime import datetime
from typing import Tuple, List, Dict
from app.core.constants import SUPPORTED_AIRLINES_SET

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

    error_msgs = []
    state_updates = {}

    if included and isinstance(included, list):
        unsupported = [air for air in included if air not in SUPPORTED_AIRLINES_SET and air != "CLEAR"]
        if unsupported:
            err_msg = f"[LỖI NGHIỆP VỤ]: Khách yêu cầu hãng ngoài luồng ({', '.join(unsupported)}). Hệ thống chỉ bán vé của Vietnam Airlines (VN), VietJet (VJ) và Bamboo Airways (QH)."
            error_msgs.append(err_msg)
            state_updates["includedAirlines"] = ["CLEAR"]

    missing_fields = []
    if not origin: missing_fields.append("ngày đi (origin)")
    if not destination: missing_fields.append("điểm đến (destination)")
    if not departureDate: missing_fields.append("ngày đi (departureDate)")

    if missing_fields:
        missing_str = ", ".join(missing_fields)
        error_msgs.append(f"[SLOT_FILLING_REQUIRED]: Khách chưa cung cấp đủ {missing_str}.")

    total_passengers = adults + children
    has_kids = (children > 0 or infants > 0)

    if has_kids and not pax_confirmed:
        error_msgs.append("[NEED_AGE_CONFIRMATION]: Cần xác nhận lại độ tuổi chính xác của bé để áp dụng giá vé ưu đãi nhất.")
    
    if total_passengers > 9:
        error_msgs.append("[PAX_LIMIT]: Hệ thống chỉ hỗ trợ đặt tối đa 9 khách có ghế. Vui lòng liên hệ bộ phận đoàn.")
    
    if infants > adults:
        error_msgs.append("[PAX_INVALID]: Số lượng trẻ sơ sinh (infants) không được vượt quá số lượng người lớn (adults).")
        state_updates["infants"] = 0 

    if is_roundtrip:
        if not returnDate or returnDate == "CLEAR":
            error_msgs.append(
                "[MISSING_RETURN_DATE]: Khách muốn bay khứ hồi nhưng chưa cung cấp ngày về."
            )

    if departureDate and returnDate and departureDate != "CLEAR" and returnDate != "CLEAR":
        try:
            dep_dt = datetime.strptime(departureDate, "%Y-%m-%d")
            today = datetime.now()
            
            if dep_dt.date() < today.date():
                error_msgs.append("[INVALID_DATE]: Ngày đi (departureDate) nằm trong quá khứ.")
                state_updates["departureDate"] = "CLEAR"
                
            if returnDate and returnDate != "CLEAR":
                ret_dt = datetime.strptime(returnDate, "%Y-%m-%d")
                if ret_dt.date() < dep_dt.date():
                    error_msgs.append("[INVALID_DATE]: Ngày về (returnDate) diễn ra trước ngày đi.")
                    state_updates["returnDate"] = "CLEAR"
                    
        except ValueError:
            error_msgs.append("[INVALID_FORMAT]: Định dạng ngày tháng không hợp lệ (phải là YYYY-MM-DD).")
            state_updates["departureDate"] = "CLEAR"
            if returnDate and returnDate != "CLEAR":
                state_updates["returnDate"] = "CLEAR"

    is_valid = len(error_msgs) == 0
    return is_valid, error_msgs, state_updates