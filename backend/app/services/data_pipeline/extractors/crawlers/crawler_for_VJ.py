import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

MAX_RETRIES = 3

def crawl_vj_policy(url):
    """
    Crawler Vietjet Air dùng Playwright.
    Thuật toán khoan sâu: root (Tầng 0) -> jss149 (Tầng 2) -> xs-12 -> MuiGrid-item.
    """
    for attempt in range(MAX_RETRIES):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                page.wait_for_selector('#root', timeout=15000)
                page.wait_for_timeout(3000) 
                
                html_content = page.content()
                browser.close()

            soup = BeautifulSoup(html_content, 'html.parser')
            target_div = None
            jss_container = None
            
            root_div = soup.find(id='root')
            
            if root_div:
                for child_level_1 in root_div.find_all(recursive=False):
                    child_level_2 = child_level_1.find(class_=re.compile(r'jss149'), recursive=False)
                    if child_level_2:
                        jss_container = child_level_2
                        break
            
            if jss_container:
                xs_12 = jss_container.find(class_=re.compile(r'MuiGrid-grid-xs-12'))
                if xs_12:
                    target_div = xs_12
                else:
                    mui_item = jss_container.find(class_=re.compile(r'MuiGrid-item'))
                    if mui_item:
                        target_div = mui_item
                    else:
                        target_div = jss_container

            if not target_div:
                target_div = soup.find(id='root') or soup.find('body')
                
            if not target_div or not target_div.get_text(strip=True):
                print(f"      ⚠️ VJ: DOM trống rỗng tại {url}. Đang thử lại...")
                continue

            for tag in target_div(['script', 'style', 'nav', 'footer', 'noscript', 'header']):
                tag.decompose()

            for img in target_div.find_all('img'):
                src = img.get('src', '').lower()
                alt_text = img.get('alt', '').strip()
                
                if 'greensuccess' in src:
                    img.replace_with(" [Bao gồm / Có] ")
                elif 'redclose' in src:
                    img.replace_with(" [Không bao gồm] ")
                elif alt_text:
                    img.replace_with(f" [{alt_text}] ")
                else:
                    img.decompose()

            for tr in target_div.find_all('tr'):
                for cell in tr.find_all(['td', 'th']):
                    cell.append(" | ")
                tr.append("\n")

            for li in target_div.find_all('li'):
                li.insert(0, "- ")

            raw_text = target_div.get_text(separator='\n', strip=True)
            
            clean_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
            clean_text = re.sub(r'\|\s+\|\s+\|', '|', clean_text)
            
            if clean_text:
                return clean_text

        except Exception as e:
            print(f"      ⚠️ Lỗi Playwright VJ: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None

def get_vj_promo_urls():
    url = "https://www.vietjetair.com/vi/news/khuyen-mai-1697696806643/"
    
    unique_urls = set()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def handle_response(response):
            if "/api/v1/post?slug=khuyen-mai-1697696806643" in response.url and response.status == 200:
                try:
                    data = response.json()
                    for post in data.get("list", []):
                        slug = post.get("slug")
                        if slug:
                            full_url = f"https://www.vietjetair.com/vi/news/{slug}"
                            unique_urls.add(full_url)
                except Exception:
                    pass

        page.on("response", handle_response)
        
        page.goto(url, wait_until="networkidle", timeout=60000)
        time.sleep(3)
        
        browser.close()
        
    promotions = [{"airline": "VJ", "url": u} for u in unique_urls]
    
    return promotions

import re
import time
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

def extract_vj_promo_text(url):
    print(f"   ⏳ [VJ] Đang cào: {url}")
    text_content = ""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_())
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            page.wait_for_selector("#root", timeout=20000)
            
            time.sleep(3) 
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            root_div = soup.find(id='root')
            if root_div:
                target_div = root_div.select_one('.MuiGrid-root.MuiGrid-grid-xs-12')
                
                if target_div:
                    text_content = target_div.get_text(separator='\n', strip=True)
                else:
                    print("   ⚠️ [VJ] Cào được HTML nhưng không tìm thấy thẻ nội dung.")
                    
        except Exception as e:
            print(f"   ❌ [VJ] Lỗi: {e}")
        finally:
            browser.close()
            
    return text_content