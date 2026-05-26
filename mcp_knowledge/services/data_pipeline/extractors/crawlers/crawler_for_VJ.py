import re, time, logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def crawl_vj_policy(url: str) -> str | None:
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_selector("#root", timeout=15000)
                page.wait_for_timeout(3000)
                html = page.content()
                browser.close()
            soup = BeautifulSoup(html, "html.parser")
            root = soup.find(id="root")
            target = None
            if root:
                for c1 in root.find_all(recursive=False):
                    c2 = c1.find(class_=re.compile(r"jss149"), recursive=False)
                    if c2:
                        xs12 = c2.find(class_=re.compile(r"MuiGrid-grid-xs-12"))
                        target = xs12 or c2.find(class_=re.compile(r"MuiGrid-item")) or c2
                        break
            target = target or root or soup.find("body")
            if not target or not target.get_text(strip=True):
                continue
            for tag in target(["script","style","nav","footer","noscript","header"]):
                tag.decompose()
            for img in target.find_all("img"):
                src = img.get("src","").lower()
                alt = img.get("alt","").strip()
                if "greensuccess" in src:   img.replace_with(" [Bao gồm] ")
                elif "redclose" in src:     img.replace_with(" [Không bao gồm] ")
                elif alt:                   img.replace_with(f" [{alt}] ")
                else:                       img.decompose()
            for tr in target.find_all("tr"):
                for cell in tr.find_all(["td","th"]): cell.append(" | ")
                tr.append("\n")
            for li in target.find_all("li"): li.insert(0, "- ")
            raw = target.get_text(separator="\n", strip=True)
            clean = re.sub(r"\n{3,}", "\n\n", raw).strip()
            clean = re.sub(r"\|\s+\|\s+\|", "|", clean)
            if clean: return clean
        except Exception as e:
            logger.warning(f"VJ error: {e}. Retry {attempt+1}/{MAX_RETRIES}")
            time.sleep(3)
    return None


def get_vj_promo_urls(url: str) -> list[str]:
    unique_urls = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        def handle_response(response):
            if "/api/v1/post?slug=khuyen-mai-1697696806643" in response.url and response.status == 200:
                try:
                    for post in response.json().get("list", []):
                        slug = post.get("slug")
                        if slug: unique_urls.add(f"https://www.vietjetair.com/vi/news/{slug}")
                except Exception: pass
        page.on("response", handle_response)
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(3)
        except Exception as e:
            logger.error(f"get_vj_promo_urls error: {e}")
        finally:
            browser.close()
    return list(unique_urls)


def extract_vj_promo_text(url: str) -> str:
    logger.info(f"[VJ] Crawling: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/*", lambda route: route.abort()
                   if route.request.resource_type in ["image","media","font"]
                   else route.continue_())
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector("#root", timeout=20000)
            time.sleep(3)
            soup = BeautifulSoup(page.content(), "html.parser")
            root = soup.find(id="root")
            if root:
                target = root.select_one(".MuiGrid-root.MuiGrid-grid-xs-12")
                if target: text_content = target.get_text(separator="\n", strip=True)
        except Exception as e:
            logger.error(f"VJ promo crawl error: {e}")
        finally:
            browser.close()
    return text_content