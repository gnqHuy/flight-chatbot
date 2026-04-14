import logging
from sqlmodel import Session
from utils.database import engine                                           # FIX
from services.data_pipeline.extractors.promo_extractor import PromoExtractor
from services.data_pipeline.ingest.promo_ingester import PromoDBIngester
from services.data_pipeline.post_processing.post_processing_promo import PromoLLMExtractor  # FIX [19]

logger = logging.getLogger(__name__)

class PromotionETLPipeline:
    def run_pipeline(self):
        logger.info("🚀 BẮT ĐẦU PIPELINE KHUYẾN MÃI")
        try:
            with Session(engine) as s:
                PromoExtractor(s).extract_all()     # FIX [17]: truyền session
            with Session(engine) as s:
                PromoLLMExtractor(s).process()
            with Session(engine) as s:
                PromoDBIngester(s).ingest_to_db()
            logger.info("🎉 HOÀN TẤT PIPELINE KHUYẾN MÃI")
            return True
        except Exception as e:
            logger.error(f"❌ PIPELINE THẤT BẠI: {e}")
            return False