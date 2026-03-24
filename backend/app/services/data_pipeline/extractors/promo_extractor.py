import os
import time
import logging
from app.services.data_pipeline.extractors.crawlers.crawler_for_VN import extract_vn_promo_text, get_vn_promo_urls
from app.services.data_pipeline.extractors.crawlers.crawler_for_QH import get_qh_promo_urls, extract_qh_promo_text
from app.services.data_pipeline.extractors.crawlers.crawler_for_VJ import extract_vj_promo_text, get_vj_promo_urls

logger = logging.getLogger(__name__)

class PromoExtractor:
    def __init__(self):
        self.raw_data_dir = os.path.join("app", "data", "promotions", "raws")
        
    def extract_all(self):
        logger.info("🕸️ BƯỚC 1: BẮT ĐẦU CÀO DỮ LIỆU KHUYẾN MÃI TỪ CÁC HÃNG...")
        
        all_promos = []
        
        logger.info("Đang lấy URLs của Bamboo Airways (QH)...")
        all_promos.extend(get_qh_promo_urls())
        
        logger.info("Đang lấy URLs của Vietnam Airlines (VN)...")
        all_promos.extend(get_vn_promo_urls())
        
        logger.info("Đang lấy URLs của Vietjet Air (VJ)...")
        all_promos.extend(get_vj_promo_urls())
        
        total_links = len(all_promos)
        logger.info(f"Tổng cộng tìm thấy {total_links} links khuyến mãi.")

        processed = 0
        for promo in all_promos:
            airline = promo["airline"]
            url = promo["url"]
            processed += 1
            
            airline_dir = os.path.join(self.raw_data_dir, airline)
            os.makedirs(airline_dir, exist_ok=True)
            
            file_name = f"promo_{processed:03d}.txt"
            file_path = os.path.join(airline_dir, file_name)
            
            if os.path.exists(file_path):
                logger.info(f"[{processed}/{total_links}] ⏭️ Bỏ qua (Đã có sẵn): {file_name}")
                continue
                
            logger.info(f"[{processed}/{total_links}] Đang cào [{airline}]: {url}")
            
            clean_text = None
            if airline == "QH":
                clean_text = extract_qh_promo_text(url)
            elif airline == "VN":
                clean_text = extract_vn_promo_text(url)
            elif airline == "VJ":
                clean_text = extract_vj_promo_text(url)
            
            if clean_text and clean_text.strip():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"HÃNG: {airline.upper()}\n")
                    f.write(f"FILE: {file_name}\n")
                    f.write(f"NGUỒN: {url}\n")
                    f.write("-" * 40 + "\n\n")
                    f.write(clean_text)
            else:
                logger.warning(f"❌ THẤT BẠI HOẶC RỖNG: {url}")
                
            time.sleep(2)

        logger.info("✅ HOÀN TẤT VIỆC CÀO HTML KHUYẾN MÃI!")
        return True