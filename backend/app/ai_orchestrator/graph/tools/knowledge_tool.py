from langchain_core.tools import tool
from app.ai_orchestrator.graph.tools.mcp_client import knowledge_mcp

@tool
async def search_policies(
    query: str,
    airline_codes: list[str] | None = None,
) -> str:
    """
    Tra cứu chính sách, quy định của hãng hàng không.
    Dùng khi hỏi về: hành lý, check-in, hoàn/đổi vé,
    giấy tờ, trẻ em, bà bầu, thú cưng, chất lỏng...
    """
    return await knowledge_mcp.call_tool("search_airline_policies", {
        "query":         query,
        "airline_codes": airline_codes or [],
    })


@tool
async def get_promotions(
    query: str,
    airline_codes: list[str] | None = None,
) -> str:
    """
    Tìm khuyến mãi, mã giảm giá của hãng hàng không dựa theo câu hỏi ngữ nghĩa.
    Dùng khi khách hỏi sâu/chi tiết về: khuyến mãi cho đường bay cụ thể, mã code, điều kiện giảm giá...
    """
    return await knowledge_mcp.call_tool("get_active_promotions", {
        "query":         query,
        "airline_codes": airline_codes or [], 
    })


@tool
async def get_airline_info(
    airline_codes: list[str] | None = None,
) -> str:
    """
    Lấy thông tin tổng quan, ưu/nhược điểm, hành lý cơ bản và 3 KHUYẾN MÃI NỔI BẬT MỚI NHẤT của các hãng hàng không.
    Gọi tool này khi khách yêu cầu so sánh hãng, hỏi thông tin chung, hoặc muốn biết nhanh hãng nào đang có khuyến mãi.
    """
    return await knowledge_mcp.call_tool("get_airline_info", {
        "airline_codes": airline_codes or [],
    })