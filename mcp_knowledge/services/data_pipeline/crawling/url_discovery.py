"""
services/data_pipeline/crawling/url_discovery.py
"""
import time
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from services.data_pipeline.crawling.url_classifier import classify_urls

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

ENTRY_POINTS = {
    "VN": "https://www.vietnamairlines.com/vn/vi/sitemap",
    "QH": "https://www.bambooairways.com/vn/vi/sitemap",
    "VJ": "https://www.vietjetair.com/vi",
}

BASE_DOMAINS = {
    "VN": "www.vietnamairlines.com",
    "QH": "www.bambooairways.com",
    "VJ": "www.vietjetair.com",
}

BASE_PATHS = {
    "www.vietnamairlines.com": "/vn/vi/",
    "www.bambooairways.com":   "/vn/vi/",
    "www.vietjetair.com":      "/vi/",
}

EXCLUDE_PATTERNS = [
    "javascript", "mailto:", "tel:",
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".zip",
    "?", "#", "utm_",
    "/login", "/logout", "/register", "/payment", "/checkout", "/cart",
    "facebook.com", "twitter.com", "instagram.com",
    "youtube.com", "linkedin.com", "tiktok.com",
]


def discover_urls(airline_code: str) -> list[dict]:
    """
    Trả về list[{"url": str, "category": str}]
    Chỉ trả về URL có category != general
    """
    entry  = ENTRY_POINTS.get(airline_code)
    domain = BASE_DOMAINS.get(airline_code)
    if not entry or not domain:
        return []

    if airline_code == "VJ":
        raw_urls = list(_discover_vj(entry, domain))
    else:
        raw_urls = list(_discover_multilevel(entry, domain))

    logger.info(f"[discovery] {airline_code}: {len(raw_urls)} raw URLs, classifying...")

    classified = classify_urls(raw_urls)

    results = [
        {"url": url, "category": cat}
        for url, cat in classified.items()
        if cat != "general"
    ]

    logger.info(f"[discovery] {airline_code}: {len(results)} relevant URLs after classify")
    return results


def _depth(url: str) -> int:
    """
    Đếm số path segment sau base prefix.
    """
    parsed    = urlparse(url)
    path      = parsed.path
    base_path = BASE_PATHS.get(parsed.netloc, "/")

    if base_path not in path:
        return -1

    rest = path.split(base_path, 1)[1]
    if not rest:
        return 0

    return rest.rstrip("/").count("/") + 1


def _discover_multilevel(entry: str, domain: str) -> set[str]:
    all_urls    = set()
    visited     = set()
    invalid_urls = set()

    # ── Tầng 1 ───────────────────────────────────────────────────────────────
    logger.info(f"[discovery] Tầng 1: {entry}")
    sitemap_html = _fetch_html(entry)
    if not sitemap_html:
        return all_urls

    tier1 = _extract_all_links(sitemap_html, entry, domain)
    tier1 = {u for u in tier1 if _depth(u) > 0}
    all_urls.update(tier1)
    visited.add(entry)
    logger.info(f"  → {len(tier1)} URLs")

    # ── Tầng 2 ───────────────────────────────────────────────────────────────
    h4_links = _extract_h4_links(sitemap_html, entry, domain)
    h4_links = {u for u in h4_links if _depth(u) > 0 and u not in visited}
    logger.info(f"[discovery] Tầng 2: {len(h4_links)} h4 pages to crawl")

    tier2_new = set()
    for url in h4_links:
        visited.add(url)
        html = _fetch_html(url)
        if not html:
            invalid_urls.add(url)
            all_urls.discard(url)
            continue
        new = _extract_all_links(html, url, domain) - all_urls
        new = {u for u in new if _depth(u) > 0}
        tier2_new.update(new)
        all_urls.update(new)
        time.sleep(0.3)

    all_urls -= invalid_urls
    logger.info(f"  → {len(tier2_new)} new URLs")

    # ── Tầng 3 ───────────────────────────────────────────────────────────────
    to_crawl_t3 = [u for u in all_urls if u not in visited]
    logger.info(f"[discovery] Tầng 3: {len(to_crawl_t3)} pages to crawl")

    tier3_new = set()
    for url in to_crawl_t3:
        visited.add(url)
        html = _fetch_html(url)
        if not html:
            invalid_urls.add(url)
            all_urls.discard(url) 
            continue
        new = _extract_content_links(html, url, domain) - all_urls
        new = {u for u in new if _depth(u) > 0}
        tier3_new.update(new)
        all_urls.update(new)
        time.sleep(0.3)

    all_urls -= invalid_urls
    logger.info(f"  → {len(all_urls)} total URLs, {len(invalid_urls)} invalid URLs")
    logger.info(f"  → {len(tier3_new)} new URLs")

    return all_urls


def _discover_vj(entry: str, domain: str) -> set[str]:
    """VJ: Playwright + scroll để load footer. 1 tầng là đủ."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page    = browser.new_page()
            page.route("**/*", lambda route: (
                route.abort()
                if route.request.resource_type in ["image", "media", "font"]
                else route.continue_()
            ))
            page.goto(entry, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#root", timeout=15000)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)
            html = page.content()
            browser.close()

        return {u for u in _extract_all_links(html, entry, domain) if _depth(u) > 0}
    except Exception as e:
        logger.error(f"[discovery] VJ error: {e}")
        return set()


# ── Fetch helpers ─────────────────────────────────────────────────────────────

def _fetch_html(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"[discovery] HTTP {resp.status_code}: {url}")
        return None
    except Exception as e:
        logger.warning(f"[discovery] fetch error {url}: {e}")
        return None


# ── Link extractors ───────────────────────────────────────────────────────────

def _extract_all_links(html: str, base_url: str, domain: str) -> set[str]:
    """Lấy tất cả links cùng domain từ toàn bộ trang."""
    soup = BeautifulSoup(html, "html.parser")
    return _links_from_tags(soup.find_all("a", href=True), base_url, domain)


def _extract_h4_links(html: str, base_url: str, domain: str) -> set[str]:
    """Chỉ lấy links nằm trong thẻ <h4> — tiêu đề cha trong sitemap."""
    soup = BeautifulSoup(html, "html.parser")
    tags = []
    for h4 in soup.find_all("h4"):
        tags.extend(h4.find_all("a", href=True))
    return _links_from_tags(tags, base_url, domain)


def _extract_content_links(html: str, base_url: str, domain: str) -> set[str]:
    """
    Chỉ lấy links nằm trong content tags: <p>, <li>, <td>.
    Bỏ qua nav/header/footer/menu.
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(["nav", "header", "footer"]):
        tag.decompose()

    tags = []
    for content_tag in soup.find_all(["p", "li", "td"]):
        tags.extend(content_tag.find_all("a", href=True))
    return _links_from_tags(tags, base_url, domain)


def _links_from_tags(a_tags, base_url: str, domain: str) -> set[str]:
    """Convert list of <a> tags thành set URLs đã filter."""
    found = set()
    for a in a_tags:
        href     = a["href"].strip()
        full_url = urljoin(base_url, href)
        if urlparse(full_url).netloc != domain:
            continue
        if any(p in full_url for p in EXCLUDE_PATTERNS):
            continue
        found.add(full_url.rstrip("/"))
    return found