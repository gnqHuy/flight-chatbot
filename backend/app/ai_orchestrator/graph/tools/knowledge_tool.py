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
    airline_code: str | None = None,
) -> str:
    """
    Tìm khuyến mãi, mã giảm giá của hãng hàng không.
    Dùng khi hỏi về: khuyến mãi, mã code, giảm giá, ưu đãi...
    """
    return await knowledge_mcp.call_tool("get_active_promotions", {
        "query":        query,
        "airline_code": airline_code,
    })