from datetime import datetime
from typing import Tuple, List, Dict
from app.core.constants import CURRENT_TIME, SUPPORTED_AIRLINES_SET, ContextTag, ValidationTag


def validate_flight_params(search_filters: dict) -> Tuple[bool, List[str], Dict]:
    origin        = search_filters.get("origin")
    destination   = search_filters.get("destination")
    departureDate = search_filters.get("departureDate")
    returnDate    = search_filters.get("returnDate")

    adults   = int(search_filters.get("adults")   or 1)
    children = int(search_filters.get("children") or 0)
    infants  = int(search_filters.get("infants")  or 0)

    need_age_confirmation = search_filters.get("need_age_confirmation", False)
    roundTrip             = search_filters.get("roundTrip", False)
    preferred_airlines    = search_filters.get("preferred_airlines") or []

    raw_errors, state_updates = [], {}

    missing = []
    if not origin:        missing.append("điểm đi (origin)")
    if not destination:   missing.append("điểm đến (destination)")
    if not departureDate: missing.append("ngày đi (departureDate)")
    if missing:
        raw_errors.append(f"Khách chưa cung cấp đủ {', '.join(missing)}.")

    total = adults + children + infants
    if adults < 1:
        raw_errors.append("Mỗi lượt tìm kiếm bắt buộc phải có ít nhất 1 người lớn.")
        state_updates["adults"] = 1
    if (children > 0 or infants > 0) and need_age_confirmation:
        raw_errors.append("Cần xác nhận lại độ tuổi chính xác của trẻ em.")
    if total > 9:
        raw_errors.append("Vượt quá số khách tối đa (9 người).")
    if infants > adults:
        raw_errors.append("Số trẻ sơ sinh không được vượt quá số người lớn.")
        state_updates["infants"] = 0
    if roundTrip and not returnDate:
        raw_errors.append("Khách muốn bay khứ hồi nhưng chưa cung cấp ngày về.")

    for airline in preferred_airlines:
        if airline and airline != "CLEAR" and airline not in SUPPORTED_AIRLINES_SET:
            return False, [f"{ValidationTag.INVALID_AIRLINE}:\n- '{airline}'"], {"preferred_airlines": "CLEAR"}

    if departureDate:
        try:
            dep_dt = datetime.strptime(departureDate, "%Y-%m-%d")
            today  = CURRENT_TIME
            if dep_dt.date() < today.date():
                raw_errors.append("Ngày đi nằm trong quá khứ.")
                state_updates["departureDate"] = "CLEAR"
            if returnDate:
                ret_dt = datetime.strptime(returnDate, "%Y-%m-%d")
                if ret_dt.date() < today.date():
                    raw_errors.append("Ngày về nằm trong quá khứ.")
                    state_updates["returnDate"] = "CLEAR"
                if ret_dt.date() < dep_dt.date():
                    raw_errors.append("Ngày về diễn ra trước ngày đi.")
                    state_updates["returnDate"] = "CLEAR"
        except ValueError:
            raw_errors.append("Định dạng ngày không hợp lệ (YYYY-MM-DD).")
            state_updates["departureDate"] = "CLEAR"
            if returnDate:
                state_updates["returnDate"] = "CLEAR"

    error_msgs = []
    if raw_errors:
        combined = f"{ContextTag.VALIDATION}:\n" + "\n".join(f"- {e}" for e in raw_errors)
        error_msgs.append(combined)

    return len(raw_errors) == 0, error_msgs, state_updates