import os
import logging
from datetime import datetime

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv(override=True)

SUPPORTED_AIRLINES = ["VN", "VJ", "QH"]

OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY", "")
KNOWLEDGE_DATABASE_URL = os.getenv("KNOWLEDGE_DATABASE_URL", "")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8002"))

COST_PER_TOKEN = 0.0000003

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("mcp-knowledge")

mcp = FastMCP("KnowledgeServer", host=HOST, port=PORT)

class ContextTag:
    PROMO_INFO    = "[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]"
    POLICY_INFO   = "[KIẾN THỨC NGHIỆP VỤ CHÍNH SÁCH]"
    SYS_NOT_FOUND = "[KHÔNG TÌM THẤY DỮ LIỆU]"
    SYS_ERROR     = "[TRỤC TRẶC HỆ THỐNG]"

def get_current_time() -> datetime:
    raw = os.getenv("TEST_DATE", "").strip()

    if raw:
        try:
            return datetime.strptime(raw, "%Y-%m-%d")
        except ValueError:
            pass

    return datetime.now()


def get_current_time_str() -> str:
    return get_current_time().strftime("%Y-%m-%d %H:%M")
