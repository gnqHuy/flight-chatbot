# mcp_knowledge/tools.py
import threading
from collections import defaultdict
from sqlmodel import Session, select, or_

from constants import mcp, logger

# Import các dependency của dự án
from constants import get_current_time, get_current_time_str, SUPPORTED_AIRLINES, ContextTag
from services.rag.vector_store import get_policy_vector_store, get_embeddings
from utils.database import engine                                               
from models.airline import Airline                                              
from models.flight_promotion import FlightPromotion                             
from services.data_pipeline.pineline.policy_pipeline import PolicyETLPipeline
from services.data_pipeline.pineline.promo_pipeline import PromotionETLPipeline
from models.pipeline_run import PipelineRun
from repositories.crawler_staging_repo import CrawlerStagingRepository

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
def get_active_promotions(query: str, airline_codes: list[str] | None = None) -> str:
    """Tìm kiếm các chương trình khuyến mãi vé máy bay."""
    logger.info(f"[promo] query='{query}' airlines={airline_codes}")
    try:
        today        = get_current_time().date()
        today_str    = get_current_time_str()
        embeddings   = get_embeddings()
        query_vector = embeddings.embed_query(query)
 
        with Session(engine) as session:
            stmt = select(FlightPromotion)
            
            if airline_codes and "CLEAR" not in airline_codes:
                clean_codes = [c.strip().upper() for c in airline_codes if c]
                if clean_codes:
                    airline_objs = session.exec(
                        select(Airline).where(Airline.code.in_(clean_codes))
                    ).all()
                    
                    airline_ids = [al.id for al in airline_objs]
                    if airline_ids:
                        stmt = stmt.where(FlightPromotion.airline_id.in_(airline_ids))
 
            stmt = stmt.where(
                or_(
                    FlightPromotion.booking_end_date == None,
                    FlightPromotion.booking_end_date >= today,
                )
            ).order_by(
                FlightPromotion.embedding.cosine_distance(query_vector)
            ).limit(3)
            
            docs = list(session.exec(stmt).all())
 
        if not docs:
            return f"{ContextTag.SYS_NOT_FOUND}: Không có khuyến mãi phù hợp."
 
        result = f"{ContextTag.PROMO_INFO}\n- CÂU HỎI: '{query}'\n- NGÀY: {today_str}\n"
        for i, p in enumerate(docs, 1):
            b_end = p.booking_end_date.strftime("%d/%m/%Y") if p.booking_end_date else "Không giới hạn"
            result += (
                f"\n▶ {i}. {p.promo_name}\n"
                f"   - Mã: {p.promo_code or 'Tự động áp dụng'}\n"
                f"   - Hạn: {b_end}\n"
                f"   - Chi tiết: {p.description}\n"
                f"   - Điều kiện: {p.conditions}\n"
                f"   - [Link]: {p.url}\n"
            )
        return result.strip()
    except Exception as e:
        logger.exception("get_active_promotions error")
        return f"{ContextTag.SYS_ERROR}: Lỗi tra cứu khuyến mãi: {str(e)}"

# # ── Tool 3: run_policy_pipeline ───────────────────────────────────────────────
# @mcp.tool()
# def run_policy_pipeline() -> str:
#     """Chạy toàn bộ ETL pipeline cho chính sách: crawl → format → ingest vector DB."""
#     logger.info("[pipeline] Starting policy ETL in background...")
#     try:
#         def _run():
#             PolicyETLPipeline().run_pipeline()
#         threading.Thread(target=_run, daemon=True).start()
#         return "✅ Policy pipeline đã được kích hoạt chạy nền. Dùng get_pipeline_status() để theo dõi."
#     except Exception as e:
#         logger.exception("run_policy_pipeline error")
#         return f"❌ Lỗi: {str(e)}"

# # ── Tool 4: run_promo_pipeline ────────────────────────────────────────────────
# @mcp.tool()
# def run_promo_pipeline() -> str:
#     """Chạy toàn bộ ETL pipeline cho khuyến mãi: discover → crawl → extract → ingest."""
#     logger.info("[pipeline] Starting promo ETL in background...")
#     try:
#         def _run():
#             PromotionETLPipeline().run_pipeline()
#         threading.Thread(target=_run, daemon=True).start()
#         return "✅ Promo pipeline đã được kích hoạt chạy nền. Dùng get_pipeline_status() để theo dõi."
#     except Exception as e:
#         logger.exception("run_promo_pipeline error")
#         return f"❌ Lỗi: {str(e)}"

# # ── Tool 5: get_pipeline_status ───────────────────────────────────────────────
# @mcp.tool()
# def get_pipeline_status() -> str:
#     """Xem trạng thái các lần chạy pipeline gần nhất."""
#     try:
#         with Session(engine) as s:
#             runs = s.exec(
#                 select(PipelineRun)
#                 .order_by(PipelineRun.started_at.desc())
#                 .limit(5)
#             ).all()

#             counts = CrawlerStagingRepository(s).count_by_status()

#         lines = ["=== PIPELINE RUNS (5 gần nhất) ==="]
#         if not runs:
#             lines.append("  Chưa có lần chạy nào.")
#         else:
#             for r in runs:
#                 duration = ""
#                 if r.finished_at:
#                     secs = int((r.finished_at - r.started_at).total_seconds())
#                     duration = f" | {secs}s"
#                 lines.append(
#                     f"  [{r.pipeline_type.upper()}] {r.status.upper()}"
#                     f" | started={r.started_at.strftime('%Y-%m-%d %H:%M')}{duration}"
#                     f" | discovered={r.urls_discovered}"
#                     f" | crawled={r.urls_crawled}"
#                     f" | ingested={r.urls_ingested}"
#                 )
#                 if r.status == "failed" and r.error_message:
#                     lines.append(f"    ❌ {r.error_message[:100]}")

#         lines.append("\n=== STAGING STATUS ===")
#         for k, v in counts.items():
#             lines.append(f"  {k}: {v}")

#         return "\n".join(lines)
#     except Exception as e:
#         return f"❌ Lỗi: {str(e)}"

@mcp.tool()
def get_airline_info(airline_codes: list[str] | None = None) -> str:
    """
    Lấy thông tin tổng quan, ưu/nhược điểm và hành lý cơ bản của các hãng hàng không.
    Gọi tool này khi khách hàng yêu cầu so sánh các hãng bay hoặc hỏi thông tin về một hãng cụ thể.
    """
    logger.info(f"[airline_info] Requesting info for airlines: {airline_codes}")
    
    try:
        with Session(engine) as session:
            stmt = select(Airline)
            
            if airline_codes and len(airline_codes) > 0 and "CLEAR" not in airline_codes:
                clean_codes = [code.strip().upper() for code in airline_codes if code]
                if clean_codes:
                    stmt = stmt.where(Airline.code.in_(clean_codes))
            
            airlines = session.exec(stmt).all()
            
        if not airlines:
            return f"{ContextTag.SYS_NOT_FOUND}: Không tìm thấy thông tin hãng bay trong cơ sở dữ liệu."

        lines = [f"{ContextTag.POLICY_INFO}\n[THÔNG TIN TỔNG QUAN VỀ HÃNG BAY]"]
        
        for al in airlines:
            lines.append(f"\n▶ HÃNG: {al.name} (Mã: {al.code})")
            
            if getattr(al, 'description', None):
                lines.append(f"  - Giới thiệu: {al.description}")
                
            if getattr(al, 'pros', None):
                lines.append(f"  - Ưu điểm: {al.pros}")
                
            if getattr(al, 'cons', None):
                lines.append(f"  - Nhược điểm/Lưu ý: {al.cons}")
                
            if getattr(al, 'baggage_basic_info', None):
                lines.append(f"  - Hành lý cơ bản: {al.baggage_basic_info}")
                
        return "\n".join(lines)
        
    except Exception as e:
        logger.exception("get_airline_info error")
        return f"{ContextTag.SYS_ERROR}: Lỗi truy xuất thông tin hãng bay: {str(e)}"