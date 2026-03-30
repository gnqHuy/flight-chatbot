import re
import time
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
from requests.compat import urljoin

from app.core.constants import AIRLINE_BASE_URLS

MAX_RETRIES = 3

def crawl_qh_policy(url: str) -> str | None:
    """
    Nhận vào 1 url policy, trả về raw text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            main_content = soup.find(id='main-content')
            
            if not main_content:
                print(f"      ⚠️ QH: Không tìm thấy id='main-content' tại {url}")
                return None

            portlets = main_content.find_all(class_=re.compile(r'portlet-content'))
            
            if not portlets:
                print(f"      ⚠️ QH: Không tìm thấy class 'portlet-content' nào tại {url}")
                return None

            all_clean_text = []
            
            for portlet in portlets:
                for tag in portlet(['script', 'style', 'nav', 'footer', 'noscript', 'header', 'button']):
                    tag.decompose()
                    
                for hidden_tag in portlet.find_all(style=re.compile(r'display:\s*none', re.I)):
                    hidden_tag.decompose()

                for tr in portlet.find_all('tr'):
                    for cell in tr.find_all(['td', 'th']):
                        cell.append(" | ")
                    tr.append("\n")

                for li in portlet.find_all('li'):
                    li.insert(0, "- ")
                    
                block_text = portlet.get_text(separator='\n', strip=True)
                if block_text:
                    all_clean_text.append(block_text)

            raw_text = "\n\n".join(all_clean_text)
            
            clean_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
            clean_text = re.sub(r'\|\s+\|\s+\|', '|', clean_text)
            
            return clean_text

        except requests.exceptions.RequestException as e:
            print(f"      ⚠️ Lỗi mạng QH: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None


def get_qh_promo_urls(url: str) -> list[str]:
    """
    Nhận vào 1 url (trang danh sách khuyến mãi), trả về danh sách các link (chuỗi).
    """
    base_url = AIRLINE_BASE_URLS["QH"]
    promotions = set()
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        offer_blocks = soup.find_all(attrs={"data-analytics-asset-title": "Ưu đãi"})
        
        for block in offer_blocks:
            a_tags = block.find_all('a', class_=re.compile(r'txtp11_link'), href=True)
            
            for a in a_tags:
                href = a.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    promotions.add(full_url)
                        
        return list(promotions)

    except Exception as e:
        print(f"Lỗi cào URL QH: {e}")
        return []
    

def extract_qh_promo_text(url: str) -> str:
    """
    Nhận vào 1 url khuyến mãi cụ thể, dùng Playwright để cào và trả về raw text.
    """
    print(f"   ⏳ [QH] Đang cào: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            page.wait_for_selector("#content", timeout=20000)
            time.sleep(2)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            for script_or_style in soup(["script", "style"]):
                script_or_style.decompose()
            
            content_section = soup.find(id='content')
            
            if content_section:
                articles = content_section.find_all(class_=re.compile(r'journal-content-article'))
                
                if articles:
                    extracted_texts = []
                    for article in articles:
                        text = article.get_text(separator='\n', strip=True)
                        if text:
                            extracted_texts.append(text)
                            
                    text_content = "\n\n".join(extracted_texts)
                else:
                    print("   ⚠️ [QH] Không tìm thấy class 'journal-content-article'.")
            else:
                print("   ⚠️ [QH] Không tìm thấy thẻ id='content'.")
                
        except Exception as e:
            print(f"   ❌ [QH] Lỗi: {e}")
        finally:
            browser.close()
            
    return text_content