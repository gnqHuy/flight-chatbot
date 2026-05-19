"""
utils/flight_parser.py
Parse raw Duffel API offer → clean dict dùng trong toàn server.
Tất cả None-safe: không crash dù Duffel trả thiếu field.
"""
from datetime import datetime
import logging
import sys

logger = logging.getLogger(__name__)


def _safe_get(obj: dict, *keys, default=None):
    """Lấy nested key an toàn, không crash nếu giá trị là None."""
    for k in keys:
        if not isinstance(obj, dict):
            return default
        obj = obj.get(k)
        if obj is None:
            return default
    return obj


def _parse_duration(raw: str) -> str:
    """PT2H30M → 2h 30m"""
    if not raw:
        return "N/A"
    return raw.replace("PT", "").replace("H", "h ").replace("M", "m").lower().strip()


def _calc_layover(seg: dict, next_seg: dict) -> str | None:
    try:
        arr = datetime.strptime(seg["arriving_at"], "%Y-%m-%dT%H:%M:%S")
        dep = datetime.strptime(next_seg["departing_at"], "%Y-%m-%dT%H:%M:%S")
        mins = int((dep - arr).total_seconds() / 60)
        h, m = divmod(mins, 60)
        return f"{h}h {m}m" if h > 0 else f"{m}m"
    except Exception:
        return None


def format_duffel_offer(raw: dict) -> dict | None:
    """
    Parse 1 raw Duffel offer → clean flight dict.
    Trả None nếu lỗi nghiêm trọng (thiếu price).
    """
    try:
        grand_total = float(raw["total_amount"])
        base_price  = float(raw.get("base_amount") or 0)
        tax_fees    = float(raw.get("tax_amount")  or 0)
        currency    = raw.get("total_currency", "VND")

        last_ticketing     = _safe_get(raw, "payment_requirements", "payment_required_by", default="N/A")
        validating_airline = _safe_get(raw, "owner", "iata_code", default="UNKNOWN")

        # First slice/segment/passenger để lấy cabin + baggage
        first_slice   = (raw.get("slices") or [{}])[0]
        first_segment = (first_slice.get("segments") or [{}])[0]
        first_pax     = (first_segment.get("passengers") or [{}])[0]

        cabin       = (first_pax.get("cabin_class") or "ECONOMY").upper()
        fare_option = first_slice.get("fare_brand_name") or "STANDARD"

        baggages    = first_pax.get("baggages") or []
        checked_qty = sum(b.get("quantity", 0) for b in baggages if b.get("type") == "checked")
        carry_qty   = sum(b.get("quantity", 0) for b in baggages if b.get("type") == "carry_on")
        checked_str = f"{checked_qty} kiện" if checked_qty > 0 else "Không kèm ký gửi"
        carry_str   = f"{carry_qty} kiện"   if carry_qty   > 0 else "Không kèm xách tay"

        all_airlines: set[str] = set()
        parsed_itineraries = []

        for slc in (raw.get("slices") or []):
            segs = slc.get("segments") or []
            if not segs:
                continue

            first_seg = segs[0]
            last_seg  = segs[-1]

            # Flight number của slice (dùng segment đầu)
            mc_code   = _safe_get(first_seg, "marketing_carrier", "iata_code", default="XX")
            mc_num    = first_seg.get("marketing_carrier_flight_number") or ""
            slice_fn  = f"{mc_code}{mc_num}"

            detailed_segments = []
            for i, seg in enumerate(segs):
                carrier_code     = _safe_get(seg, "marketing_carrier", "iata_code", default="XX")
                operating_carrier = _safe_get(seg, "operating_carrier", "iata_code", default=carrier_code)
                all_airlines.add(carrier_code)

                seg_fn = f"{carrier_code}{seg.get('marketing_carrier_flight_number') or ''}"
                seg_pax = (seg.get("passengers") or [{}])[0]

                layover = _calc_layover(seg, segs[i + 1]) if i < len(segs) - 1 else None

                detailed_segments.append({
                    "carrierCode":      carrier_code,
                    "operatingCarrier": operating_carrier,
                    "isCodeshare":      carrier_code != operating_carrier,
                    "flightNumber":     seg_fn,
                    "aircraft":         _safe_get(seg, "aircraft", "iata_code", default="N/A"),
                    "duration":         _parse_duration(seg.get("duration") or ""),
                    "layoverTime":      layover,
                    "cabin":            (seg_pax.get("cabin_class") or cabin).upper(),
                    "bookingClass":     seg_pax.get("fare_basis_code") or "N/A",
                    "departure": {
                        "iata":     _safe_get(seg, "origin", "iata_code"),
                        "at":       seg.get("departing_at") or "N/A",
                        "terminal": seg.get("origin_terminal") or "N/A",
                    },
                    "arrival": {
                        "iata":     _safe_get(seg, "destination", "iata_code"),
                        "at":       seg.get("arriving_at") or "N/A",
                        "terminal": seg.get("destination_terminal") or "N/A",
                    },
                })

            parsed_itineraries.append({
                "flightNumber": slice_fn,
                "duration":     _parse_duration(slc.get("duration") or ""),
                "stops":        len(segs) - 1,
                "departure": {
                    "iata":     _safe_get(first_seg, "origin", "iata_code"),
                    "city":     _safe_get(first_seg, "origin", "city_name"),
                    "at":       first_seg.get("departing_at") or "N/A",
                    "terminal": first_seg.get("origin_terminal") or "N/A",
                },
                "arrival": {
                    "iata":     _safe_get(last_seg, "destination", "iata_code"),
                    "city":     _safe_get(last_seg, "destination", "city_name"),
                    "at":       last_seg.get("arriving_at") or "N/A",
                    "terminal": last_seg.get("destination_terminal") or "N/A",
                },
                "segmentDetails": detailed_segments,
            })

        return {
            "id":                 raw["id"],
            "price":              grand_total,
            "basePrice":          base_price,
            "taxAndFees":         tax_fees,
            "currency":           currency,
            "cabin":              cabin,
            "fareOption":         fare_option,
            "bookableSeats":      "N/A",
            "lastTicketingDate":  last_ticketing,
            "validatingAirline":  validating_airline,
            "checkedBaggage":     checked_str,
            "cabinBaggage":       carry_str,
            "airlines":           sorted(all_airlines),
            "itineraries":        parsed_itineraries,
        }

    except Exception as e:
        logger.warning(f"Lỗi parse offer: {e}", exc_info=True)
        return None
    
def build_search_summary(
    search_id: str,
    flights: list[dict],
    origin: str,
    destination: str,
    departureDate: str,
    roundTrip: bool = False,
    returnDate: str | None = None,
) -> str:
    cheapest = min(flights, key=lambda f: f.get("price", 9e9))

    non_stop = sum(
        1 for f in flights
        if all(it.get("stops", 1) == 0 for it in (f.get("itineraries") or []))
    )

    is_round_trip = bool(roundTrip and returnDate)
    trip_type = "round_trip" if is_round_trip else "one_way"

    summary = (
        f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]\n"
        f"search_id={search_id}\n"
        f"trip_type={trip_type}\n"
        f"total={len(flights)}\n"
        f"non_stop={non_stop}\n"
        f"cheapest_price={cheapest.get('price', 0):.0f} {cheapest.get('currency', 'VND')}\n"
        f"cheapest_airlines={', '.join(cheapest.get('airlines') or [])}\n"
        f"outbound={origin}→{destination} ngày {departureDate}"
    )

    if is_round_trip:
        summary += f"\ninbound={destination}→{origin} ngày {returnDate}"

    return summary