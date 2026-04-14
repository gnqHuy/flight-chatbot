import re, time, json, logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

# FIX: định nghĩa inline
AIRLINE_BASE_URLS = {"VN": "https://www.vietnamairlines.com"}
MAX_RETRIES = 3
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}


def crawl_vn_policy(url: str) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup.find_all(class_=re.compile(r"experiencefragment", re.I)):
                tag.decompose()
            content_divs = soup.find_all(class_="cmp-vna-rte")
            if not content_divs: return None
            blocks = []
            for div in content_divs:
                for inline in div.find_all(["a","span","strong","b","em","i"]): inline.unwrap()
                for li in div.find_all("li"): li.insert(0, "- ")
                for h in div.find_all(["h1","h2","h3","h4"]):
                    h.insert(0, "\n[TIÊU ĐỀ] "); h.append("\n")
                t = div.get_text(separator="\n", strip=True)
                if t: blocks.append(t)
            raw = "\n\n".join(blocks)
            clean = re.sub(r"\n{2,}", "\n\n", raw).strip()
            return re.sub(r"^\s+", "", clean, flags=re.MULTILINE)
        except requests.exceptions.RequestException as e:
            logger.warning(f"VN network error: {e}. Retry {attempt+1}/{MAX_RETRIES}")
            time.sleep(3)
    return None


def get_vn_promo_urls(url: str) -> list[str]:
    base_url = AIRLINE_BASE_URLS["VN"]
    unique_urls = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".cmp-promotion-list", timeout=15000)
            time.sleep(2)
            for link in page.locator("a.promotion-calendar-card__cta").all():
                href = link.get_attribute("href")
                if href and not href.startswith(("javascript","#")):
                    unique_urls.add(urljoin(base_url, href))
            for p_list in page.locator(".cmp-promotion-list").all():
                data_promo = p_list.get_attribute("data-promotion")
                if data_promo:
                    try:
                        for item in json.loads(data_promo).get("promotionList", []):
                            cta = item.get("ctaDirect")
                            if cta: unique_urls.add(urljoin(base_url, cta))
                    except json.JSONDecodeError: continue
        except Exception as e:
            logger.error(f"get_vn_promo_urls error: {e}")
        finally:
            browser.close()
    return list(unique_urls)


def extract_vn_promo_text(url: str) -> str:
    logger.info(f"[VN] Crawling: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(2)
            soup = BeautifulSoup(page.content(), "html.parser")
            asset = soup.find(class_=re.compile(r"Asset|Campaign"))
            if asset: text_content = asset.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.error(f"VN promo crawl error: {e}")
        finally:
            browser.close()
    return text_content