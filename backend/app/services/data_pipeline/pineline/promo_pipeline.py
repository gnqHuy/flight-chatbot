import logging
from sqlmodel import Session

from app.database.database import engine 
from app.services.data_pipeline.extractors.promo_extractor import PromoExtractor
from app.services.data_pipeline.ingest.promo_ingester import PromoDBIngester
from app.services.data_pipeline.post_processing.post_processing_promo import PromoLLMExtractor
    
logger = logging.getLogger(__name__)

class PromotionETLPipeline:
    def __init__(self):
        self.crawler = PromoExtractor()

    def run_pipeline(self):
        logger.info("="*50)
        logger.info("🚀 BẮT ĐẦU PIPELINE KHUYẾN MÃI (PROMOTION ETL)")
        logger.info("="*50)
        
        try:
            self.crawler.extract_all()
            
            with Session(engine) as session:
                transformer = PromoLLMExtractor(session)
                loader = PromoDBIngester(session)
                
                transformer.process()
                
                loader.ingest_to_db()
                
            logger.info("\n🎉 HOÀN TẤT TOÀN BỘ PIPELINE KHUYẾN MÃI!\n")
            return True
            
        except Exception as e:
            logger.error(f"\n❌ PIPELINE KHUYẾN MÃI THẤT BẠI: {e}\n")
            return False