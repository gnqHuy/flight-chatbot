"""
services/data_pipeline/crawling/html_fetcher.py

Fetch HTML từ URL. Tự detect static vs JS-rendered.

Kết quả test thực tế:
- VN: requests OK (static)
- QH: requests OK (static)
- VJ: Playwright, KHÔNG block stylesheet (VJ dùng CSS để render #root)
"""
import time
import logging
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

MIN_TEXT_LENGTH = 300
MAX_RETRIES     = 3
RETRY_DELAY     = 3


def fetch_html(url: str, force_playwright: bool = False) -> str | None:
    """
    Fetch HTML. Tự chọn method:
    - requests trước (nhanh)
    - nếu text < MIN_TEXT_LENGTH → Playwright
    - force_playwright=True: dùng Playwright luôn
    """
    if not force_playwright:
        html = _fetch_static(url)
        
        if html == 404:
            return None
            
        if html and isinstance(html, str) and _has_enough_content(html):
            logger.debug(f"[fetcher] Static OK: {url}")
            return html
            
        logger.info(f"[fetcher] Static insufficient → Playwright: {url}")

    return _fetch_playwright(url)


def fetch_html_with_intercept(url: str, intercept_pattern: str) -> tuple[str, list[dict]]:
    """
    Fetch HTML + intercept network responses khớp pattern.
    Dùng cho VJ promo (intercept API nội bộ).
    Returns: (html, list of intercepted JSON responses)
    """
    intercepted = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page    = browser.new_page()

        def handle_response(response):
            if intercept_pattern in response.url and response.status == 200:
                try:
                    intercepted.append(response.json())
                except Exception:
                    pass

        page.on("response", handle_response)

        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
            html = page.content()
        except Exception as e:
            logger.error(f"[fetcher] Intercept error {url}: {e}")
            html = ""
        finally:
            browser.close()

    return html, intercepted


# ── Private ───────────────────────────────────────────────────────────────────

def _fetch_static(url: str) -> str | int | None:
    """
    Trả về HTML (str) nếu thành công.
    Trả về số 404 nếu dính lỗi Not Found (để chặn Playwright).
    Trả về None nếu lỗi mạng hoặc cần thử bằng Playwright.
    """
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                return resp.text
                
            if resp.status_code == 404:
                logger.warning(f"[fetcher] HTTP 404 - Bỏ qua URL này: {url}")
                return 404
                
            logger.warning(f"[fetcher] HTTP {resp.status_code}: {url}")
        except requests.RequestException as e:
            logger.warning(f"[fetcher] Static attempt {attempt+1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    return None


def _fetch_playwright(url: str) -> str | None:
    """
    Playwright fetch.
    VJ dùng CSS để hiển thị #root — block stylesheet làm #root bị hidden mãi.
    """
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page    = browser.new_page()

                page.route("**/*", lambda route: (
                    route.abort()
                    if route.request.resource_type in ["image", "media", "font"]
                    else route.continue_()
                ))

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                try:
                    page.wait_for_selector("#root", timeout=10000)
                except Exception:
                    logger.debug(f"[fetcher] Không tìm thấy #root trên {url}, vẫn tiếp tục lấy HTML.")
                
                page.wait_for_timeout(3000)
                html = page.content()
                browser.close()
                return html

        except Exception as e:
            logger.warning(f"[fetcher] Playwright attempt {attempt+1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return None


def _has_enough_content(html: str) -> bool:
    text = BeautifulSoup(html, "html.parser").get_text(strip=True)
    return len(text) >= MIN_TEXT_LENGTH