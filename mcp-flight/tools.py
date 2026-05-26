# mcp-flight/tools.py
import json
from core import mcp, logger, _META_TTL
from utils.cache_manager import same_core_params, recover_cache

from services.duffel_service import search_flights_async
from services.redis_service import save_flights, load_flights, exists, save_raw, load_raw
from services.filter_service import filter_and_sort, build_filter_summary
from utils.flight_parser import build_search_summary
from utils.validators import is_round_trip_offer, validate_search_params, validate_filter_params
from utils.flight_analysis import build_analysis_context

@mcp.tool()
async def search_flights(
    origin: str,
    destination: str,
    departureDate: str,
    roundTrip: bool = False,
    returnDate: str | None = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    travelClass: str | None = None,
    preferred_airlines: list[str] | None = None,
    current_search_id: str | None = None,
) -> str:
    """Tìm chuyến bay từ Duffel API. MCP tự quyết dùng cache hay gọi mới."""
    logger.info(
        f"[search_flights] CALL {origin}→{destination} {departureDate} "
        f"roundTrip={roundTrip} returnDate={returnDate} "
        f"adults={adults} children={children} infants={infants} "
        f"current_search_id={current_search_id}"
    )

    params = {
        "origin": origin,
        "destination": destination,
        "departureDate": departureDate,
        "roundTrip": roundTrip,
        "returnDate": returnDate,
        "adults": adults,
        "children": children,
        "infants": infants,
        "travelClass": travelClass,
        "preferred_airlines": preferred_airlines or [],
    }

    is_valid, errors, _ = validate_search_params(params)
    if not is_valid:
        return "[THÔNG TIN ĐẶT VÉ CẦN KHÁCH KIỂM TRA LẠI]:\n" + "\n".join(f"- {e}" for e in errors)

    # Cache check
    if current_search_id and current_search_id != "CLEAR":
        meta_raw = load_raw(f"{current_search_id}:meta")
        data_alive = exists(current_search_id)

        if meta_raw and data_alive:
            try:
                meta = json.loads(meta_raw)

                if same_core_params(params, meta):
                    flights = load_flights(current_search_id)

                    if flights:
                        save_flights(flights, prefix="search", override_key=current_search_id)
                        save_raw(f"{current_search_id}:meta", meta_raw, ttl=_META_TTL)

                        logger.info(f"[search_flights] CACHE HIT — {len(flights)} vé. TTL reset.")

                        return build_search_summary(
                            search_id=current_search_id,
                            flights=flights,
                            origin=origin,
                            destination=destination,
                            departureDate=departureDate,
                            roundTrip=roundTrip,
                            returnDate=returnDate,
                        )

            except Exception as e:
                logger.warning(f"[search_flights] Lỗi parse meta: {e} — gọi Duffel")

    logger.info(f"[search_flights] Gọi Duffel API: {origin}→{destination} {departureDate}")

    try:
        flights = await search_flights_async(params, max_offers=200)
    except Exception as e:
        return f"[TRỤC TRẶC HỆ THỐNG]: Không thể kết nối với hãng hàng không. Chi tiết: {str(e)}"

    if not flights:
        return f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Không có chuyến bay VN/VJ/QH nào cho {origin}→{destination} ngày {departureDate}."

    if roundTrip and returnDate:
        round_trip_flights = [
            f for f in flights
            if is_round_trip_offer(f, origin, destination, returnDate)
        ]

        if not round_trip_flights:
            return (
                "[DỮ LIỆU CHUYẾN BAY KHÔNG ĐẦY ĐỦ]\n"
                f"Yêu cầu là vé khứ hồi {origin}→{destination} ngày {departureDate}, "
                f"về ngày {returnDate}.\n"
                f"Hệ thống nhận được {len(flights)} offer nhưng chưa có offer nào đủ "
                "chiều đi và chiều về hợp lệ.\n"
                "Vui lòng kiểm tra lại phần tạo request hoặc parse dữ liệu từ Duffel."
            )

        flights = round_trip_flights

    search_id = save_flights(flights, prefix="search")
    save_raw(f"{search_id}:meta", json.dumps(params), ttl=_META_TTL)

    return build_search_summary(
        search_id=search_id,
        flights=flights,
        origin=origin,
        destination=destination,
        departureDate=departureDate,
        roundTrip=roundTrip,
        returnDate=returnDate,
    )

@mcp.tool()
async def get_filtered_flights(search_id: str, maxPrice: int | None = None, preferred_airlines: list[str] | None = None,
                               nonStop: bool | None = None, travelClass: str | None = None, start_hour: int | None = None,
                               end_hour: int | None = None, sort_preference: str | None = None) -> str:
    """Lọc và sắp xếp vé server-side. Tự động recover cache nếu hết hạn."""
    flights = load_flights(search_id)
    if not flights:
        flights = await recover_cache(search_id)
        if not flights:
            return "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể khôi phục tự động. Vui lòng tìm vé lại nhé."

    filters = {k: v for k, v in {"maxPrice": maxPrice, "preferred_airlines": preferred_airlines, "nonStop": nonStop,
                                 "travelClass": travelClass, "start_hour": start_hour, "end_hour": end_hour, "sort_preference": sort_preference}.items() if v is not None}
    
    is_valid, errors = validate_filter_params(filters)
    if not is_valid:
        return "[BỘ LỌC KHÔNG HỢP LỆ]:\n" + "\n".join(f"- {e}" for e in errors)

    original_count = len(flights)
    filtered = filter_and_sort(flights, filters)
    summary = build_filter_summary(original_count, filtered, filters)
    filtered_id = save_flights(filtered, prefix="filtered") if filtered else None

    return f"[BỘ LỌC ĐƯỢC ÁP DỤNG]\nfiltered_id={filtered_id or 'NONE'}\noriginal_count={original_count}\nfiltered_count={len(filtered)}\nsummary={summary}"

@mcp.tool()
async def analyze_flights(
    current_search_id: str, 
    compare_flights: list[str] | None = None, 
    compare_airlines: list[str] | None = None
) -> str:
    """Build structured analysis context cho LLM. Tự động recover cache nếu hết hạn."""
    flights = load_flights(current_search_id)
    if not flights:
        flights = await recover_cache(current_search_id)
        if not flights:
            return "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể khôi phục tự động. Vui lòng tìm vé lại nhé."

    offer_ids = []
    flight_nums = []
    if compare_flights:
        for item in compare_flights:
            if str(item).startswith("off_"):
                offer_ids.append(item)
            else:
                flight_nums.append(item)

    context = build_analysis_context(
        flights=flights, 
        target_flights=flight_nums if flight_nums else None,
        target_airlines=([c.upper() for c in compare_airlines if c] if compare_airlines else None),
        target_offer_ids=offer_ids if offer_ids else None
    )
    return f"[DỮ LIỆU SO SÁNH CHUYẾN BAY]\n{context}"