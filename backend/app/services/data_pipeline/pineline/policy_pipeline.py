import logging

from app.services.data_pipeline.extractors.policy_extractor import PolicyExtractor
from app.services.data_pipeline.ingest.policy_ingester import PolicyDBIngester
from app.services.data_pipeline.post_processing.post_processing_policies import PolicyLLMFormatter
    
logger = logging.getLogger(__name__)

class PolicyETLPipeline:
    def __init__(self):
        self.crawler = PolicyExtractor()
        self.transformer = PolicyLLMFormatter()
        self.loader = PolicyDBIngester()

    def run_pipeline(self):
        print("="*50)
        print("🚀 BẮT ĐẦU PIPELINE CHÍNH SÁCH (POLICY ETL)")
        print("="*50)
        try:
            self.crawler.extract_all()
            
            self.transformer.process()
            
            self.loader.ingest_to_db()
                
            print("\n🎉 HOÀN TẤT TOÀN BỘ PIPELINE CHÍNH SÁCH!\n")
            return True
        except Exception as e:
            print(f"\n❌ PIPELINE CHÍNH SÁCH THẤT BẠI: {e}\n")
            return False