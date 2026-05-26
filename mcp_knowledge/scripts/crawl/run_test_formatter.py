import logging
import sys
from sqlmodel import Session

# Import kết nối DB của bạn
from app.database.database import engine 

# Import 2 class Formatter mà chúng ta vừa viết
# (Nhớ sửa lại đường dẫn import cho đúng với cấu trúc thư mục thực tế của bạn nhé)
from app.services.data_pipeline.post_processing.post_processing_policies import PolicyLLMFormatter
from app.services.data_pipeline.post_processing.post_processing_promo import PromoLLMExtractor

# Cấu hình logging hiển thị màu mè và rõ ràng trên Terminal
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("TestFormatter")

def run_formatter_test():
    # Mở phiên làm việc với Database
    with Session(engine) as session:
        try:
            logger.info("🚀 BẮT ĐẦU CHẠY THỬ NGHIỆM HỆ THỐNG LLM FORMATTER (PHA 2)")
            logger.info("=" * 60)

            # --- 1. TEST CHUẨN HÓA CHÍNH SÁCH (POLICY) ---
            logger.info("🔹 Đang khởi động PolicyLLMFormatter (Chuyển Text -> Markdown)...")
            policy_formatter = PolicyLLMFormatter(session)
            policy_formatter.process()
            
            logger.info("-" * 60)

            # --- 2. TEST BÓC TÁCH KHUYẾN MÃI (PROMO) ---
            logger.info("🔹 Đang khởi động PromoLLMExtractor (Chuyển Text -> JSON)...")
            promo_extractor = PromoLLMExtractor(session)
            promo_extractor.process()

            logger.info("=" * 60)
            logger.info("🎉 TẤT CẢ CÁC LUỒNG BÓC TÁCH LLM ĐÃ CHẠY XONG!")
            
        except Exception as e:
            logger.error(f"❌ Có lỗi nghiêm trọng xảy ra: {e}")
            session.rollback()

if __name__ == "__main__":
    run_formatter_test()