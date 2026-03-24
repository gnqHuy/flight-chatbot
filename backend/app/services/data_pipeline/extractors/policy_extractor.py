import os
import time
import logging

from app.services.data_pipeline.extractors.crawlers.crawler_for_VJ import crawl_vj_policy
from app.services.data_pipeline.extractors.crawlers.crawler_for_VN import crawl_vn_policy
from app.services.data_pipeline.extractors.crawlers.crawler_for_QH import crawl_qh_policy
from app.services.data_pipeline.extractors.source_urls.policy_urls import POLICY_URLS

logger = logging.getLogger(__name__)

class PolicyExtractor:
    def __init__(self):
        self.raw_data_dir = os.path.join("app", "data", "policies", "raws")
        
    def extract_all(self):
        logger.info("🕸️ BƯỚC 1: BẮT ĐẦU CÀO DỮ LIỆU CHÍNH SÁCH...")
        
        total_links = sum(len(links) for links in POLICY_URLS.values())
        processed = 0
        
        for airline, categories in POLICY_URLS.items():
            airline_dir = os.path.join(self.raw_data_dir, airline)
            os.makedirs(airline_dir, exist_ok=True)
            
            for category, url in categories.items():
                processed += 1
                file_path = os.path.join(airline_dir, f"{category}.txt")
                
                if os.path.exists(file_path):
                    continue
                    
                logger.info(f"[{processed}/{total_links}] Đang cào [{airline}] - {category}")
                
                clean_text = None
                if airline == "VN":
                    clean_text = crawl_vn_policy(url)
                elif airline == "VJ":
                    clean_text = crawl_vj_policy(url)
                elif airline == "QH":
                    clean_text = crawl_qh_policy(url)
                
                if clean_text:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"HÃNG: {airline.upper()}\n")
                        f.write(f"CHỦ ĐỀ: {category}\n")
                        f.write(f"NGUỒN: {url}\n")
                        f.write("-" * 40 + "\n\n")
                        f.write(clean_text)
                
                time.sleep(2)
                
        logger.info("✅ HOÀN TẤT CÀO CHÍNH SÁCH!")
        return True