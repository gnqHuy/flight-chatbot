import logging

from app.services.data_pipeline.extractors.promo_extractor import PromoExtractor
from app.services.data_pipeline.ingest.promo_ingester import PromoDBIngester
from app.services.data_pipeline.post_processing.post_processing_promo import PromoLLMExtractor
    
logger = logging.getLogger(__name__)

class PromotionETLPipeline:
    def __init__(self):
        self.crawler = PromoExtractor()
        self.transformer = PromoLLMExtractor()
        self.loader = PromoDBIngester()

    def run_pipeline(self):
        print("="*50)
        print("🚀 BẮT ĐẦU PIPELINE KHUYẾN MÃI (PROMOTION ETL)")
        print("="*50)
        try:
            self.crawler.extract_all()
            
            cleaned_json_path = self.transformer.process()
            
            if cleaned_json_path:
                self.loader.ingest_to_db(json_path=cleaned_json_path)
            else:
                print("⚠️ Bỏ qua bước Nạp DB vì không có dữ liệu JSON được tạo ra.")
                
            print("\n🎉 HOÀN TẤT TOÀN BỘ PIPELINE KHUYẾN MÃI!\n")
            return True
        except Exception as e:
            print(f"\n❌ PIPELINE KHUYẾN MÃI THẤT BẠI: {e}\n")
            return False