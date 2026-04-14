from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from models.enums import UrlType, StagingStatus          # FIX
from models.crawler_staging import CrawlerStaging
from models.crawler_url import CrawlerUrl


class CrawlerStagingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_raw_content(self, url_id: int, airline_id: int, raw_text: str) -> CrawlerStaging:
        existing = self.session.exec(
            select(CrawlerStaging).where(CrawlerStaging.url_id == url_id)
        ).first()
        if existing:
            existing.raw_text      = raw_text
            existing.status        = StagingStatus.CRAWLED
            existing.error_message = None
            obj = existing
        else:
            obj = CrawlerStaging(
                url_id=url_id, airline_id=airline_id,
                raw_text=raw_text, status=StagingStatus.CRAWLED,
            )
        self.session.add(obj)
        return obj

    def get_pending_llm_tasks(self, url_type: UrlType, limit: int = 500) -> List[CrawlerStaging]:
        return list(self.session.exec(
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.CRAWLED)
            .where(CrawlerUrl.url_type == url_type)
            .options(joinedload(CrawlerStaging.url_obj))
            .limit(limit)
        ).all())

    def update_formatted_data(self, staging_id: int, json_data: dict):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.formatted_data = json_data
            obj.status         = StagingStatus.LLM_FORMATTED
            self.session.add(obj)

    def mark_as_error(self, staging_id: int, error_msg: str):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.status        = StagingStatus.ERROR
            obj.error_message = error_msg
            self.session.add(obj)

    def get_by_url_id(self, url_id: int) -> Optional[CrawlerStaging]:
        return self.session.exec(
            select(CrawlerStaging).where(CrawlerStaging.url_id == url_id)
        ).first()

    def count_by_status(self) -> dict:
        from sqlmodel import func
        return {
            s.value: self.session.exec(
                select(func.count(CrawlerStaging.id))
                .where(CrawlerStaging.status == s)
            ).one()
            for s in StagingStatus
        }