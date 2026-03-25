from sqlmodel import Session, select
from typing import List, Optional
from app.database.models.crawler_url import CrawlerUrl, UrlType

class CrawlerUrlRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, url_obj: CrawlerUrl) -> CrawlerUrl:
        self.session.add(url_obj)
        self.session.commit()
        self.session.refresh(url_obj)
        return url_obj

    def get_by_id(self, url_id: int) -> Optional[CrawlerUrl]:
        return self.session.get(CrawlerUrl, url_id)

    def get_active_urls(self, url_type: Optional[UrlType] = None) -> List[CrawlerUrl]:
        query = select(CrawlerUrl).where(CrawlerUrl.is_active == True)
        if url_type:
            query = query.where(CrawlerUrl.url_type == url_type)
        return list(self.session.exec(query).all())

    def get_urls_by_airline(self, airline_id: int) -> List[CrawlerUrl]:
        statement = select(CrawlerUrl).where(CrawlerUrl.airline_id == airline_id)
        return list(self.session.exec(statement).all())