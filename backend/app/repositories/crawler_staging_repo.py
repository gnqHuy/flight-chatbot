from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from typing import List, Optional
from app.core.enums import UrlType
from app.database.models.crawler_staging import CrawlerStaging, StagingStatus
from app.database.models.crawler_url import CrawlerUrl

class CrawlerStagingRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_raw_content(self, url_id: int, airline_id: int, raw_text: str) -> CrawlerStaging:
        statement = select(CrawlerStaging).where(CrawlerStaging.url_id == url_id)
        existing = self.session.exec(statement).first()

        if existing:
            existing.raw_text = raw_text
            existing.status = StagingStatus.CRAWLED
            existing.error_message = None
            obj = existing
        else:
            obj = CrawlerStaging(
                url_id=url_id,
                airline_id=airline_id,
                raw_text=raw_text,
                status=StagingStatus.CRAWLED
            )
        
        self.session.add(obj)
        return obj

    def get_pending_llm_tasks(self, url_type: UrlType, limit: int = 10) -> List[CrawlerStaging]:
        """
        Lấy danh sách chờ bóc tách THEO LOẠI (Policy hoặc Promo).
        Dùng joinedload để lấy luôn thông tin URL trong 1 câu query (tối ưu hiệu năng).
        """
        statement = (
            select(CrawlerStaging)
            .join(CrawlerUrl)
            .where(CrawlerStaging.status == StagingStatus.CRAWLED)
            .where(CrawlerUrl.url_type == url_type)
            .options(joinedload(CrawlerStaging.url)) 
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def update_formatted_data(self, staging_id: int, json_data: dict):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.formatted_data = json_data
            obj.status = StagingStatus.LLM_FORMATTED
            self.session.add(obj)

    def mark_as_error(self, staging_id: int, error_msg: str):
        obj = self.session.get(CrawlerStaging, staging_id)
        if obj:
            obj.status = StagingStatus.ERROR
            obj.error_message = error_msg
            self.session.add(obj)

    def get_by_url_id(self, url_id: int) -> Optional[CrawlerStaging]:
        return self.session.exec(select(CrawlerStaging).where(CrawlerStaging.url_id == url_id)).first()