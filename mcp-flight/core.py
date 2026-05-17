# mcp-flight/core.py
import sys
import logging
from mcp.server.fastmcp import FastMCP

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

mcp = FastMCP("FlightServer")

_META_TTL = 7200
_CORE_PARAM_KEYS = [
    "origin", "destination", "departureDate",
    "roundTrip", "returnDate",
    "adults", "children", "infants",
    "travelClass",
]