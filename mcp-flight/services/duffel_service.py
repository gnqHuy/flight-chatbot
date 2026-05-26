"""
services/duffel_service.py
Gọi Duffel API → trả về list flight dicts đã parse.
Hoàn toàn độc lập, không import từ backend.
"""
import os
import json
import logging
import httpx
from utils.flight_parser import format_duffel_offer

logger = logging.getLogger(__name__)

DUFFEL_TOKEN   = os.getenv("DUFFEL_ACCESS_TOKEN", "")
DUFFEL_URL     = "https://api.duffel.com/air/offer_requests?return_offers=true"
DUFFEL_HEADERS = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
    "Duffel-Version": "v2",
}
SUPPORTED_AIRLINES = {"VN", "VJ", "QH"}


def _build_payload(params: dict) -> dict:
    """Chuyển search_filters dict → Duffel API payload."""
    origin        = params["origin"]
    destination   = params["destination"]
    departure_date = params["departureDate"]
    return_date   = params.get("returnDate")
    round_trip    = params.get("roundTrip", False)
    travel_class  = params.get("travelClass")

    slices = [{"origin": origin, "destination": destination, "departure_date": departure_date}]
    if round_trip and return_date:
        slices.append({"origin": destination, "destination": origin, "departure_date": return_date})

    passengers = []
    for _ in range(max(1, int(params.get("adults") or 1))):
        passengers.append({"type": "adult"})
    for _ in range(int(params.get("children") or 0)):
        passengers.append({"type": "child"})
    for _ in range(int(params.get("infants") or 0)):
        passengers.append({"type": "infant_without_seat"})

    payload: dict = {"slices": slices, "passengers": passengers}

    if travel_class:
        tc = travel_class.upper() if isinstance(travel_class, str) else str(travel_class).upper()
        cabin_map = {
            "ECONOMY": "economy", "PREMIUM_ECONOMY": "premium_economy",
            "BUSINESS": "business", "FIRST": "first",
        }
        cabin = cabin_map.get(tc)
        if cabin:
            payload["cabin_class"] = cabin

    return {"data": payload}


async def search_flights_async(params: dict, max_offers: int = 200) -> list[dict]:
    """
    Async call đến Duffel API.
    Trả về list flight dicts đã parse, lọc theo SUPPORTED_AIRLINES.
    """
    payload = _build_payload(params)
    logger.info(f"[Duffel] Calling API: {params.get('origin')}→{params.get('destination')} {params.get('departureDate')}")
    logger.debug(f"[Duffel] Payload: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            DUFFEL_URL,
            json=payload,
            headers={**DUFFEL_HEADERS, "Authorization": f"Bearer {DUFFEL_TOKEN}"},
        )
        resp.raise_for_status()

    raw_offers = resp.json().get("data", {}).get("offers", [])
    logger.info(f"[Duffel] Got {len(raw_offers)} raw offers")

    # Lọc chỉ lấy hãng hỗ trợ
    filtered = [
        o for o in raw_offers
        if (o.get("owner") or {}).get("iata_code", "").upper() in SUPPORTED_AIRLINES
    ]

    # Thêm lọc preferred_airlines nếu có
    preferred = {a.upper() for a in (params.get("preferred_airlines") or []) if a != "CLEAR"}
    if preferred:
        filtered = [
            o for o in filtered
            if (o.get("owner") or {}).get("iata_code", "").upper() in preferred
        ]

    filtered = filtered[:max_offers]

    parsed = []
    for raw in filtered:
        flight = format_duffel_offer(raw)
        if flight:
            parsed.append(flight)

    logger.info(f"[Duffel] Parsed {len(parsed)} flights after filter")
    return parsed