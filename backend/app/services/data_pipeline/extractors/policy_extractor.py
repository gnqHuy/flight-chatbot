import time
import logging
from sqlmodel import Session

from app.services.data_pipeline.extractors.crawlers.crawler_for_VJ import crawl_vj_policy
from app.services.data_pipeline.extractors.crawlers.crawler_for_VN import crawl_vn_policy
from app.services.data_pipeline.extractors.crawlers.crawler_for_QH import crawl_qh_policy

from app.repositories.crawler_url_repo import CrawlerUrlRepository
from app.repositories.crawler_staging_repo import CrawlerStagingRepository
from app.database.models.crawler_url import UrlType

logger = logging.getLogger(__name__)

class PolicyExtractor:
    def __init__(self, session: Session):
        self.session = session
        self.url_repo = CrawlerUrlRepository(self.session)
        self.staging_repo = CrawlerStagingRepository(self.session)
        
    def extract_all(self):
        logger.info("🕸️ BẮT ĐẦU CÀO DỮ LIỆU CHÍNH SÁCH VÀO DATABASE STAGING...")
        
        policy_urls = self.url_repo.get_active_urls(url_type=UrlType.POLICY_PAGE)
        
        total_links = len(policy_urls)
        processed = 0
        
        for url_obj in policy_urls:
            processed += 1
            
            existing_staging = self.staging_repo.get_by_url_id(url_obj.id)
            if existing_staging and existing_staging.status != "error":
                continue

            airline_code = url_obj.airline.code
            category = url_obj.category or "general_policy"
            url_string = url_obj.url

            logger.info(f"[{processed}/{total_links}] Đang cào [{airline_code}] - {category}: {url_string}")
            
            clean_text = None
            try:
                if airline_code == "VN":
                    clean_text = crawl_vn_policy(url_string)
                elif airline_code == "VJ":
                    clean_text = crawl_vj_policy(url_string)
                elif airline_code == "QH":
                    clean_text = crawl_qh_policy(url_string)
                
                if clean_text and clean_text.strip():
                    self.staging_repo.save_raw_content(
                        url_id=url_obj.id,
                        airline_id=url_obj.airline_id,
                        raw_text=clean_text
                    )
                    
                    url_obj.last_crawled_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.session.add(url_obj)
                    
                    self.session.commit()
                    logger.info(f"✅ Đã nạp Staging cho Policy ID: {url_obj.id}")
                else:
                    logger.warning(f"⚠️ Nội dung trống tại: {url_string}")

            except Exception as e:
                self.session.rollback()
                logger.error(f"❌ Lỗi khi cào Policy {url_string}: {str(e)}")
                if existing_staging:
                    self.staging_repo.mark_as_error(existing_staging.id, str(e))
                    self.session.commit()
            
            time.sleep(2)
            
        logger.info("✅ HOÀN TẤT CÀO CHÍNH SÁCH VÀO DB!")
        return True