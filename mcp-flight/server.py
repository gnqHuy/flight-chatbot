import os
import sys
import uvicorn
from dotenv import load_dotenv
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import JSONResponse
from mcp.server.sse import SseServerTransport

load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(__file__))

from core import mcp, logger
import tools
from services.redis_service import load_flights

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

    async def get_cached_flights_endpoint(request: Request):
        search_id = request.path_params["search_id"]
        flights = load_flights(search_id)
        if not flights:
            return JSONResponse({"detail": "Phiên tìm vé đã hết hạn hoặc không tồn tại"}, status_code=410)
        return JSONResponse({"flights": flights})

    app = Starlette(routes=[
        Route("/health",   health),
        Route("/sse",      handle_sse),
        Mount("/messages", app=sse.handle_post_message),
        Route("/api/flights/cache/{search_id}", get_cached_flights_endpoint, methods=["GET"]),
    ])

    uvicorn.run(app, host=host, port=port, log_config=None)