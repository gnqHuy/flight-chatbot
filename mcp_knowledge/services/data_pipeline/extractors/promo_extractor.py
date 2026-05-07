import time
import logging
from datetime import datetime
from sqlmodel import Session

from repositories.crawler_url_repo import CrawlerUrlRepository
from repositories.crawler_staging_repo import CrawlerStagingRepository
from models.crawler_url import CrawlerUrl
from models.enums import UrlType, StagingStatus

from services.data_pipeline.extractors.crawlers.crawler_for_VJ import get_vj_promo_urls
from services.data_pipeline.extractors.crawlers.crawler_for_VN import get_vn_promo_urls
from services.data_pipeline.extractors.crawlers.crawler_for_QH import get_qh_promo_urls
from services.data_pipeline.crawling.html_fetcher import fetch_html
from services.data_pipeline.scraping.content_extractor import extract_content

logger = logging.getLogger(__name__)

URL_CRAWLERS = {
    "VN": get_vn_promo_urls,
    "VJ": get_vj_promo_urls,
    "QH": get_qh_promo_urls,
}


class PromoExtractor:
    def __init__(self, session: Session):
        self.session      = session
        self.url_repo     = CrawlerUrlRepository(session)
        self.staging_repo = CrawlerStagingRepository(session)

    def discover_promo_urls(self) -> int:
        """Discover promo URLs từ PROMO_LIST_PAGE. Trả về số URLs mới."""
        logger.info("Discovering promo URLs...")
        total_added = 0

        for page in self.url_repo.get_active_urls(url_type=UrlType.PROMO_LIST_PAGE):
            code       = page.airline.code
            discovered = URL_CRAWLERS.get(code, lambda u: [])(page.url)
            existing   = {u.url for u in self.url_repo.get_urls_by_airline(page.airline_id)}

            added = 0
            for link in discovered:
                if link not in existing:
                    self.session.add(CrawlerUrl(
                        airline_id=page.airline_id,
                        url_type=UrlType.PROMO_PAGE,
                        category="promotion",
                        url=link,
                        is_active=True,
                    ))
                    added += 1

            self.session.commit()
            total_added += added
            logger.info(f"  {code}: {len(discovered)} found, {added} new")

        return total_added

    def extract_all(self, run_id: str = None) -> int:
        """
        Crawl content từng promo page.
        Trả về số URLs crawl thành công.
        """
        self.discover_promo_urls()

        urls = self.url_repo.get_active_urls(url_type=UrlType.PROMO_PAGE)
        logger.info(f"Crawling {len(urls)} promo pages...")

        success = error = skipped = 0

        for i, url_obj in enumerate(urls, 1):
            existing     = self.staging_repo.get_by_url_id(url_obj.id)
            airline_code = url_obj.airline.code if url_obj.airline else "?"

            if existing and existing.status not in (StagingStatus.ERROR, StagingStatus.PENDING):
                skipped += 1
                continue

            logger.info(f"[{i}/{len(urls)}] [{airline_code}] {url_obj.url}")

            try:
                html = fetch_html(
                    url_obj.url,
                    force_playwright=(airline_code == "VJ"),
                )
                if not html:
                    logger.warning(f"  ⚠ Fetch failed")
                    if existing:
                        self.staging_repo.mark_as_error(existing.id, "Fetch failed")
                        self.session.commit()
                    error += 1
                    continue

                text = extract_content(html)
                if not text or not text.strip():
                    logger.warning(f"  ⚠ Empty content")
                    if existing:
                        self.staging_repo.mark_as_error(existing.id, "Empty content")
                        self.session.commit()
                    error += 1
                    continue

                self.staging_repo.save_raw_content(
                    url_obj.id,
                    url_obj.airline_id,
                    text,
                    pipeline_run_id=run_id,
                )
                url_obj.last_crawled_at = datetime.now()
                self.session.add(url_obj)
                self.session.commit()
                logger.info(f"  ✅ {len(text):,} chars")
                success += 1

            except Exception as e:
                self.session.rollback()
                logger.error(f"  ❌ {e}")
                if existing:
                    self.staging_repo.mark_as_error(existing.id, str(e))
                    self.session.commit()
                error += 1

            time.sleep(1)

        logger.info(f"Done: {success} ok / {skipped} skipped / {error} error")
        return success