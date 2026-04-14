# app/ai_orchestrator/tools/mcp_client.py
import os
from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPKnowledgeClient:
    def __init__(self):
        # Tự động lấy URL nội bộ từ Docker hoặc Localhost
        self.server_url = os.getenv("KNOWLEDGE_MCP_URL", "http://127.0.0.1:5001/sse")

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Hàm gọi tool dùng một lần (Mở -> Khởi tạo -> Gọi -> Tự đóng)"""
        async with sse_client(self.server_url) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                
                # Trích xuất text từ response của thư viện MCP
                return "\n".join(content.text for content in result.content)

# Khởi tạo một instance duy nhất (Singleton) để import vào các Node
knowledge_mcp = MCPKnowledgeClient()