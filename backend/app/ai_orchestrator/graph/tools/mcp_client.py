"""
app/ai_orchestrator/graph/tools/mcp_client.py
Persistent MCP Client: Duy trì kết nối SSE dai dẳng để tối ưu hiệu năng.
Hỗ trợ tự động kết nối lại (auto-reconnect) nếu mất kết nối.
"""
import os
import logging
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client

logger = logging.getLogger(__name__)

class MCPClient:
    def __init__(self, server_url: str, name: str = "mcp"):
        self.server_url = server_url
        self.name = name
        self.session: ClientSession | None = None
        self._exit_stack = AsyncExitStack()

    async def connect(self):
        """Thiết lập kết nối SSE dai dẳng."""
        if self.session:
            return

        logger.info(f"[{self.name}] Đang khởi tạo kết nối Persistent SSE tới {self.server_url}...")
        try:
            streams = await self._exit_stack.enter_async_context(sse_client(self.server_url))
            self.session = await self._exit_stack.enter_async_context(ClientSession(streams[0], streams[1]))
            
            await self.session.initialize()
            logger.info(f"[{self.name}] ✅ Đã kết nối và khởi tạo session thành công!")
            
        except Exception as e:
            logger.error(f"[{self.name}] ❌ Lỗi kết nối: {e}")
            await self.close()
            raise

    async def close(self):
        """Đóng kết nối và giải phóng tài nguyên."""
        if self.session or self._exit_stack:
            logger.info(f"[{self.name}] Đóng kết nối SSE...")
            try:
                await self._exit_stack.aclose()
            except Exception as e:
                logger.error(f"[{self.name}] Lỗi khi đóng kết nối: {e}")
            finally:
                self.session = None

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Gọi tool thông qua session đã mở sẵn."""
        if not self.session:
            logger.warning(f"[{self.name}] Session chưa mở hoặc bị mất, đang thử kết nối lại...")
            await self.connect()

        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return "\n".join(c.text for c in result.content if hasattr(c, "text"))
            
        except Exception as e:
            logger.error(f"[{self.name}] Lỗi khi gọi tool '{tool_name}': {e}")
            await self.close()
            return f"❌ Lỗi kết nối tới MCP Server {self.name}: {str(e)}"

knowledge_mcp = MCPClient(
    server_url=os.getenv("KNOWLEDGE_MCP_URL", "http://127.0.0.1:5001/sse"),
    name="Knowledge",
)

flight_mcp = MCPClient(
    server_url=os.getenv("FLIGHT_MCP_URL", "http://127.0.0.1:8001/sse"),
    name="Flight",
)