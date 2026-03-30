import logging
from sqlmodel import Session

from app.database.database import engine 
from app.services.data_pipeline.extractors.policy_extractor import PolicyExtractor
from app.services.data_pipeline.ingest.policy_ingester import PolicyDBIngester
from app.services.data_pipeline.post_processing.post_processing_policies import PolicyLLMFormatter
    
logger = logging.getLogger(__name__)

class PolicyETLPipeline:
    def __init__(self):
        self.crawler = PolicyExtractor()

    def run_pipeline(self):
        logger.info("="*50)
        logger.info("🚀 BẮT ĐẦU PIPELINE CHÍNH SÁCH (POLICY ETL)")
        logger.info("="*50)
        
        try:
            self.crawler.extract_all()
            
            with Session(engine) as session:
                transformer = PolicyLLMFormatter(session)
                loader = PolicyDBIngester(session)
                
                transformer.process()
                
                loader.ingest_to_db()
                
            logger.info("\n🎉 HOÀN TẤT TOÀN BỘ PIPELINE CHÍNH SÁCH!\n")
            return True
            
        except Exception as e:
            logger.error(f"\n❌ PIPELINE CHÍNH SÁCH THẤT BẠI: {e}\n")
            return False