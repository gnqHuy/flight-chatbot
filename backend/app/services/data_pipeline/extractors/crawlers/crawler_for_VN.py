import re
import time
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

MAX_RETRIES = 3

def crawl_vn_policy(url: str) -> str | None:
    """
    Crawler policy cho Vietnam Airlines. Nhận vào url, trả về raw text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for tag in soup.find_all(class_=re.compile(r'experiencefragment', re.I)):
                tag.decompose()
                
            content_divs = soup.find_all(class_='cmp-vna-rte')
            
            if content_divs:
                all_text_blocks = []
                for div in content_divs:
                    for inline_tag in div.find_all(['a', 'span', 'strong', 'b', 'em', 'i']):
                        inline_tag.unwrap()
                        
                    for li_tag in div.find_all('li'):
                        li_tag.insert(0, "- ")
                        
                    for heading in div.find_all(['h1', 'h2', 'h3', 'h4']):
                        heading.insert(0, "\n[TIÊU ĐỀ] ")
                        heading.append("\n")

                    block_text = div.get_text(separator='\n', strip=True)
                    if block_text:
                        all_text_blocks.append(block_text)
                
                raw_text = "\n\n".join(all_text_blocks)
                
                clean_text = re.sub(r'\n{2,}', '\n\n', raw_text).strip()
                clean_text = re.sub(r'^\s+', '', clean_text, flags=re.MULTILINE)
                
                return clean_text
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"      ⚠️ Lỗi mạng VNA: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None


def get_vn_promo_urls(url: str) -> list[str]:
    """
    Nhận vào trang khuyến mãi tháng của VN, dùng Playwright bắt cả DOM và Data attribute, 
    trả về danh sách các link (chuỗi).
    """
    base_url = "https://www.vietnamairlines.com"
    unique_urls = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            print("   ⏳ Đang chờ VNA render lịch khuyến mãi...")
            
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_selector(".cmp-promotion-list", timeout=15000)
            time.sleep(2) 
            
            cta_links = page.locator("a.promotion-calendar-card__cta").all()
            for link in cta_links:
                href = link.get_attribute("href")
                if href and not href.startswith(('javascript', '#')):
                    full_url = urljoin(base_url, href)
                    unique_urls.add(full_url)
                    
            promo_lists = page.locator(".cmp-promotion-list").all()
            for p_list in promo_lists:
                data_promo = p_list.get_attribute("data-promotion")
                if data_promo:
                    try:
                        promo_json = json.loads(data_promo)
                        for item in promo_json.get("promotionList", []):
                            cta_direct = item.get("ctaDirect")
                            if cta_direct:
                                full_url = urljoin(base_url, cta_direct)
                                unique_urls.add(full_url)
                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"   ❌ Lỗi cào URL VN: {e}")
        finally:
            browser.close()

    return list(unique_urls)


def extract_vn_promo_text(url: str) -> str:
    """
    Nhận vào 1 url khuyến mãi cụ thể, dùng Playwright để cào và trả về raw text.
    """
    print(f"   ⏳ [VN] Đang cào: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            time.sleep(2)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            asset_div = soup.find(class_=re.compile(r'Asset|Campaign'))
            if asset_div:
                text_content = asset_div.get_text(separator='\n', strip=True)
            else:
                print(f"   ⚠️ [VN] Không tìm thấy nội dung khuyến mãi tại {url}")
                
        except Exception as e:
            print(f"   ❌ [VN] Lỗi: {e}")
        finally:
            browser.close()
            
    return text_content