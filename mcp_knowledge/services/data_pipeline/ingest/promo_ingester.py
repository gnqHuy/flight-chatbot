import logging
from datetime import datetime
from sqlmodel import Session, select
from langchain_openai import OpenAIEmbeddings

from app.core.config import OPENAI_API_KEY
from app.database.models.crawler_staging import CrawlerStaging
from app.database.models.crawler_url import CrawlerUrl, UrlType
from app.database.models.flight_promotion import FlightPromotion
from app.core.enums import StagingStatus

logger = logging.getLogger(__name__)

class PromoDBIngester:
    def __init__(self, session: Session):
        self.session = session
        self.embedder = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            api_key=OPENAI_API_KEY
        )

    def _parse_date(self, date_str):
        if not date_str or date_str.lower() == "null":
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def ingest_to_db(self):
        logger.info("🗄️ BƯỚC 3: BẮT ĐẦU NẠP DỮ LIỆU KHUYẾN MÃI VÀO DATABASE...")

        statement = (
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.LLM_FORMATTED)
            .where(CrawlerUrl.url_type == UrlType.PROMO_PAGE)
        )
        
        ready_tasks = self.session.exec(statement).all()

        if not ready_tasks:
            logger.warning("⚠️ Không có dữ liệu Khuyến mãi nào ở trạng thái LLM_FORMATTED để nạp.")
            return False

        logger.info(f"🚀 Bắt đầu xử lý {len(ready_tasks)} bài viết khuyến mãi...")

        promotions_to_process = []
        texts_to_embed = []
        tasks_to_update = []

        for task in ready_tasks:
            if not task.formatted_data:
                continue

            promo_data = task.formatted_data.copy()
            metadata = promo_data.pop("metadata", {})
            promo_data["airline_id"] = metadata.get("airline_id") 
            promo_data["url"] = metadata.get("source_url", "UNKNOWN")

            promo_name = promo_data.get('promo_name', '')
            description = promo_data.get('description', '')
            conditions = promo_data.get('conditions', '')

            rag_text = f"Tên khuyến mãi: {promo_name}\nMô tả: {description}\nĐiều kiện áp dụng: {conditions}"
            
            texts_to_embed.append(rag_text)
            promotions_to_process.append(promo_data)
            tasks_to_update.append(task)

        if not texts_to_embed:
            logger.warning("⚠️ Không có dữ liệu hợp lệ để nạp.")
            return False

        logger.info("🧠 Đang gọi OpenAI API để tạo Vector Embeddings (Vui lòng đợi)...")
        try:
            embeddings_list = self.embedder.embed_documents(texts_to_embed)
            logger.info("   ✅ Đã lấy xong Vector Embeddings!")
        except Exception as e:
            logger.error(f"❌ Lỗi khi gọi OpenAI Embeddings: {e}")
            return False

        logger.info("🗄️ Đang lưu dữ liệu vào bảng FlightPromotion...")
        try:
            for idx, promo in enumerate(promotions_to_process):
                db_promo = FlightPromotion(
                    airline_id=promo.get("airline_id"),
                    promo_code=promo.get("promo_code"),
                    promo_name=promo.get("promo_name"),
                    booking_start_date=self._parse_date(promo.get("booking_start_date")),
                    booking_end_date=self._parse_date(promo.get("booking_end_date")),
                    travel_start_date=self._parse_date(promo.get("travel_start_date")),
                    travel_end_date=self._parse_date(promo.get("travel_end_date")),
                    description=promo.get("description"),
                    conditions=promo.get("conditions"),
                    url=promo.get("url"),
                    embedding=embeddings_list[idx] 
                )
                self.session.add(db_promo)
                
                tasks_to_update[idx].status = StagingStatus.COMPLETED
                self.session.add(tasks_to_update[idx])

            self.session.commit()
            logger.info("🎉 THÀNH CÔNG! Đã lưu toàn bộ khuyến mãi vào bảng 'flight_promotions' và cập nhật Staging.")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Lỗi khi nạp DB Khuyến mãi: {e}")
            return False