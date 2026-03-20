import re
import time
import requests
from bs4 import BeautifulSoup

MAX_RETRIES = 3

def crawl_qh_policy(url):
    """
    Crawler chuyên biệt cho Bamboo Airways (Liferay CMS).
    Thuật toán: Quét id="main-content" -> gom toàn bộ class="portlet-content".
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
            
            # ==========================================
            # 1. TÌM KHỐI NỘI DUNG CHÍNH (MAIN-CONTENT)
            # ==========================================
            main_content = soup.find(id='main-content')
            
            if not main_content:
                print(f"      ⚠️ QH: Không tìm thấy id='main-content' tại {url}")
                return None
                
            # ==========================================
            # 2. GOM TẤT CẢ CÁC PORTLET-CONTENT
            # ==========================================
            # Trên Liferay, một bài viết có thể bị chia thành nhiều portlet liền kề nhau
            portlets = main_content.find_all(class_=re.compile(r'portlet-content'))
            
            if not portlets:
                print(f"      ⚠️ QH: Không tìm thấy class 'portlet-content' nào tại {url}")
                return None

            all_clean_text = []
            
            # Xử lý từng khối portlet tìm được
            for portlet in portlets:
                # Dọn rác
                for tag in portlet(['script', 'style', 'nav', 'footer', 'noscript', 'header', 'button']):
                    tag.decompose()
                    
                # Xóa các thẻ div ẩn (thường là popup hoặc form tìm kiếm rác)
                for hidden_tag in portlet.find_all(style=re.compile(r'display:\s*none', re.I)):
                    hidden_tag.decompose()

                # Xử lý Bảng biểu (Chèn dấu | vào giữa các cột để LLM đọc được)
                for tr in portlet.find_all('tr'):
                    for cell in tr.find_all(['td', 'th']):
                        cell.append(" | ")
                    tr.append("\n")

                # Xử lý Danh sách
                for li in portlet.find_all('li'):
                    li.insert(0, "- ")
                    
                # Ép text khối hiện tại
                block_text = portlet.get_text(separator='\n', strip=True)
                if block_text:
                    all_clean_text.append(block_text)

            # ==========================================
            # 3. GỘP NỘI DUNG VÀ DỌN DẸP
            # ==========================================
            raw_text = "\n\n".join(all_clean_text)
            
            # Dọn dẹp khoảng trắng dư thừa
            clean_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
            # Dọn các dòng bảng rỗng
            clean_text = re.sub(r'\|\s+\|\s+\|', '|', clean_text)
            
            return clean_text

        except requests.exceptions.RequestException as e:
            print(f"      ⚠️ Lỗi mạng QH: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None