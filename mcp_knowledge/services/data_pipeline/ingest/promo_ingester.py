import logging
from datetime import datetime
from sqlmodel import Session, select
from langchain_openai import OpenAIEmbeddings

from constants import OPENAI_API_KEY
from models.crawler_staging import CrawlerStaging
from models.crawler_url import CrawlerUrl, UrlType
from models.flight_promotion import FlightPromotion
from models.enums import StagingStatus

logger = logging.getLogger(__name__)


class PromoDBIngester:
    def __init__(self, session: Session):
        self.session  = session
        self.embedder = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )

    def _parse_date(self, date_str):
        if not date_str or str(date_str).lower() in ("null", "none", ""):
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def ingest_to_db(self, run_id: str = None) -> int:
        """
        Nạp promo vào DB với upsert theo (airline_id, url).
        Nếu có run_id → chỉ xử lý tasks của lần chạy đó.
        Trả về số records ingested.
        """
        logger.info("🗄️ BƯỚC 3: NẠP DỮ LIỆU KHUYẾN MÃI VÀO DATABASE...")

        stmt = (
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.LLM_FORMATTED)
            .where(CrawlerUrl.url_type == UrlType.PROMO_PAGE)
        )
        if run_id:
            stmt = stmt.where(CrawlerStaging.pipeline_run_id == run_id)

        ready_tasks = self.session.exec(stmt).all()
        if not ready_tasks:
            logger.warning("⚠️ Không có Promo nào ở trạng thái LLM_FORMATTED")
            return 0

        logger.info(f"🚀 Xử lý {len(ready_tasks)} promos...")

        texts_to_embed = []
        tasks_meta     = []

        for task in ready_tasks:
            if not task.formatted_data:
                continue
            promo_data = task.formatted_data.copy()
            metadata   = promo_data.pop("metadata", {})
            promo_data["airline_id"] = metadata.get("airline_id")
            promo_data["url"]        = metadata.get("source_url", "UNKNOWN")

            rag_text = (
                f"Tên khuyến mãi: {promo_data.get('promo_name', '')}\n"
                f"Mô tả: {promo_data.get('description', '')}\n"
                f"Điều kiện: {promo_data.get('conditions', '')}"
            )
            texts_to_embed.append(rag_text)
            tasks_meta.append((task, promo_data))

        if not texts_to_embed:
            logger.warning("⚠️ Không có text để embed")
            return 0

        try:
            embeddings = self.embedder.embed_documents(texts_to_embed)
        except Exception as e:
            logger.error(f"❌ Embedding failed: {e}")
            return 0

        success = error = 0
        for (task, promo_data), embedding in zip(tasks_meta, embeddings):
            try:
                self._upsert(promo_data, embedding)
                task.status = StagingStatus.COMPLETED
                self.session.add(task)
                self.session.commit()
                success += 1
            except Exception as e:
                self.session.rollback()
                logger.error(f"❌ Upsert failed {promo_data.get('url')}: {e}")
                task.status        = StagingStatus.ERROR
                task.error_message = str(e)
                self.session.add(task)
                self.session.commit()
                error += 1

        logger.info(f"✅ Done: {success} upserted, {error} errors")
        return success

    def _upsert(self, promo_data: dict, embedding: list[float]):
        """INSERT nếu chưa có, UPDATE nếu đã có (theo url)."""
        url        = promo_data.get("url", "UNKNOWN")
        airline_id = promo_data.get("airline_id")

        existing = self.session.exec(
            select(FlightPromotion).where(FlightPromotion.url == url)
        ).first()

        if existing:
            existing.promo_name          = promo_data.get("promo_name", existing.promo_name)
            existing.promo_code          = promo_data.get("promo_code")
            existing.booking_start_date  = self._parse_date(promo_data.get("booking_start_date"))
            existing.booking_end_date    = self._parse_date(promo_data.get("booking_end_date"))
            existing.travel_start_date   = self._parse_date(promo_data.get("travel_start_date"))
            existing.travel_end_date     = self._parse_date(promo_data.get("travel_end_date"))
            existing.description         = promo_data.get("description", existing.description)
            existing.conditions          = promo_data.get("conditions", existing.conditions)
            existing.embedding           = embedding
            existing.updated_at          = datetime.now()
            self.session.add(existing)
            logger.debug(f"  ↺ Updated: {existing.promo_name}")
        else:
            self.session.add(FlightPromotion(
                airline_id=airline_id,
                url=url,
                promo_name         = promo_data.get("promo_name", ""),
                promo_code         = promo_data.get("promo_code"),
                booking_start_date = self._parse_date(promo_data.get("booking_start_date")),
                booking_end_date   = self._parse_date(promo_data.get("booking_end_date")),
                travel_start_date  = self._parse_date(promo_data.get("travel_start_date")),
                travel_end_date    = self._parse_date(promo_data.get("travel_end_date")),
                description        = promo_data.get("description", ""),
                conditions         = promo_data.get("conditions", ""),
                embedding          = embedding,
            ))
            logger.debug(f"  + Inserted: {promo_data.get('promo_name')}")