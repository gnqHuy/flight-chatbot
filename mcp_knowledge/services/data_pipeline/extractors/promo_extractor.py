import time, logging
from sqlmodel import Session
from repositories.crawler_url_repo import CrawlerUrlRepository      # FIX
from repositories.crawler_staging_repo import CrawlerStagingRepository
from models.crawler_url import CrawlerUrl
from models.enums import UrlType
from services.data_pipeline.extractors.crawlers.crawler_for_VJ import get_vj_promo_urls, extract_vj_promo_text
from services.data_pipeline.extractors.crawlers.crawler_for_VN import get_vn_promo_urls, extract_vn_promo_text
from services.data_pipeline.extractors.crawlers.crawler_for_QH import get_qh_promo_urls, extract_qh_promo_text

logger = logging.getLogger(__name__)

URL_CRAWLERS     = {"VN": get_vn_promo_urls,     "VJ": get_vj_promo_urls,     "QH": get_qh_promo_urls}
CONTENT_CRAWLERS = {"VN": extract_vn_promo_text, "VJ": extract_vj_promo_text, "QH": extract_qh_promo_text}

class PromoExtractor:
    def __init__(self, session: Session):
        self.session      = session
        self.url_repo     = CrawlerUrlRepository(session)
        self.staging_repo = CrawlerStagingRepository(session)

    def discover_promo_urls(self):
        logger.info("Discovering promo URLs...")
        for page in self.url_repo.get_active_urls(url_type=UrlType.PROMO_LIST_PAGE):
            code = page.airline.code
            discovered = URL_CRAWLERS.get(code, lambda u: [])(page.url)
            existing = {u.url for u in self.url_repo.get_urls_by_airline(page.airline_id)}
            added = 0
            for link in discovered:
                if link not in existing:
                    self.session.add(CrawlerUrl(
                        airline_id=page.airline_id, url_type=UrlType.PROMO_PAGE,
                        category="promotion", url=link, is_active=True,
                    ))
                    added += 1
            self.session.commit()
            logger.info(f"  {code}: {len(discovered)} found, {added} new")

    def extract_all(self):
        self.discover_promo_urls()
        logger.info("Starting promo content crawl...")
        urls = self.url_repo.get_active_urls(url_type=UrlType.PROMO_PAGE)
        for i, url_obj in enumerate(urls, 1):
            existing = self.staging_repo.get_by_url_id(url_obj.id)
            if existing and existing.status.value != "ERROR":
                continue
            code = url_obj.airline.code
            logger.info(f"[{i}/{len(urls)}] [{code}] {url_obj.url}")
            try:
                text = CONTENT_CRAWLERS.get(code, lambda u: "")(url_obj.url)
                if text and text.strip():
                    self.staging_repo.save_raw_content(url_obj.id, url_obj.airline_id, text)
                    url_obj.last_crawled_at = time.strftime("%Y-%m-%d %H:%M:%S")
                    self.session.add(url_obj)
                    self.session.commit()
                else:
                    logger.warning(f"  ⚠️ Empty: {url_obj.url}")
            except Exception as e:
                self.session.rollback()
                logger.error(f"  ❌ Error: {e}")
                if existing:
                    self.staging_repo.mark_as_error(existing.id, str(e))
                    self.session.commit()
            time.sleep(2)
        return True