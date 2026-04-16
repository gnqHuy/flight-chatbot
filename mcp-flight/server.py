"""
mcp-flight/server.py

MCP Flight Server — 3 tools chính:
  1. search_flights        → gọi Duffel, save Redis, trả search_id
  2. get_filtered_flights  → filter/sort server-side, trả filtered_id + summary
  3. analyze_flights       → build structured analysis context cho LLM

Transport: SSE (FastMCP), port 8001.
Hoàn toàn độc lập với backend — không import từ app/.
"""
import os
import sys
import logging
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from services.duffel_service  import search_flights_async
from services.redis_service   import save_flights, load_flights, exists
from services.filter_service  import filter_and_sort, build_filter_summary
from services.airline_service import get_airlines_info
from utils.validators         import validate_search_params, validate_filter_params
from utils.flight_analysis    import build_analysis_context

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-flight")

mcp = FastMCP("FlightServer")


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1: search_flights
# ─────────────────────────────────────────────────────────────────────────────
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
    """
    Tìm chuyến bay từ Duffel API.
    Trả về search_id để các tools khác dùng, hoặc thông báo lỗi validation.
    """
    logger.info(f"[search_flights] {origin}→{destination} {departureDate}")

    params = {
        "origin": origin, "destination": destination,
        "departureDate": departureDate, "roundTrip": roundTrip,
        "returnDate": returnDate, "adults": adults,
        "children": children, "infants": infants,
        "travelClass": travelClass,
        "preferred_airlines": preferred_airlines or [],
    }

    # ── Validate ──────────────────────────────────────────────────────────────
    is_valid, errors, _ = validate_search_params(params)
    if not is_valid:
        return "[THÔNG TIN ĐẶT VÉ CẦN KHÁCH KIỂM TRA LẠI]:\n" + "\n".join(f"- {e}" for e in errors)

    # ── Cache hit ─────────────────────────────────────────────────────────────
    if current_search_id and current_search_id != "CLEAR" and exists(current_search_id):
        flights = load_flights(current_search_id)
        if flights:
            logger.info(f"[search_flights] Cache hit: {current_search_id} ({len(flights)} vé)")
            return (
                f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]: Tải lại từ cache.\n"
                f"search_id={current_search_id}\n"
                f"total={len(flights)}\n"
                f"Hành trình: {origin}→{destination} ngày {departureDate}"
            )

    # ── Gọi Duffel API ────────────────────────────────────────────────────────
    try:
        flights = await search_flights_async(params, max_offers=200)
    except Exception as e:
        logger.error(f"[search_flights] Duffel error: {e}")
        return f"[TRỤC TRẶC HỆ THỐNG]: Không thể kết nối với hãng hàng không. Chi tiết: {str(e)}"

    if not flights:
        return (
            f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Không có chuyến bay VN/VJ/QH nào cho hành trình "
            f"{origin}→{destination} ngày {departureDate}."
        )

    # ── Lưu Redis ─────────────────────────────────────────────────────────────
    search_id = save_flights(flights, prefix="search")

    # Thống kê nhanh
    cheapest = min(flights, key=lambda f: f.get("price", 9e9))
    non_stop = sum(
        1 for f in flights
        if all(it.get("stops", 1) == 0 for it in (f.get("itineraries") or []))
    )

    return (
        f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]\n"
        f"search_id={search_id}\n"
        f"total={len(flights)}\n"
        f"non_stop={non_stop}\n"
        f"cheapest_price={cheapest.get('price', 0):.0f} {cheapest.get('currency', 'VND')}\n"
        f"cheapest_airlines={', '.join(cheapest.get('airlines') or [])}\n"
        f"Hành trình: {origin}→{destination} ngày {departureDate}"
        + (f" | Khứ hồi về {returnDate}" if roundTrip and returnDate else "")
    )


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2: get_filtered_flights
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
async def get_filtered_flights(
    search_id: str,
    maxPrice: int | None = None,
    preferred_airlines: list[str] | None = None,
    nonStop: bool | None = None,
    travelClass: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    sort_preference: str | None = None,
) -> str:
    """
    Lấy danh sách vé đã lọc và sắp xếp server-side.
    Lưu kết quả vào Redis key mới (filtered_id) — FE dùng key này để hiển thị.
    Trả về filtered_id + summary để LLM xác nhận với khách.
    """
    logger.info(f"[get_filtered_flights] search_id={search_id}")

    # ── Load từ Redis ─────────────────────────────────────────────────────────
    flights = load_flights(search_id)
    if not flights:
        return (
            f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Phiên tìm kiếm '{search_id}' đã hết hạn. "
            f"Vui lòng tìm kiếm lại."
        )

    filters = {
        "maxPrice":          maxPrice,
        "preferred_airlines": preferred_airlines,
        "nonStop":           nonStop,
        "travelClass":       travelClass,
        "start_hour":        start_hour,
        "end_hour":          end_hour,
        "sort_preference":   sort_preference,
    }
    # Bỏ None để filter_and_sort không nhầm
    filters = {k: v for k, v in filters.items() if v is not None}

    # ── Validate filters ──────────────────────────────────────────────────────
    is_valid, errors = validate_filter_params(filters)
    if not is_valid:
        return "[BỘ LỌC KHÔNG HỢP LỆ]:\n" + "\n".join(f"- {e}" for e in errors)

    # ── Filter + Sort ─────────────────────────────────────────────────────────
    original_count = len(flights)
    filtered       = filter_and_sort(flights, filters)
    summary        = build_filter_summary(original_count, filtered, filters)

    # ── Lưu kết quả filtered ──────────────────────────────────────────────────
    if filtered:
        filtered_id = save_flights(filtered, prefix="filtered")
    else:
        filtered_id = None

    result = (
        f"[BỘ LỌC ĐƯỢC ÁP DỤNG]\n"
        f"filtered_id={filtered_id or 'NONE'}\n"
        f"original_count={original_count}\n"
        f"filtered_count={len(filtered)}\n"
        f"summary={summary}"
    )
    return result


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3: analyze_flights
# ─────────────────────────────────────────────────────────────────────────────
@mcp.tool()
async def analyze_flights(
    search_id: str,
    target_flight_numbers: list[str] | None = None,
    target_airline_codes: list[str] | None = None,
) -> str:
    """
    Build structured analysis context cho LLM.
    - target_flight_numbers: ["VN123", "VJ456"] — phân tích vé cụ thể
    - target_airline_codes: ["VN", "VJ"] — so sánh theo hãng
    - Nếu cả hai đều None: trả summary tổng quan
    """
    logger.info(
        f"[analyze_flights] search_id={search_id} "
        f"flights={target_flight_numbers} airlines={target_airline_codes}"
    )

    flights = load_flights(search_id)
    if not flights:
        return (
            f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Phiên '{search_id}' đã hết hạn. "
            f"Vui lòng tìm kiếm lại."
        )

    # Lấy thêm thông tin hãng từ DB nếu cần so sánh theo hãng
    airline_db_info = ""
    if target_airline_codes:
        clean_codes = [c.upper() for c in target_airline_codes if c and c != "CLEAR"]
        if clean_codes:
            airline_db_info = get_airlines_info(clean_codes)

    context = build_analysis_context(
        flights=flights,
        airline_db_info=airline_db_info,
        target_flights=target_flight_numbers,
        target_airlines=[c.upper() for c in target_airline_codes if c] if target_airline_codes else None,
    )

    return f"[DỮ LIỆU SO SÁNH CHUYẾN BAY/HÃNG BAY]\n{context}"


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting mcp-flight server at http://{host}:{port}/sse")

    # FastMCP version cũ: .run() chỉ nhận transport
    # Set port qua uvicorn trực tiếp
    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp._mcp_server.run(streams[0], streams[1], mcp._mcp_server.create_initialization_options())

    async def health(request: Request):
        return JSONResponse({"status": "ok", "server": "mcp-flight"})

    app = Starlette(routes=[
        Route("/health",   health),
        Route("/sse",      handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ])

    uvicorn.run(app, host=host, port=port, log_config=None)