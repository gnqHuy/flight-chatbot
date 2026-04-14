import logging
from sqlmodel import Session
from utils.database import engine
from services.data_pipeline.extractors.policy_extractor import PolicyExtractor
from services.data_pipeline.ingest.policy_ingester import PolicyDBIngester
from services.data_pipeline.post_processing.post_processing_policies import PolicyLLMFormatter

logger = logging.getLogger(__name__)

class PolicyETLPipeline:
    def run_pipeline(self):
        logger.info("🚀 BẮT ĐẦU PIPELINE CHÍNH SÁCH")
        try:
            with Session(engine) as s:
                PolicyExtractor(s).extract_all()    # FIX [17]: truyền session
            with Session(engine) as s:
                PolicyLLMFormatter(s).process()
            with Session(engine) as s:
                PolicyDBIngester(s).ingest_to_db()
            logger.info("🎉 HOÀN TẤT PIPELINE CHÍNH SÁCH")
            return True
        except Exception as e:
            logger.error(f"❌ PIPELINE THẤT BẠI: {e}")
            return False