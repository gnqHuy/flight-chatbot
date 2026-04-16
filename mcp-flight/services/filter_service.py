"""
services/filter_service.py
Server-side filter và sort flight data.
Thay thế antipattern cũ: đẩy toàn bộ 200 vé sang FE rồi FE tự lọc.

Thiết kế: nhận flights list + filter params → trả filtered list.
FE nhận filtered_search_id, dùng nó để hiển thị — không cần tự lọc nữa.
"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def apply_filters(flights: list[dict], filters: dict) -> list[dict]:
    """
    Áp dụng tất cả filter conditions lên danh sách vé.

    Filters hỗ trợ:
    - maxPrice: int — giá tối đa (VND)
    - preferred_airlines: list[str] — chỉ lấy hãng này
    - nonStop: bool — chỉ lấy bay thẳng
    - travelClass: str — ECONOMY | BUSINESS | FIRST | PREMIUM_ECONOMY
    - start_hour: int — giờ khởi hành từ (0-23)
    - end_hour: int — giờ khởi hành đến (0-23)
    """
    result = flights

    # ── maxPrice ─────────────────────────────────────────────────────────────
    max_price = filters.get("maxPrice")
    if max_price is not None:
        try:
            cap = float(max_price)
            result = [f for f in result if f.get("price", 9e9) <= cap]
        except (TypeError, ValueError):
            logger.warning(f"maxPrice không hợp lệ: {max_price}")

    # ── preferred_airlines ────────────────────────────────────────────────────
    preferred = filters.get("preferred_airlines")
    if preferred and preferred != ["CLEAR"]:
        targets = {a.upper() for a in preferred if a and a != "CLEAR"}
        if targets:
            result = [
                f for f in result
                if any(al.upper() in targets for al in (f.get("airlines") or []))
            ]

    # ── nonStop ──────────────────────────────────────────────────────────────
    non_stop = filters.get("nonStop")
    if non_stop is True:
        result = [
            f for f in result
            if all(it.get("stops", 1) == 0 for it in (f.get("itineraries") or [{}]))
        ]

    # ── travelClass ──────────────────────────────────────────────────────────
    travel_class = filters.get("travelClass")
    if travel_class and travel_class != "CLEAR":
        tc = travel_class.upper() if isinstance(travel_class, str) else str(travel_class).upper()
        result = [f for f in result if (f.get("cabin") or "").upper() == tc]

    # ── giờ bay (start_hour / end_hour) ──────────────────────────────────────
    start_hour = filters.get("start_hour")
    end_hour   = filters.get("end_hour")
    if start_hour is not None or end_hour is not None:
        sh = int(start_hour) if start_hour is not None else 0
        eh = int(end_hour)   if end_hour   is not None else 23
        filtered_by_hour = []
        for f in result:
            its = f.get("itineraries") or []
            if not its:
                continue
            dep_at = (its[0].get("departure") or {}).get("at", "")
            try:
                hour = datetime.fromisoformat(dep_at).hour
                if sh <= hour <= eh:
                    filtered_by_hour.append(f)
            except Exception:
                # Nếu parse fail, giữ lại vé
                filtered_by_hour.append(f)
        result = filtered_by_hour

    logger.info(f"[Filter] {len(flights)} → {len(result)} vé sau khi lọc")
    return result


def apply_sort(flights: list[dict], sort_preference: str | None) -> list[dict]:
    """
    Sắp xếp danh sách vé.

    sort_preference:
    - "price_asc":       giá tăng dần
    - "price_desc":      giá giảm dần
    - "departure_time":  giờ khởi hành sớm nhất
    - "arrival_time":    giờ hạ cánh sớm nhất
    - None:              giữ nguyên thứ tự (mặc định price_asc)
    """
    if not sort_preference or sort_preference == "price_asc":
        return sorted(flights, key=lambda f: f.get("price", 9e9))

    if sort_preference == "price_desc":
        return sorted(flights, key=lambda f: f.get("price", 0), reverse=True)

    if sort_preference == "departure_time":
        def dep_key(f):
            try:
                its = f.get("itineraries") or []
                at  = (its[0].get("departure") or {}).get("at", "")
                return datetime.fromisoformat(at)
            except Exception:
                return datetime.max
        return sorted(flights, key=dep_key)

    if sort_preference == "arrival_time":
        def arr_key(f):
            try:
                its = f.get("itineraries") or []
                at  = (its[-1].get("arrival") or {}).get("at", "")
                return datetime.fromisoformat(at)
            except Exception:
                return datetime.max
        return sorted(flights, key=arr_key)

    logger.warning(f"[Sort] Unknown sort_preference: {sort_preference}, dùng price_asc")
    return sorted(flights, key=lambda f: f.get("price", 9e9))


def filter_and_sort(flights: list[dict], filters: dict) -> list[dict]:
    """Convenience: filter rồi sort."""
    filtered = apply_filters(flights, filters)
    return apply_sort(filtered, filters.get("sort_preference"))


def build_filter_summary(original_count: int, filtered: list[dict], filters: dict) -> str:
    """Tạo summary text cho LLM biết filter đã làm gì."""
    result_count = len(filtered)
    parts = [f"Đã áp dụng bộ lọc: {original_count} → {result_count} vé."]

    if filters.get("maxPrice"):
        parts.append(f"Giá tối đa: {filters['maxPrice']:,} VND.")
    if filters.get("preferred_airlines"):
        parts.append(f"Hãng: {', '.join(filters['preferred_airlines'])}.")
    if filters.get("nonStop"):
        parts.append("Chỉ bay thẳng.")
    if filters.get("travelClass"):
        parts.append(f"Hạng ghế: {filters['travelClass']}.")
    if filters.get("start_hour") is not None or filters.get("end_hour") is not None:
        sh = filters.get("start_hour", 0)
        eh = filters.get("end_hour", 23)
        parts.append(f"Giờ bay: {sh}h–{eh}h.")

    sort_pref = filters.get("sort_preference")
    sort_labels = {
        "price_asc":      "giá tăng dần",
        "price_desc":     "giá giảm dần",
        "departure_time": "giờ khởi hành",
        "arrival_time":   "giờ hạ cánh",
    }
    if sort_pref and sort_pref in sort_labels:
        parts.append(f"Sắp xếp theo: {sort_labels[sort_pref]}.")

    if result_count == 0:
        parts.append("Không có vé nào khớp với bộ lọc.")
    elif filtered:
        cheapest = min(filtered, key=lambda f: f.get("price", 9e9))
        parts.append(
            f"Rẻ nhất sau lọc: {cheapest.get('price', 0):,.0f} {cheapest.get('currency', 'VND')} "
            f"({', '.join(cheapest.get('airlines') or [])})."
        )

    return " ".join(parts)