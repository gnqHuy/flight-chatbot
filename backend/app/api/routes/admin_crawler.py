# app/api/routes/admin_crawler.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.database.database import get_session
from app.database.models.crawler_url import CrawlerUrl
from app.repositories.airline_repo import AirlineRepository
from app.repositories.crawler_url_repo import CrawlerUrlRepository
from app.schemas.crawler import BulkUrlCreateRequest

router = APIRouter(prefix="/admin/crawler", tags=["Admin Crawler"])

@router.post("/urls/bulk")
def add_crawler_urls_bulk(request: BulkUrlCreateRequest, session: Session = Depends(get_session)):
    airline_repo = AirlineRepository(session)
    url_repo = CrawlerUrlRepository(session)

    airline = airline_repo.get_by_code(request.airline_code.upper())
    if not airline:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy hãng bay mã '{request.airline_code}'."
        )

    existing_urls = {u.url for u in url_repo.get_urls_by_airline(airline.id)}

    added_count = 0
    skipped_count = 0

    for url_string in request.urls:
        url_string = url_string.strip()
        if not url_string:
            continue

        if url_string in existing_urls:
            skipped_count += 1
            continue

        new_url = CrawlerUrl(
            airline_id=airline.id,
            url_type=request.url_type,
            category=request.category,
            url=url_string,
            is_active=True
        )
        session.add(new_url)
        added_count += 1

    if added_count > 0:
        session.commit()

    return {
        "status": "success",
        "message": f"Đã thêm thành công {added_count} link. Bỏ qua {skipped_count} link trùng lặp.",
        "data": {"added": added_count, "skipped": skipped_count}
    }