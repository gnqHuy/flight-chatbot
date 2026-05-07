from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime
from models.enums import UrlType, StagingStatus
from models.crawler_staging import CrawlerStaging
from models.crawler_url import CrawlerUrl


class CrawlerStagingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_raw_content(
        self,
        url_id:          int,
        airline_id:      int,
        raw_text:        str,
        pipeline_run_id: str  = None,
        content_hash:    str  = None,
    ) -> CrawlerStaging:
        existing = self.session.exec(
            select(CrawlerStaging).where(CrawlerStaging.url_id == url_id)
        ).first()

        if existing:
            existing.raw_text        = raw_text
            existing.status          = StagingStatus.CRAWLED
            existing.error_message   = None
            existing.pipeline_run_id = pipeline_run_id
            existing.content_hash    = content_hash
            existing.updated_at      = datetime.now()
            obj = existing
        else:
            obj = CrawlerStaging(
                url_id=url_id,
                airline_id=airline_id,
                raw_text=raw_text,
                status=StagingStatus.CRAWLED,
                pipeline_run_id=pipeline_run_id,
                content_hash=content_hash,
            )
        self.session.add(obj)
        return obj

    def get_pending_llm_tasks(
        self,
        url_type:        UrlType,
        pipeline_run_id: str  = None,
        limit:           int  = 500,
    ) -> List[CrawlerStaging]:
        """
        Lấy các tasks CRAWLED chờ LLM format.
        Nếu có pipeline_run_id → chỉ lấy tasks của lần chạy đó.
        """
        stmt = (
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.CRAWLED)
            .where(CrawlerUrl.url_type == url_type)
            .options(joinedload(CrawlerStaging.url_obj))
        )
        if pipeline_run_id:
            stmt = stmt.where(CrawlerStaging.pipeline_run_id == pipeline_run_id)

        return list(self.session.exec(stmt.limit(limit)).all())

    def update_formatted_data(self, staging_id: int, json_data: dict):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.formatted_data = json_data
            obj.status         = StagingStatus.LLM_FORMATTED
            obj.updated_at     = datetime.now()
            self.session.add(obj)

    def mark_as_error(self, staging_id: int, error_msg: str):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.status        = StagingStatus.ERROR
            obj.error_message = error_msg
            obj.updated_at    = datetime.now()
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