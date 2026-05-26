"""
services/data_pipeline/extractors/policy_extractor.py

Orchestrate toàn bộ luồng crawl policy:
  1. sync_urls(): discover URL mới → insert DB
  2. extract_all(): crawl + scrape từng URL → lưu crawler_staging
"""
import logging
from datetime import datetime
from sqlmodel import Session

from repositories.crawler_url_repo import CrawlerUrlRepository
from repositories.crawler_staging_repo import CrawlerStagingRepository
from models.crawler_url import CrawlerUrl
from models.enums import UrlType, StagingStatus

from services.data_pipeline.crawling.html_fetcher import fetch_html
from services.data_pipeline.crawling.url_discovery import discover_urls
from services.data_pipeline.scraping.content_extractor import extract_content, compute_hash

logger = logging.getLogger(__name__)


class PolicyExtractor:
    def __init__(self, session: Session):
        self.session      = session
        self.url_repo     = CrawlerUrlRepository(session)
        self.staging_repo = CrawlerStagingRepository(session)

    def sync_urls(self, airline_code: str, airline_id: int) -> int:
        """
        Discover URL policy mới → insert DB nếu chưa có.
        Trả về số URL mới được thêm.
        """
        logger.info(f"[policy] Syncing URLs for {airline_code}...")

        discovered = discover_urls(airline_code)
        if not discovered:
            logger.warning(f"[policy] {airline_code}: No URLs discovered")
            return 0

        existing_urls = {
            u.url for u in self.url_repo.get_urls_by_airline(airline_id)
        }

        added = 0
        for item in discovered:
            if item["url"] not in existing_urls:
                url_type = (
                    UrlType.PROMO_PAGE
                    if item["category"] == "promotion"
                    else UrlType.POLICY_PAGE
                )
                self.session.add(CrawlerUrl(
                    airline_id=airline_id,
                    url_type=url_type,
                    category=item["category"],
                    url=item["url"],
                    is_active=True,
                ))
                added += 1

        if added:
            self.session.commit()

        logger.info(f"[policy] {airline_code}: {len(discovered)} discovered, {added} new")
        return added

    def extract_all(self, run_id: str = None) -> int:
        """
        Crawl tất cả policy URLs đang active.
        Trả về số URLs crawl thành công.
        """
        urls = self.url_repo.get_active_urls(url_type=UrlType.POLICY_PAGE)
        logger.info(f"[policy] Crawling {len(urls)} policy pages...")

        success = error = skipped = 0

        for i, url_obj in enumerate(urls, 1):
            existing     = self.staging_repo.get_by_url_id(url_obj.id)
            airline_code = url_obj.airline.code if url_obj.airline else "?"
            logger.info(f"[{i}/{len(urls)}] [{airline_code}] {url_obj.url}")

            try:
                html = fetch_html(url_obj.url, force_playwright=(airline_code == "VJ"))
                if not html:
                    logger.warning(f"  ⚠ Fetch failed")
                    if existing:
                        self.staging_repo.mark_as_error(existing.id, "Fetch failed")
                        self.session.commit()
                    error += 1
                    continue

                text = extract_content(html)
                if not text:
                    logger.warning(f"  ⚠ Empty content")
                    if existing:
                        self.staging_repo.mark_as_error(existing.id, "Empty content")
                        self.session.commit()
                    error += 1
                    continue

                # Content hash check — skip nếu không thay đổi
                new_hash = compute_hash(text)
                if (existing
                        and existing.status == StagingStatus.COMPLETED
                        and existing.content_hash == new_hash):
                    logger.info(f"  ✓ No change, skip")
                    skipped += 1
                    continue

                # Lưu vào staging kèm run_id và content_hash
                self.staging_repo.save_raw_content(
                    url_obj.id,
                    url_obj.airline_id,
                    text,
                    pipeline_run_id=run_id,
                    content_hash=new_hash,
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

        logger.info(f"[policy] Done: {success} ok, {skipped} skipped, {error} errors")
        return success