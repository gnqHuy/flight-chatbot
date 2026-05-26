import re, time, logging
import requests
from bs4 import BeautifulSoup
from requests.compat import urljoin
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

AIRLINE_BASE_URLS = {"QH": "https://www.bambooairways.com"}
MAX_RETRIES = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def crawl_qh_policy(url: str) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            main = soup.find(id="main-content")
            if not main:
                logger.warning(f"QH: no #main-content at {url}")
                return None
            portlets = main.find_all(class_=re.compile(r"portlet-content"))
            if not portlets:
                return None
            blocks = []
            for portlet in portlets:
                for tag in portlet(["script","style","nav","footer","noscript","header","button"]):
                    tag.decompose()
                for hidden in portlet.find_all(style=re.compile(r"display:\s*none", re.I)):
                    hidden.decompose()
                for tr in portlet.find_all("tr"):
                    for cell in tr.find_all(["td","th"]):
                        cell.append(" | ")
                    tr.append("\n")
                for li in portlet.find_all("li"):
                    li.insert(0, "- ")
                t = portlet.get_text(separator="\n", strip=True)
                if t:
                    blocks.append(t)
            raw = "\n\n".join(blocks)
            clean = re.sub(r"\n{3,}", "\n\n", raw).strip()
            return re.sub(r"\|\s+\|\s+\|", "|", clean)
        except requests.exceptions.RequestException as e:
            logger.warning(f"QH network error: {e}. Retry {attempt+1}/{MAX_RETRIES}")
            time.sleep(3)
    return None


def get_qh_promo_urls(url: str) -> list[str]:
    base_url = AIRLINE_BASE_URLS["QH"]
    promotions = set()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for block in soup.find_all(attrs={"data-analytics-asset-title": "Ưu đãi"}):
            for a in block.find_all("a", class_=re.compile(r"txtp11_link"), href=True):
                href = a.get("href")
                if href:
                    promotions.add(urljoin(base_url, href))
    except Exception as e:
        logger.error(f"get_qh_promo_urls error: {e}")
    return list(promotions)


def extract_qh_promo_text(url: str) -> str:
    logger.info(f"[QH] Crawling: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", lambda route: route.abort()
                   if route.request.resource_type in ["image","media","font"]
                   else route.continue_())
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#content", timeout=20000)
            time.sleep(2)
            soup = BeautifulSoup(page.content(), "html.parser")
            for tag in soup(["script","style"]):
                tag.decompose()
            section = soup.find(id="content")
            if section:
                articles = section.find_all(class_=re.compile(r"journal-content-article"))
                if articles:
                    text_content = "\n\n".join(
                        a.get_text(separator="\n", strip=True)
                        for a in articles if a.get_text(strip=True)
                    )
        except Exception as e:
            logger.error(f"QH promo crawl error: {e}")
        finally:
            browser.close()
    return text_content