"""
app/ai_orchestrator/graph/tools/flight_tool.py
3 tools riêng biệt: search_flights, filter_flights, analyze_flights.
Normalize được xử lý ở system prompt — tool chỉ gọi MCP.
"""
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 1: search_flights
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def search_flights(
    origin: str,
    destination: str,
    departureDate: str,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    roundTrip: bool = False,
    returnDate: str | None = None,
    travelClass: str | None = None,
    preferred_airlines: list[str] | None = None,
) -> str:
    """
    Tìm vé máy bay mới từ Duffel API.
    Gọi khi: khách cung cấp hành trình mới HOẶC đổi Core Param
    (điểm đi, điểm đến, ngày bay, số hành khách, hạng ghế).
    KHÔNG gọi nếu chỉ thay đổi bộ lọc (hãng, giá, giờ bay).

    Trả về search_id để dùng cho filter_flights và analyze_flights.
    origin/destination: mã IATA 3 chữ (HAN, SGN, DAD, PQC, CXR...).
    preferred_airlines: IATA code hãng bay (VN, VJ, QH).
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    logger.info(f"[search_flights] {origin}→{destination} {departureDate}")

    return await flight_mcp.call_tool("search_flights", {
        "origin":             origin,
        "destination":        destination,
        "departureDate":      departureDate,
        "adults":             adults,
        "children":           children,
        "infants":            infants,
        "roundTrip":          roundTrip,
        "returnDate":         returnDate,
        "travelClass":        travelClass,
        "preferred_airlines": preferred_airlines or [],
        "current_search_id":  None,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 2: filter_flights
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def filter_flights(
    current_search_id: str,
    maxPrice: int | None = None,
    preferred_airlines: list[str] | None = None,
    nonStop: bool | None = None,
    travelClass: str | None = None,
    start_hour: int | None = None,
    end_hour: int | None = None,
    sort_preference: str | None = None,
) -> str:
    """
    Lọc và sắp xếp vé từ kết quả tìm kiếm đang có.
    Gọi khi: khách thay đổi Soft Param trên danh sách hiện tại.
    Nếu cache hết hạn, MCP server tự động tìm lại — không cần lo.

    Bỏ lọc một tiêu chí: truyền None cho param đó.
    Loại hãng X: preferred_airlines = [các hãng còn lại, KHÔNG có X].
    sort_preference: "price_asc" | "price_desc" | "departure_time" | "arrival_time"
    preferred_airlines: IATA code (VN, VJ, QH).
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    logger.info(f"[filter_flights] search_id={current_search_id}")

    return await flight_mcp.call_tool("get_filtered_flights", {
        "search_id":          current_search_id,
        "maxPrice":           maxPrice,
        "preferred_airlines": preferred_airlines,
        "nonStop":            nonStop,
        "travelClass":        travelClass,
        "start_hour":         start_hour,
        "end_hour":           end_hour,
        "sort_preference":    sort_preference,
    })


# ─────────────────────────────────────────────────────────────────────────────
# TOOL 3: analyze_flights
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def analyze_flights(
    current_search_id: str,
    compare_airlines: list[str] | None = None,
    compare_flights: list[str] | None = None,
) -> str:
    """
    So sánh và phân tích vé hoặc hãng bay từ kết quả tìm kiếm.
    Gọi khi: khách muốn so sánh vé/hãng cụ thể.
    Nếu cache hết hạn, MCP server tự động tìm lại — không cần lo.

    compare_airlines: IATA code ["VN","VJ","QH"] — so sánh theo hãng.
    compare_flights: mã chuyến ["VN123","VJ456"] — so sánh vé cụ thể.
    Phải truyền ít nhất 1 trong 2.
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    if not compare_airlines and not compare_flights:
        return (
            "[YÊU CẦU CHỌN]: Bạn muốn so sánh hãng nào hoặc chuyến nào? "
            "Cho mình biết mã hãng (VN/VJ/QH) hoặc tick chọn trên màn hình."
        )

    logger.info(f"[analyze_flights] search_id={current_search_id} airlines={compare_airlines}")

    return await flight_mcp.call_tool("analyze_flights", {
        "search_id":             current_search_id,
        "target_airline_codes":  compare_airlines,
        "target_flight_numbers": compare_flights,
    })