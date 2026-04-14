"""
mcp_knowledge/server.py
MCP Knowledge Server — policy RAG + promo RAG + ETL pipeline triggers.
Transport: SSE (FastMCP built-in), port 8002.
"""
import os, logging
from collections import defaultdict
from sqlmodel import Session, select, or_
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv(override=True)

from constants import SUPPORTED_AIRLINES, CURRENT_TIME, CURRENT_TIME_STR, ContextTag
from services.rag.vector_store import get_policy_vector_store, get_embeddings
from utils.database import engine                                               
from models.airline import Airline                                              
from models.flight_promotion import FlightPromotion                            

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mcp-knowledge")

port = int(os.getenv("PORT", "5001"))
host = os.getenv("HOST", "0.0.0.0")

mcp = FastMCP("KnowledgeServer", host=host, port=port)


# ── Tool 1: search_airline_policies ───────────────────────────────────────────
@mcp.tool()
def search_airline_policies(query: str, airline_codes: list[str] | None = None) -> str:
    """Tra cứu chính sách, quy định của các hãng hàng không."""
    logger.info(f"[policy] query='{query}' airlines={airline_codes}")
    target_airlines = (
        [c.upper() for c in airline_codes if c != "CLEAR"]
        if airline_codes and "CLEAR" not in airline_codes
        else []
    )
    try:
        store = get_policy_vector_store()
        docs  = []
        if target_airlines:
            for al in target_airlines:
                docs.extend(store.similarity_search(query, k=3, filter={"airline": al}))
        else:
            for al in SUPPORTED_AIRLINES:
                docs.extend(store.similarity_search(query, k=2, filter={"airline": al}))

        if not docs:
            return f"{ContextTag.SYS_NOT_FOUND}: Không tìm thấy thông tin chính sách."

        grouped = defaultdict(list)
        for doc in docs:
            airline = doc.metadata.get("airline", "UNKNOWN").upper()
            url     = doc.metadata.get("source_url", "Không có link")
            content = " ".join(doc.page_content.replace("\n", " ").split()).strip()
            if not any(i["content"] == content for i in grouped[airline]):
                grouped[airline].append({"content": content, "url": url})

        result = f"{ContextTag.POLICY_INFO}\n- CÂU HỎI: '{query}'\n- NỘI DUNG TRA CỨU:\n"
        for airline, items in grouped.items():
            result += f"\n▶ QUY ĐỊNH CỦA HÃNG {airline}:\n"
            for i, item in enumerate(items, 1):
                result += f"  {i}. {item['content']}\n     [Link]: {item['url']}\n"
        return result.strip()
    except Exception as e:
        logger.exception("search_airline_policies error")
        return f"{ContextTag.SYS_ERROR}: Lỗi hệ thống: {str(e)}"


# ── Tool 2: get_active_promotions ─────────────────────────────────────────────
@mcp.tool()
def get_active_promotions(query: str, airline_code: str | None = None) -> str:
    """Tìm kiếm các chương trình khuyến mãi vé máy bay."""
    logger.info(f"[promo] query='{query}' airline={airline_code}")
    try:
        embeddings   = get_embeddings()          # FIX [1]
        query_vector = embeddings.embed_query(query)

        with Session(engine) as session:
            stmt = select(FlightPromotion)
            if airline_code:
                airline_obj = session.exec(
                    select(Airline).where(Airline.code == airline_code.upper())
                ).first()
                if airline_obj:
                    stmt = stmt.where(FlightPromotion.airline_id == airline_obj.id)
            stmt = stmt.where(
                or_(FlightPromotion.booking_end_date == None,
                    FlightPromotion.booking_end_date >= CURRENT_TIME.date())
            ).order_by(
                FlightPromotion.embedding.cosine_distance(query_vector)
            ).limit(3)
            docs = list(session.exec(stmt).all())

        if not docs:
            return f"{ContextTag.SYS_NOT_FOUND}: Không có khuyến mãi phù hợp."

        result = f"{ContextTag.PROMO_INFO}\n- CÂU HỎI: '{query}'\n- NGÀY: {CURRENT_TIME_STR}\n"
        for i, p in enumerate(docs, 1):
            b_end = p.booking_end_date.strftime("%d/%m/%Y") if p.booking_end_date else "Không giới hạn"
            result += f"\n▶ {i}. {p.promo_name}\n   - Mã: {p.promo_code}\n   - Hạn: {b_end}\n   - Chi tiết: {p.description}\n   - [Link]: {p.url}\n"
        return result.strip()
    except Exception as e:
        logger.exception("get_active_promotions error")
        return f"{ContextTag.SYS_ERROR}: Lỗi tra cứu khuyến mãi: {str(e)}"


# ── Tool 3: run_policy_pipeline ───────────────────────────────────────────────
@mcp.tool()
def run_policy_pipeline() -> str:
    """Chạy toàn bộ ETL pipeline cho chính sách: crawl → format → ingest vector DB."""
    logger.info("[pipeline] Starting policy ETL...")
    try:
        from services.data_pipeline.pineline.policy_pipeline import PolicyETLPipeline
        ok = PolicyETLPipeline().run_pipeline()
        return "✅ Policy pipeline hoàn tất." if ok else "❌ Policy pipeline thất bại."
    except Exception as e:
        logger.exception("run_policy_pipeline error")
        return f"❌ Lỗi: {str(e)}"


# ── Tool 4: run_promo_pipeline ────────────────────────────────────────────────
@mcp.tool()
def run_promo_pipeline() -> str:
    """Chạy toàn bộ ETL pipeline cho khuyến mãi: discover → crawl → extract → ingest."""
    logger.info("[pipeline] Starting promo ETL...")
    try:
        from services.data_pipeline.pineline.promo_pipeline import PromotionETLPipeline
        ok = PromotionETLPipeline().run_pipeline()
        return "✅ Promo pipeline hoàn tất." if ok else "❌ Promo pipeline thất bại."
    except Exception as e:
        logger.exception("run_promo_pipeline error")
        return f"❌ Lỗi: {str(e)}"


# ── Tool 5: get_pipeline_status ───────────────────────────────────────────────
@mcp.tool()
def get_pipeline_status() -> str:
    """Xem số lượng tasks theo status trong staging table."""
    try:
        from repositories.crawler_staging_repo import CrawlerStagingRepository
        with Session(engine) as s:
            counts = CrawlerStagingRepository(s).count_by_status()
        return "\n".join(f"  {k}: {v}" for k, v in counts.items())
    except Exception as e:
        return f"❌ Lỗi: {str(e)}"


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8002"))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🚀 Starting KnowledgeServer at http://{host}:{port}/sse")
    # FIX [16]: thêm host parameter
    mcp.run(transport="sse")