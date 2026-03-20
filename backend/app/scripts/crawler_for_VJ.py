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
                
                # BẮT BUỘC ĐỢI: Chờ thẻ root xuất hiện và chờ ReactJS render thêm 3s
                page.wait_for_selector('#root', timeout=15000)
                page.wait_for_timeout(3000) 
                
                html_content = page.content()
                browser.close()

            # ==========================================
            # XỬ LÝ HTML RÚT TRÍCH TEXT (GIỚI HẠN & KHOAN SÂU)
            # ==========================================
            soup = BeautifulSoup(html_content, 'html.parser')
            target_div = None
            jss_container = None
            
            # Khởi điểm: Tìm thẻ id="root"
            root_div = soup.find(id='root')
            
            if root_div:
                # TẦNG 1 & 2: Tìm jss149 là con của con root
                for child_level_1 in root_div.find_all(recursive=False):
                    child_level_2 = child_level_1.find(class_=re.compile(r'jss149'), recursive=False)
                    if child_level_2:
                        jss_container = child_level_2
                        break
            
            # Nếu tìm thấy jss149, bắt đầu khoan sâu (Tầng 3+)
            if jss_container:
                # Tìm MuiGrid-grid-xs-12 (ưu tiên cao nhất)
                xs_12 = jss_container.find(class_=re.compile(r'MuiGrid-grid-xs-12'))
                if xs_12:
                    target_div = xs_12
                else:
                    # Nếu không có xs-12, tìm MuiGrid-item đầu tiên
                    mui_item = jss_container.find(class_=re.compile(r'MuiGrid-item'))
                    if mui_item:
                        target_div = mui_item
                    else:
                        # Fallback về chính jss149
                        target_div = jss_container

            # Fallback cuối cùng nếu toàn bộ quy trình trên thất bại
            if not target_div:
                target_div = soup.find(id='root') or soup.find('body')
                
            if not target_div or not target_div.get_text(strip=True):
                print(f"      ⚠️ VJ: DOM trống rỗng tại {url}. Đang thử lại...")
                continue

            # ==========================================
            # DỌN RÁC & FORMAT DỮ LIỆU BÊN TRONG TARGET_DIV
            # ==========================================
            for tag in target_div(['script', 'style', 'nav', 'footer', 'noscript', 'header']):
                tag.decompose()

            # Chuyển đổi ảnh thành Text (Giữ lại tick xanh, X đỏ, tên hạng vé)
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

            # Xử lý Bảng biểu
            for tr in target_div.find_all('tr'):
                for cell in tr.find_all(['td', 'th']):
                    cell.append(" | ")
                tr.append("\n")

            # Xử lý Danh sách
            for li in target_div.find_all('li'):
                li.insert(0, "- ")

            # Ép ra text thuần túy
            raw_text = target_div.get_text(separator='\n', strip=True)
            
            # Dọn dẹp khoảng trắng
            clean_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
            clean_text = re.sub(r'\|\s+\|\s+\|', '|', clean_text)
            
            if clean_text:
                return clean_text

        except Exception as e:
            print(f"      ⚠️ Lỗi Playwright VJ: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None