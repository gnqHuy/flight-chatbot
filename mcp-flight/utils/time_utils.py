"""
time_utils.py
Dùng chung cho tất cả các server.
Đọc APP_DATE từ env để inject thời gian khi test.
Production: APP_DATE để trống → dùng datetime.now().
Test:       APP_DATE=2026-05-15 → dùng ngày đó.
"""
import os
from datetime import datetime


def get_current_time() -> datetime:
    """Trả về datetime hiện tại hoặc datetime inject từ APP_DATE."""
    raw = os.getenv("APP_DATE", "").strip()
    if raw:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
    return datetime.now()


def get_current_date_str() -> str:
    """Trả về ngày dạng YYYY-MM-DD."""
    return get_current_time().strftime("%Y-%m-%d")


def get_current_datetime_str() -> str:
    """Trả về datetime dạng YYYY-MM-DD HH:MM."""
    return get_current_time().strftime("%Y-%m-%d %H:%M")