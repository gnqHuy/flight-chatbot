"""
app/ai_orchestrator/graph/tools/flight_tool.py
"""
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


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
    current_search_id: str | None = None,
) -> str:
    """
    Tìm vé máy bay mới từ Duffel API.
    Gọi khi: khách cung cấp hành trình mới HOẶC đổi Core Param.
    current_search_id: luôn truyền search_id hiện tại để MCP kiểm tra cache.
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    logger.info(
        f"[search_flights tool] {origin}→{destination} {departureDate} | "
        f"current_search_id={current_search_id}"
    )

    args = {
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
        "current_search_id":  current_search_id,
    }
    logger.debug(f"[search_flights tool] args gửi MCP: {args}")

    result = await flight_mcp.call_tool("search_flights", args)
    logger.debug(f"[search_flights tool] MCP trả về: {result[:200]}...")
    return result


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
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    logger.info(
        f"[filter_flights tool] search_id={current_search_id} | "
        f"maxPrice={maxPrice} airlines={preferred_airlines} nonStop={nonStop} "
        f"hours={start_hour}-{end_hour} sort={sort_preference}"
    )

    args = {
        "search_id":          current_search_id,
        "maxPrice":           maxPrice,
        "preferred_airlines": preferred_airlines,
        "nonStop":            nonStop,
        "travelClass":        travelClass,
        "start_hour":         start_hour,
        "end_hour":           end_hour,
        "sort_preference":    sort_preference,
    }

    result = await flight_mcp.call_tool("get_filtered_flights", args)
    logger.debug(f"[filter_flights tool] MCP trả về: {result[:200]}...")
    return result


@tool
async def analyze_flights(
    current_search_id: str,
    compare_airlines: list[str] | None = None,
    compare_flights: list[str] | None = None,
) -> str:
    """
    So sánh và phân tích vé hoặc hãng bay từ kết quả tìm kiếm.
    """
    from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp

    if not compare_airlines and not compare_flights:
        logger.warning("[analyze_flights tool] Thiếu target — không có airline và flight number")
        return (
            "[YÊU CẦU CHỌN]: Bạn muốn so sánh hãng nào hoặc chuyến nào? "
            "Cho mình biết mã hãng (VN/VJ/QH) hoặc tick chọn trên màn hình."
        )

    logger.info(
        f"[analyze_flights tool] search_id={current_search_id} | "
        f"airlines={compare_airlines} flights={compare_flights}"
    )

    args = {
        "search_id":             current_search_id,
        "target_airline_codes":  compare_airlines,
        "target_flight_numbers": compare_flights,
    }

    result = await flight_mcp.call_tool("analyze_flights", args)
    logger.debug(f"[analyze_flights tool] MCP trả về: {result[:200]}...")
    return result