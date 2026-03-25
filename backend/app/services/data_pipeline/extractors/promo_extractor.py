import time
import logging
from sqlmodel import Session

from app.services.data_pipeline.extractors.crawlers.crawler_for_VN import extract_vn_promo_text, get_vn_promo_urls
from app.services.data_pipeline.extractors.crawlers.crawler_for_QH import get_qh_promo_urls, extract_qh_promo_text
from app.services.data_pipeline.extractors.crawlers.crawler_for_VJ import extract_vj_promo_text, get_vj_promo_urls

from app.repositories.crawler_url_repo import CrawlerUrlRepository
from app.repositories.crawler_staging_repo import CrawlerStagingRepository
from app.database.models.crawler_url import CrawlerUrl, UrlType

logger = logging.getLogger(__name__)

class PromoExtractor:
    def __init__(self, session: Session):
        self.session = session
        self.url_repo = CrawlerUrlRepository(self.session)
        self.staging_repo = CrawlerStagingRepository(self.session)
        
    def discover_promo_urls(self):
        """
        Bước 1: Quét các trang tổng hợp (PROMO_LIST_PAGE) để tìm link khuyến mãi mới.
        """
        logger.info("🔍 [STEP 1] ĐANG TÌM KIẾM CÁC LINK KHUYẾN MÃI MỚI...")
        
        list_pages = self.url_repo.get_active_urls(url_type=UrlType.PROMO_LIST_PAGE)
        
        for page in list_pages:
            airline_code = page.airline.code
            logger.info(f"Đang quét danh sách của {airline_code}: {page.url}")
            
            discovered_links = []
            if airline_code == "VN":
                discovered_links = get_vn_promo_urls(page.url)
            elif airline_code == "VJ":
                discovered_links = get_vj_promo_urls(page.url)
            elif airline_code == "QH":
                discovered_links = get_qh_promo_urls(page.url)
            
            added_count = 0
            existing_urls_in_db = {u.url for u in self.url_repo.get_urls_by_airline(page.airline_id)}
            
            for link in discovered_links:
                if link not in existing_urls_in_db:
                    new_promo_url = CrawlerUrl(
                        airline_id=page.airline_id,
                        url_type=UrlType.PROMO_PAGE,
                        category="promotion",
                        url=link,
                        is_active=True
                    )
                    self.session.add(new_promo_url)
                    added_count += 1
            
            self.session.commit()
            logger.info(f"✨ {airline_code}: Tìm thấy {len(discovered_links)} link, đã thêm {added_count} link mới vào DB.")

    def extract_all(self):
        """
        Bước 2: Cào nội dung chi tiết từ các link PROMO_PAGE và lưu vào CrawlerStaging.
        """
        self.discover_promo_urls()
        
        logger.info("🕸️ [STEP 2] BẮT ĐẦU CÀO NỘI DUNG VÀ LƯU VÀO DATABASE STAGING...")
        
        promo_urls = self.url_repo.get_active_urls(url_type=UrlType.PROMO_PAGE)
        total_links = len(promo_urls)
        processed = 0
        
        for url_obj in promo_urls:
            processed += 1
            
            existing_staging = self.staging_repo.get_by_url_id(url_obj.id)
            if existing_staging and existing_staging.status != "error":
                continue
                
            airline = url_obj.airline.code
            url = url_obj.url
            
            logger.info(f"[{processed}/{total_links}] Đang cào [{airline}]: {url}")
            
            clean_text = None
            try:
                if airline == "QH":
                    clean_text = extract_qh_promo_text(url)
                elif airline == "VN":
                    clean_text = extract_vn_promo_text(url)
                elif airline == "VJ":
                    clean_text = extract_vj_promo_text(url)
                
                if clean_text and clean_text.strip():
                    self.staging_repo.save_raw_content(
                        url_id=url_obj.id,
                        airline_id=url_obj.airline_id,
                        raw_text=clean_text
                    )
                    
                    url_obj.last_crawled_at = time.strftime('%Y-%m-%d %H:%M:%S')
                    self.session.add(url_obj)
                    
                    self.session.commit()
                    logger.info(f"✅ Đã nạp Staging thành công cho ID: {url_obj.id}")
                else:
                    logger.warning(f"⚠️ Nội dung trống tại {url}")
                    
            except Exception as e:
                self.session.rollback()
                logger.error(f"❌ Lỗi khi xử lý link ID {url_obj.id}: {str(e)}")
                if existing_staging:
                    self.staging_repo.mark_as_error(existing_staging.id, str(e))
                    self.session.commit()
                
            time.sleep(2)

        logger.info("✅ HOÀN TẤT VIỆC NẠP DỮ LIỆU KHUYẾN MÃI VÀO DB STAGING!")
        return True