import logging
import sys
from sqlmodel import Session

# Import kết nối DB
from app.database.database import engine
from app.services.data_pipeline.ingest.policy_ingester import PolicyDBIngester
from app.services.data_pipeline.ingest.promo_ingester import PromoDBIngester 


# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TestIngester")

def run_ingester_test():
    with Session(engine) as session:
        try:
            logger.info("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM HỆ THỐNG VECTOR INGESTER (PHA 3)")
            logger.info("=" * 60)

            # --- 1. TEST NẠP VECTOR CHÍNH SÁCH (POLICY) ---
            logger.info("🔹 Đang khởi động PolicyDBIngester...")
            policy_ingester = PolicyDBIngester(session)
            policy_ingester.ingest_to_db()
            
            logger.info("-" * 60)

            # --- 2. TEST NẠP VECTOR KHUYẾN MÃI (PROMO) ---
            logger.info("🔹 Đang khởi động PromoDBIngester...")
            promo_ingester = PromoDBIngester(session)
            promo_ingester.ingest_to_db()

            logger.info("=" * 60)
            logger.info("🎉 TẤT CẢ CÁC LUỒNG NẠP VECTOR ĐÃ CHẠY XONG! HỆ THỐNG RAG ĐÃ SẴN SÀNG.")
            
        except Exception as e:
            logger.error(f"❌ Có lỗi nghiêm trọng xảy ra: {e}")
            session.rollback()

if __name__ == "__main__":
    run_ingester_test()