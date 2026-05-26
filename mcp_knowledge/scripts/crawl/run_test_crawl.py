import logging
import sys
from sqlmodel import Session

from app.database.database import engine
from app.services.data_pipeline.extractors.policy_extractor import PolicyExtractor
from app.services.data_pipeline.extractors.promo_extractor import PromoExtractor

# Cấu hình logging để thấy được tiến trình cào ngay trên Terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TestCrawl")

def run_test():
    # 1. Khởi tạo Session
    # Lưu ý: Đảm bảo bạn đã chạy migration hoặc create_all để có bảng trong DB
    with Session(engine) as session:
        try:
            logger.info("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM HỆ THỐNG CRAWLER")
            logger.info("-" * 50)

            # --- TEST LUỒNG PROMOTION ---
            logger.info("🔹 Đang chạy PromoExtractor...")
            promo_worker = PromoExtractor(session)
            # Hàm này sẽ tự gọi discover_promo_urls() bên trong nó
            promo_worker.extract_all()
            logger.info("✅ Hoàn tất test Promotion.")

            logger.info("-" * 50)
            logger.info("🎉 TẤT CẢ CÁC LUỒNG ĐÃ CHẠY XONG!")
            
        except Exception as e:
            logger.error(f"❌ Lỗi trong quá trình test: {e}")
            session.rollback()

if __name__ == "__main__":
    run_test()