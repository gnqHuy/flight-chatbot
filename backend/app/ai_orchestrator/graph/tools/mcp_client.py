"""
app/ai_orchestrator/graph/tools/mcp_client.py
MCP client singletons cho knowledge server và flight server.
Call-once pattern: mở SSE → gọi tool → đóng.
"""
import os
from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPClient:
    def __init__(self, server_url: str, name: str = "mcp"):
        self.server_url = server_url
        self.name       = name

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Mở SSE → initialize → call tool → đóng."""
        async with sse_client(self.server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                return "\n".join(
                    c.text for c in result.content if hasattr(c, "text")
                )

knowledge_mcp = MCPClient(
    server_url=os.getenv("KNOWLEDGE_MCP_URL", "http://127.0.0.1:5001/sse"),
    name="knowledge",
)

flight_mcp = MCPClient(
    server_url=os.getenv("FLIGHT_MCP_URL", "http://127.0.0.1:8001/sse"),
    name="flight",
)