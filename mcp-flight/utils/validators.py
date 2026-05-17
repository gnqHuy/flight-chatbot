"""
utils/validators.py
Validate search params trước khi gọi Duffel API.
"""
from datetime import datetime

from utils.time_utils import get_current_time

SUPPORTED_AIRLINES = {"VN", "VJ", "QH"}


def validate_search_params(params: dict) -> tuple[bool, list[str], dict]:
    """
    Trả về (is_valid, error_messages, state_updates).
    state_updates: các field cần reset về CLEAR khi invalid.
    """
    errors: list[str] = []
    updates: dict     = {}

    origin         = params.get("origin")
    destination    = params.get("destination")
    departure_date = params.get("departureDate")
    return_date    = params.get("returnDate")
    round_trip     = params.get("roundTrip", False)
    preferred      = params.get("preferred_airlines") or []

    try:
        adults   = int(params.get("adults")   if params.get("adults")   is not None else 1)
        children = int(params.get("children") if params.get("children") is not None else 0)
        infants  = int(params.get("infants")  if params.get("infants")  is not None else 0)
    except (TypeError, ValueError):
        errors.append("Số lượng hành khách không hợp lệ.")
        return False, errors, updates

    need_age = params.get("need_age_confirmation", False)

    # ── Bắt buộc ─────────────────────────────────────────────────────────────
    missing = []
    if not origin:         missing.append("điểm đi (origin)")
    if not destination:    missing.append("điểm đến (destination)")
    if not departure_date: missing.append("ngày đi (departureDate)")
    if missing:
        errors.append(f"Chưa đủ thông tin: {', '.join(missing)}.")

    # ── Hành khách ────────────────────────────────────────────────────────────
    total = adults + children + infants

    if adults < 1:
        errors.append("Cần ít nhất 1 người lớn.")
        updates["adults"] = 1

    if (children > 0 or infants > 0) and need_age:
        errors.append("Cần xác nhận độ tuổi chính xác của trẻ em.")

    if total > 9:
        errors.append("Tối đa 9 hành khách mỗi lần tìm kiếm.")

    if infants > adults:
        errors.append("Số trẻ sơ sinh không được vượt quá số người lớn.")
        updates["infants"] = 0

    # ── Khứ hồi ──────────────────────────────────────────────────────────────
    if round_trip and not return_date:
        errors.append("Vé khứ hồi cần có ngày về.")

    # ── Hãng bay ─────────────────────────────────────────────────────────────
    for al in preferred:
        if al and al != "CLEAR" and al.upper() not in SUPPORTED_AIRLINES:
            return False, [
                f"[HÃNG KHÔNG HỖ TRỢ]: '{al}'. Hệ thống chỉ hỗ trợ VN, VJ, QH."
            ], {"preferred_airlines": "CLEAR"}

    # ── Ngày tháng ───────────────────────────────────────────────────────────
    if departure_date:
        try:
            dep_dt = datetime.strptime(departure_date, "%Y-%m-%d")
            today  = get_current_time()
            if dep_dt.date() < today.date():
                errors.append("Ngày đi đã qua.")
                updates["departureDate"] = "CLEAR"
            if return_date:
                ret_dt = datetime.strptime(return_date, "%Y-%m-%d")
                if ret_dt.date() < today.date():
                    errors.append("Ngày về đã qua.")
                    updates["returnDate"] = "CLEAR"
                if ret_dt.date() < dep_dt.date():
                    errors.append("Ngày về không được trước ngày đi.")
                    updates["returnDate"] = "CLEAR"
        except ValueError:
            errors.append("Định dạng ngày không hợp lệ (YYYY-MM-DD).")
            updates["departureDate"] = "CLEAR"
            if return_date:
                updates["returnDate"] = "CLEAR"

    return len(errors) == 0, errors, updates


def validate_filter_params(params: dict) -> tuple[bool, list[str]]:
    """Validate filter/sort params."""
    errors: list[str] = []

    max_price = params.get("maxPrice")
    if max_price is not None:
        try:
            if int(max_price) < 0:
                errors.append("maxPrice phải >= 0.")
        except (TypeError, ValueError):
            errors.append("maxPrice phải là số nguyên.")

    start_hour = params.get("start_hour")
    end_hour   = params.get("end_hour")
    if start_hour is not None and end_hour is not None:
        try:
            if not (0 <= int(start_hour) <= 23) or not (0 <= int(end_hour) <= 23):
                errors.append("start_hour và end_hour phải trong khoảng 0–23.")
            if int(start_hour) > int(end_hour):
                errors.append("start_hour không được lớn hơn end_hour.")
        except (TypeError, ValueError):
            errors.append("start_hour và end_hour phải là số nguyên.")

    sort = params.get("sort_preference")
    valid_sorts = {"price_asc", "price_desc", "departure_time", "arrival_time", None}
    if sort not in valid_sorts:
        errors.append(f"sort_preference không hợp lệ: '{sort}'.")

    return len(errors) == 0, errors