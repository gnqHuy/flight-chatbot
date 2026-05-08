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
import uvicorn

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from services.duffel_service  import search_flights_async
from services.redis_service   import save_flights, load_flights, exists, save_raw, load_raw
from services.filter_service  import filter_and_sort, build_filter_summary
from services.airline_service import get_airlines_info
from utils.validators         import validate_search_params, validate_filter_params
from utils.flight_analysis    import build_analysis_context

# ─────────────────────────────────────────────────────────────────────────────
# Logging — DEBUG=true để xem chi tiết, mặc định INFO
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
    force=True,
)
logging.getLogger("sse_starlette.sse").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("mcp-flight")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
mcp = FastMCP("FlightServer")

_META_TTL = 7200

_CORE_PARAM_KEYS = [
    "origin", "destination", "departureDate",
    "roundTrip", "returnDate",
    "adults", "children", "infants",
    "travelClass",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(val) -> str:
    if val is None or val == "" or val is False:
        return ""
    if val is True:
        return "TRUE"
    s = str(val).strip().upper()
    if s in ("TRUE", "FALSE"):
        return s if s == "TRUE" else ""
    return s


def _same_core_params(params: dict, meta: dict) -> bool:
    logger.debug("[cache_check] So sánh Core Params:")
    all_same = True
    for key in _CORE_PARAM_KEYS:
        p_val = _normalize(params.get(key))
        m_val = _normalize(meta.get(key))
        if p_val != m_val:
            logger.debug(f"  [DIFF] {key}: '{meta.get(key)}' → '{params.get(key)}'")
            all_same = False
        else:
            logger.debug(f"  [SAME] {key}: '{params.get(key)}'")
    return all_same


async def _recover_cache(search_id: str) -> list | None:
    logger.info(f"[recover] Bắt đầu recover cho search_id={search_id}")

    meta_raw = load_raw(f"{search_id}:meta")
    if not meta_raw:
        logger.warning(f"[recover] FAIL — không có meta key '{search_id}:meta' trong Redis")
        return None

    try:
        meta = json.loads(meta_raw)
    except Exception as e:
        logger.error(f"[recover] FAIL — parse meta lỗi: {e}")
        return None

    logger.info(
        f"[recover] Meta OK — "
        f"{meta.get('origin')}→{meta.get('destination')} "
        f"{meta.get('departureDate')} "
        f"adults={meta.get('adults')} children={meta.get('children')} infants={meta.get('infants')}"
    )

    try:
        logger.info("[recover] Gọi Duffel API để lấy lại vé...")
        flights = await search_flights_async(meta, max_offers=200)
        if flights:
            save_flights(flights, prefix="search", override_key=search_id)
            save_raw(f"{search_id}:meta", meta_raw, ttl=_META_TTL)
            logger.info(
                f"[recover] OK — {len(flights)} vé, "
                f"data TTL reset 3600s, meta TTL reset {_META_TTL}s"
            )
            return flights
        else:
            logger.warning("[recover] Duffel trả về 0 vé")
    except Exception as e:
        logger.error(f"[recover] Duffel error: {e}")

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1: search_flights
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
    Cache logic: MCP tự quyết dùng cache hay gọi Duffel mới dựa trên Core Params.
    Backend chỉ cần luôn truyền current_search_id hiện tại vào args.
    """
    logger.info(
        f"[search_flights] CALL {origin}→{destination} {departureDate} "
        f"adults={adults} children={children} infants={infants} "
        f"current_search_id={current_search_id}"
    )

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

    # ── Validate (V1–V7) ──────────────────────────────────────────────────────
    is_valid, errors, _ = validate_search_params(params)
    if not is_valid:
        logger.warning(f"[search_flights] Validation FAIL: {errors}")
        return "[THÔNG TIN ĐẶT VÉ CẦN KHÁCH KIỂM TRA LẠI]:\n" + "\n".join(
            f"- {e}" for e in errors
        )

    # ── Cache check ───────────────────────────────────────────────────────────
    if current_search_id and current_search_id != "CLEAR":
        meta_raw   = load_raw(f"{current_search_id}:meta")
        data_alive = exists(current_search_id)
        logger.debug(f"  meta_exists={meta_raw is not None} | data_exists={data_alive}")

        if meta_raw and data_alive:
            try:
                meta = json.loads(meta_raw)
                if _same_core_params(params, meta):
                    flights = load_flights(current_search_id)
                    if flights:
                        save_flights(flights, prefix="search", override_key=current_search_id)
                        save_raw(f"{current_search_id}:meta", meta_raw, ttl=_META_TTL)
                        cheapest = min(flights, key=lambda f: f.get("price", 9e9))
                        non_stop = sum(
                            1 for f in flights
                            if all(it.get("stops", 1) == 0 for it in (f.get("itineraries") or []))
                        )
                        logger.info(
                            f"[search_flights] CACHE HIT — {len(flights)} vé, "
                            f"rẻ nhất {cheapest.get('price')} {cheapest.get('currency')}. TTL reset."
                        )
                        return (
                            f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]\n"
                            f"search_id={current_search_id}\n"
                            f"total={len(flights)}\n"
                            f"non_stop={non_stop}\n"
                            f"cheapest_price={cheapest.get('price', 0):.0f} {cheapest.get('currency', 'VND')}\n"
                            f"cheapest_airlines={', '.join(cheapest.get('airlines') or [])}\n"
                            f"Hành trình: {origin}→{destination} ngày {departureDate}"
                            + (f" | Khứ hồi về {returnDate}" if roundTrip and returnDate else "")
                        )
                    else:
                        logger.warning("[search_flights] Params giống nhưng data corrupt — gọi Duffel mới")
                else:
                    logger.info(f"[search_flights] CACHE MISS — params thay đổi, bỏ id={current_search_id}")
            except Exception as e:
                logger.warning(f"[search_flights] Lỗi parse meta: {e} — gọi Duffel")
        else:
            logger.info(
                f"[search_flights] Cache hết hạn hoặc không có meta cho id={current_search_id}"
            )
    else:
        logger.info("[search_flights] Không có current_search_id — gọi Duffel mới")

    # ── Gọi Duffel ────────────────────────────────────────────────────────────
    logger.info(f"[search_flights] Gọi Duffel API: {origin}→{destination} {departureDate}")
    try:
        flights = await search_flights_async(params, max_offers=200)
    except Exception as e:
        logger.error(f"[search_flights] Duffel FAIL: {e}")
        return (
            f"[TRỤC TRẶC HỆ THỐNG]: Không thể kết nối với hãng hàng không. "
            f"Chi tiết: {str(e)}"
        )

    if not flights:
        logger.warning(f"[search_flights] Duffel trả về 0 vé")
        return (
            f"[KHÔNG TÌM THẤY CHUYẾN BAY]: Không có chuyến bay VN/VJ/QH nào cho "
            f"{origin}→{destination} ngày {departureDate}."
        )

    # ── Lưu Redis + meta ──────────────────────────────────────────────────────
    search_id = save_flights(flights, prefix="search")
    save_raw(f"{search_id}:meta", json.dumps(params), ttl=_META_TTL)

    cheapest = min(flights, key=lambda f: f.get("price", 9e9))
    non_stop = sum(
        1 for f in flights
        if all(it.get("stops", 1) == 0 for it in (f.get("itineraries") or []))
    )
    logger.info(
        f"[search_flights] OK — {len(flights)} vé, non_stop={non_stop}, "
        f"rẻ nhất {cheapest.get('price')} {cheapest.get('currency')} "
        f"({', '.join(cheapest.get('airlines') or [])}). Lưu → {search_id}"
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
# Tool 2: get_filtered_flights
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
    logger.info(
        f"[filter_flights] CALL search_id={search_id} | "
        f"maxPrice={maxPrice} airlines={preferred_airlines} nonStop={nonStop} "
        f"hours={start_hour}-{end_hour} sort={sort_preference}"
    )

    flights = load_flights(search_id)
    if not flights:
        logger.info(f"[filter_flights] Cache MISS — thử recover...")
        flights = await _recover_cache(search_id)
        if not flights:
            logger.warning("[filter_flights] Recover FAIL")
            return (
                "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể "
                "khôi phục tự động. Vui lòng tìm vé lại nhé."
            )
    else:
        logger.info(f"[filter_flights] Cache HIT — {len(flights)} vé")

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

    is_valid, errors = validate_filter_params(filters)
    if not is_valid:
        logger.warning(f"[filter_flights] Filter params invalid: {errors}")
        return "[BỘ LỌC KHÔNG HỢP LỆ]:\n" + "\n".join(f"- {e}" for e in errors)

    original_count = len(flights)
    filtered       = filter_and_sort(flights, filters)
    summary        = build_filter_summary(original_count, filtered, filters)
    filtered_id    = save_flights(filtered, prefix="filtered") if filtered else None

    logger.info(f"[filter_flights] OK — {original_count} → {len(filtered)} vé. filtered_id={filtered_id}")

    return (
        f"[BỘ LỌC ĐƯỢC ÁP DỤNG]\n"
        f"filtered_id={filtered_id or 'NONE'}\n"
        f"original_count={original_count}\n"
        f"filtered_count={len(filtered)}\n"
        f"summary={summary}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3: analyze_flights
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
    """
    logger.info(
        f"[analyze_flights] CALL search_id={search_id} | "
        f"airlines={target_airline_codes} flights={target_flight_numbers}"
    )

    flights = load_flights(search_id)
    if not flights:
        logger.info("[analyze_flights] Cache MISS — thử recover...")
        flights = await _recover_cache(search_id)
        if not flights:
            logger.warning("[analyze_flights] Recover FAIL")
            return (
                "[THÔNG TIN CẦN BỔ SUNG]: Phiên tìm kiếm đã hết hạn và không thể "
                "khôi phục tự động. Vui lòng tìm vé lại nhé."
            )
    else:
        logger.info(f"[analyze_flights] Cache HIT — {len(flights)} vé")

    airline_db_info = ""
    if target_airline_codes:
        clean = [c.upper() for c in target_airline_codes if c and c != "CLEAR"]
        if clean:
            logger.debug(f"[analyze_flights] Lấy DB info cho hãng: {clean}")
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

    logger.info(f"[analyze_flights] OK — context {len(context)} chars")
    return f"[DỮ LIỆU SO SÁNH CHUYẾN BAY/HÃNG BAY]\n{context}"


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8001"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"Starting mcp-flight server at http://{host}:{port}/sse")

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