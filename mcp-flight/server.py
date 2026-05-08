"""
mcp-flight/server.py

MCP Flight Server — 3 tools:
  1. search_flights       → Duffel API → lưu Redis (kèm meta) → trả search_id
  2. get_filtered_flights → filter/sort server-side; tự recover cache nếu hết hạn
  3. analyze_flights      → build analysis context; tự recover cache nếu hết hạn

Transport: SSE (FastMCP), port 8001.
"""
import os
import sys
import json
import logging
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from services.duffel_service  import search_flights_async
from services.redis_service   import save_flights, load_flights, exists, save_raw, load_raw
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

_META_TTL = 7200  # Lưu meta 2 giờ — dài hơn TTL data (1h) để còn recover

# Core params dùng để so sánh cache hit — đổi bất kỳ field nào → search mới
_CORE_PARAM_KEYS = [
    "origin", "destination", "departureDate",
    "roundTrip", "returnDate",
    "adults", "children", "infants",
    "travelClass",
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Normalize param value để so sánh
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(val) -> str:
    """
    Chuẩn hoá giá trị param để so sánh cache hit.
    None / "" / False đều về chuỗi "" để tránh false miss.
    """
    if val is None or val == "" or val is False:
        return ""
    if val is True:
        return "TRUE"
    s = str(val).strip().upper()
    if s == "TRUE":
        return "TRUE"
    if s == "FALSE":
        return ""
    return s


def _same_core_params(params: dict, meta: dict) -> bool:
    """
    So sánh Core Params hiện tại với meta đã lưu.
    Trả True chỉ khi tất cả Core Params giống nhau → có thể dùng cache.
    """
    for key in _CORE_PARAM_KEYS:
        if _normalize(params.get(key)) != _normalize(meta.get(key)):
            logger.debug(
                f"[cache_check] Param '{key}' thay đổi: "
                f"'{meta.get(key)}' → '{params.get(key)}'"
            )
            return False
    return True


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: Cache recovery
# ─────────────────────────────────────────────────────────────────────────────

async def _recover_cache(search_id: str) -> list | None:
    """
    Thử recover cache từ meta params đã lưu khi search lần đầu.
    Trả về danh sách vé mới nếu thành công, None nếu không có meta.
    """
    meta_raw = load_raw(f"{search_id}:meta")
    if not meta_raw:
        logger.warning(f"[recover] Không có meta cho {search_id}")
        return None

    try:
        meta = json.loads(meta_raw)
    except Exception:
        return None

    logger.info(
        f"[recover] Tìm lại từ meta: "
        f"{meta.get('origin')}→{meta.get('destination')} {meta.get('departureDate')}"
    )

    try:
        flights = await search_flights_async(meta, max_offers=200)
        if flights:
            # Lưu lại với cùng search_id để các keys cũ vẫn dùng được
            save_flights(flights, prefix="search", override_key=search_id)
            save_raw(f"{search_id}:meta", meta_raw, ttl=_META_TTL)
            return flights
    except Exception as e:
        logger.error(f"[recover] Duffel error: {e}")

    return None


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

    Cache logic (MCP tự quyết, không phụ thuộc backend):
      - Nếu current_search_id được truyền vào VÀ còn hạn VÀ Core Params
        giống hệt meta đã lưu → trả lại cache, KHÔNG gọi Duffel.
      - Nếu Core Params thay đổi (dù id còn hạn) → gọi Duffel mới.
      - Nếu không có current_search_id → gọi Duffel bình thường.

    Backend chỉ cần luôn truyền current_search_id hiện tại vào args.
    MCP tự quyết dùng cache hay gọi mới.
    """
    logger.info(f"[search_flights] {origin}→{destination} {departureDate}")

    params = {
        "origin":             origin,
        "destination":        destination,
        "departureDate":      departureDate,
        "roundTrip":          roundTrip,
        "returnDate":         returnDate,
        "adults":             adults,
        "children":           children,
        "infants":            infants,
        "travelClass":        travelClass,
        "preferred_airlines": preferred_airlines or [],
    }

    # ── Validate trước (V1–V7) ────────────────────────────────────────────────
    is_valid, errors, _ = validate_search_params(params)
    if not is_valid:
        return "[THÔNG TIN ĐẶT VÉ CẦN KHÁCH KIỂM TRA LẠI]:\n" + "\n".join(
            f"- {e}" for e in errors
        )

    # ── Cache hit: so sánh Core Params với meta đã lưu ───────────────────────
    # Đây là bước quan trọng — MCP tự quyết, không tin tưởng hoàn toàn vào
    # backend để tránh: (1) gọi Duffel lặp với cùng params, (2) trả sai data
    # khi backend truyền id nhưng params đã đổi.
    if current_search_id and current_search_id != "CLEAR":
        meta_raw = load_raw(f"{current_search_id}:meta")
        if meta_raw and exists(current_search_id):
            try:
                meta = json.loads(meta_raw)
                if _same_core_params(params, meta):
                    flights = load_flights(current_search_id)
                    if flights:
                        save_flights(flights, prefix="search", override_key=current_search_id)
                        save_raw(f"{current_search_id}:meta", meta_raw, ttl=_META_TTL)
                        logger.info(f"[search_flights] Cache hit + TTL refreshed: {current_search_id}")
                        cheapest = min(flights, key=lambda f: f.get("price", 9e9))
                        non_stop = sum(
                            1 for f in flights
                            if all(
                                it.get("stops", 1) == 0
                                for it in (f.get("itineraries") or [])
                            )
                        )
                        return (
                            f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]\n"
                            f"search_id={current_search_id}\n"
                            f"total={len(flights)}\n"
                            f"non_stop={non_stop}\n"
                            f"cheapest_price={cheapest.get('price', 0):.0f} "
                            f"{cheapest.get('currency', 'VND')}\n"
                            f"cheapest_airlines={', '.join(cheapest.get('airlines') or [])}\n"
                            f"Hành trình: {origin}→{destination} ngày {departureDate}"
                            + (f" | Khứ hồi về {returnDate}" if roundTrip and returnDate else "")
                        )
                else:
                    logger.info(
                        f"[search_flights] Core params thay đổi → tìm mới "
                        f"(bỏ cache {current_search_id})"
                    )
            except Exception as e:
                logger.warning(f"[search_flights] Lỗi parse meta: {e} → gọi Duffel")
        # Nếu meta không có hoặc id hết hạn → gọi Duffel bình thường

    # ── Gọi Duffel ────────────────────────────────────────────────────────────
    try:
        flights = await search_flights_async(params, max_offers=200)
    except Exception as e:
        logger.error(f"[search_flights] Duffel error: {e}")
        return (
            f"[TRỤC TRẶC HỆ THỐNG]: Không thể kết nối với hãng hàng không. "
            f"Chi tiết: {str(e)}"
        )

    if not flights:
        return (
            f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Không có chuyến bay VN/VJ/QH nào cho "
            f"{origin}→{destination} ngày {departureDate}."
        )

    # ── Lưu Redis + meta ──────────────────────────────────────────────────────
    search_id = save_flights(flights, prefix="search")

    # Meta lưu Core Params để: (1) compare cache hit lần sau, (2) recover khi hết hạn
    save_raw(f"{search_id}:meta", json.dumps(params), ttl=_META_TTL)

    # Thống kê
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
    Lọc và sắp xếp vé server-side.
    Tự động recover cache nếu hết hạn (dùng meta params đã lưu).
    """
    logger.info(f"[get_filtered_flights] search_id={search_id}")

    # ── Load cache (tự recover nếu hết hạn) ──────────────────────────────────
    flights = load_flights(search_id)
    if not flights:
        logger.info(f"[get_filtered_flights] Cache hết hạn, thử recover...")
        flights = await _recover_cache(search_id)
        if not flights:
            return (
                "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể "
                "khôi phục tự động. Vui lòng tìm vé lại nhé."
            )
        logger.info(f"[get_filtered_flights] Recover thành công: {len(flights)} vé")

    filters = {
        k: v for k, v in {
            "maxPrice":           maxPrice,
            "preferred_airlines": preferred_airlines,
            "nonStop":            nonStop,
            "travelClass":        travelClass,
            "start_hour":         start_hour,
            "end_hour":           end_hour,
            "sort_preference":    sort_preference,
        }.items() if v is not None
    }

    # ── Validate filter params ────────────────────────────────────────────────
    is_valid, errors = validate_filter_params(filters)
    if not is_valid:
        return "[BỘ LỌC KHÔNG HỢP LỆ]:\n" + "\n".join(f"- {e}" for e in errors)

    # ── Filter + Sort ─────────────────────────────────────────────────────────
    original_count = len(flights)
    filtered       = filter_and_sort(flights, filters)
    summary        = build_filter_summary(original_count, filtered, filters)
    filtered_id    = save_flights(filtered, prefix="filtered") if filtered else None

    return (
        f"[BỘ LỌC ĐƯỢC ÁP DỤNG]\n"
        f"filtered_id={filtered_id or 'NONE'}\n"
        f"original_count={original_count}\n"
        f"filtered_count={len(filtered)}\n"
        f"summary={summary}"
    )


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
    Tự động recover cache nếu hết hạn.
    target_airline_codes: ["VN","VJ"] — so sánh theo hãng.
    target_flight_numbers: ["VN123","VJ456"] — so sánh vé cụ thể.
    """
    logger.info(
        f"[analyze_flights] search_id={search_id} airlines={target_airline_codes}"
    )

    # ── Load cache (tự recover nếu hết hạn) ──────────────────────────────────
    flights = load_flights(search_id)
    if not flights:
        logger.info(f"[analyze_flights] Cache hết hạn, thử recover...")
        flights = await _recover_cache(search_id)
        if not flights:
            return (
                "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể "
                "khôi phục tự động. Vui lòng tìm vé lại nhé."
            )
        logger.info(f"[analyze_flights] Recover thành công: {len(flights)} vé")

    airline_db_info = ""
    if target_airline_codes:
        clean = [c.upper() for c in target_airline_codes if c and c != "CLEAR"]
        if clean:
            airline_db_info = get_airlines_info(clean)

    context = build_analysis_context(
        flights=flights,
        airline_db_info=airline_db_info,
        target_flights=target_flight_numbers,
        target_airlines=(
            [c.upper() for c in target_airline_codes if c]
            if target_airline_codes else None
        ),
    )

    return f"[DỮ LIỆU SO SÁNH CHUYẾN BAY/HÃNG BAY]\n{context}"


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting mcp-flight server at http://{host}:{port}/sse")

    import uvicorn
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Route, Mount
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    sse = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp._mcp_server.run(
                streams[0], streams[1],
                mcp._mcp_server.create_initialization_options()
            )

    async def health(request: Request):
        return JSONResponse({"status": "ok", "server": "mcp-flight"})

    app = Starlette(routes=[
        Route("/health",   health),
        Route("/sse",      handle_sse),
        Mount("/messages", app=sse.handle_post_message),
    ])

    uvicorn.run(app, host=host, port=port, log_config=None)