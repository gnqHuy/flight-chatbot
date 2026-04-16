"""
utils/flight_analysis.py
Format flight data → structured text cho LLM.
Thay thế LangChain tool wrapper bằng pure Python function.
"""
from datetime import datetime


def _fmt_price(p) -> str:
    try:
        v = float(p)
        return f"{v:,.0f}" if v == int(v) else f"{v:,.2f}".rstrip("0").rstrip(".")
    except Exception:
        return str(p)


def _fmt_dt(dt_str: str) -> str:
    """2026-03-15T05:30:00 → 05:30 15/03/2026"""
    if not dt_str or dt_str == "N/A":
        return "N/A"
    try:
        return datetime.fromisoformat(dt_str).strftime("%H:%M %d/%m/%Y")
    except Exception:
        return dt_str


def format_flights_to_text(flights: list[dict]) -> str:
    """
    Biến danh sách vé đã parse → chuỗi văn bản structured cho LLM phân tích.
    Mỗi vé có đầy đủ: giá, hành lý, hành trình, chi tiết chặng.
    """
    if not flights:
        return "Không có dữ liệu chuyến bay."

    parts = []
    for idx, f in enumerate(flights, 1):
        try:
            currency = f.get("currency") or "VND"
            airlines = f.get("airlines") or []

            lines = [
                f"=== VÉ {idx}: {', '.join(airlines)} ===",
                f"Giá tổng: {_fmt_price(f.get('price', 0))} {currency}"
                f" (Giá gốc: {_fmt_price(f.get('basePrice', 0))} | Thuế/Phí: {_fmt_price(f.get('taxAndFees', 0))})",
                f"Hạng ghế: {f.get('cabin') or 'N/A'} | Gói vé: {f.get('fareOption') or 'N/A'}",
                f"Hành lý xách tay: {f.get('cabinBaggage') or 'N/A'} | Ký gửi: {f.get('checkedBaggage') or 'N/A'}",
                f"Hạn xuất vé: {f.get('lastTicketingDate') or 'N/A'}",
            ]

            for it_idx, it in enumerate(f.get("itineraries") or []):
                direction = "Chiều đi" if it_idx == 0 else "Chiều về"
                dep = it.get("departure") or {}
                arr = it.get("arrival")   or {}
                lines.append(
                    f"\n[{direction}] {dep.get('city') or dep.get('iata') or 'N/A'}"
                    f" → {arr.get('city') or arr.get('iata') or 'N/A'}"
                )
                lines.append(
                    f"  Chuyến: {it.get('flightNumber') or 'N/A'} | "
                    f"Thời gian: {it.get('duration') or 'N/A'} | "
                    f"Điểm dừng: {it.get('stops', 0)}"
                )

                for s_idx, seg in enumerate(it.get("segmentDetails") or []):
                    s_dep = seg.get("departure") or {}
                    s_arr = seg.get("arrival")   or {}
                    op_str = (
                        f" ⚠️ Khai thác bởi: {seg.get('operatingCarrier')}"
                        if seg.get("isCodeshare") else ""
                    )
                    lines.append(
                        f"  Chặng {s_idx+1}: {s_dep.get('iata')} → {s_arr.get('iata')}"
                        f" | {seg.get('flightNumber')}{op_str}"
                    )
                    lines.append(
                        f"    Khởi hành: {_fmt_dt(s_dep.get('at'))} (Terminal {s_dep.get('terminal') or 'N/A'})"
                    )
                    lines.append(
                        f"    Hạ cánh:   {_fmt_dt(s_arr.get('at'))} (Terminal {s_arr.get('terminal') or 'N/A'})"
                    )
                    lines.append(
                        f"    Bay: {seg.get('duration') or 'N/A'} | Máy bay: {seg.get('aircraft') or 'N/A'} | Hạng: {seg.get('cabin') or 'N/A'}"
                    )
                    if seg.get("layoverTime"):
                        lines.append(f"    ⏳ Trung chuyển tại {s_arr.get('iata')}: {seg['layoverTime']}")

            parts.append("\n".join(lines))
        except Exception as e:
            parts.append(f"=== LỖI VÉ {idx} ===\n{e}")

    return "\n\n".join(parts)


def build_analysis_context(
    flights: list[dict],
    airline_db_info: str = "",
    target_flights: list[str] | None = None,
    target_airlines: list[str] | None = None,
) -> str:
    """
    Build structured analysis context cho LLM — thay thế antipattern cũ
    (dump raw data và để LLM tự phân tích).

    - Nếu target_flights: lọc các vé theo mã chuyến, format chi tiết.
    - Nếu target_airlines: lọc theo hãng, format chi tiết + thêm DB info.
    - Nếu cả hai: làm cả hai.
    """
    sections: list[str] = []

    # Lọc theo airlines
    if target_airlines:
        airline_flights = [
            f for f in flights
            if any(al.upper() in (target_airlines or []) for al in (f.get("airlines") or []))
        ]
        if airline_flights:
            # Lấy 1 vé rẻ nhất mỗi hãng làm ví dụ
            seen: set[str] = set()
            examples: list[dict] = []
            for f in sorted(airline_flights, key=lambda x: x.get("price", 999999)):
                key = "_".join(sorted(f.get("airlines") or []))
                if key not in seen:
                    seen.add(key)
                    examples.append(f)
            sections.append(
                "[VÉ MINH HỌA CỦA CÁC HÃNG]\n" + format_flights_to_text(examples)
            )

        if airline_db_info:
            sections.append("[THÔNG TIN HÃNG BAY TỪ HỆ THỐNG]\n" + airline_db_info)

    # Lọc theo flight numbers
    if target_flights:
        targets_upper = {fn.strip().upper().replace(" ", "").replace("-", "") for fn in target_flights}
        matched: list[dict] = []
        for f in flights:
            for it in (f.get("itineraries") or []):
                fn = (it.get("flightNumber") or "").strip().upper().replace(" ", "")
                if fn in targets_upper:
                    matched.append(f)
                    break
        if matched:
            sections.append(
                f"[CHI TIẾT CÁC CHUYẾN BAY: {', '.join(target_flights)}]\n"
                + format_flights_to_text(matched)
            )
        else:
            sections.append(
                f"[KHÔNG TÌM THẤY]: Không có dữ liệu cho mã chuyến {target_flights}. "
                f"(Hệ thống có {len(flights)} vé)"
            )

    # Không có target cụ thể — trả summary tổng quan
    if not target_flights and not target_airlines:
        total      = len(flights)
        cheapest   = min(flights, key=lambda x: x.get("price", 9e9), default=None)
        fastest    = None
        for f in flights:
            for it in (f.get("itineraries") or []):
                if it.get("stops", 1) == 0:
                    if fastest is None or f.get("price", 9e9) < fastest.get("price", 9e9):
                        fastest = f

        lines = [f"[TÓM TẮT: {total} chuyến bay tìm được]"]
        if cheapest:
            lines.append(
                f"Rẻ nhất: {_fmt_price(cheapest['price'])} {cheapest.get('currency', 'VND')} "
                f"({', '.join(cheapest.get('airlines') or [])})"
            )
        if fastest and fastest != cheapest:
            lines.append(
                f"Bay thẳng rẻ nhất: {_fmt_price(fastest['price'])} {fastest.get('currency', 'VND')} "
                f"({', '.join(fastest.get('airlines') or [])})"
            )
        sections.append("\n".join(lines))

    return "\n\n".join(sections)