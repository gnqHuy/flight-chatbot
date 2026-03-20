import re
import time
import requests
from bs4 import BeautifulSoup

MAX_RETRIES = 3

def crawl_vn_policy(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. DIỆT GỌN CÁC KHỐI EXPERIENCEFRAGMENT (Rác)
            for tag in soup.find_all(class_=re.compile(r'experiencefragment', re.I)):
                tag.decompose()
                
            content_divs = soup.find_all(class_='cmp-vna-rte')
            
            if content_divs:
                all_text_blocks = []
                for div in content_divs:
                    # --- BƯỚC XỬ LÝ MỚI: DỌN DẸP THẺ HTML TRƯỚC KHI ÉP TEXT ---
                    
                    # A. Lột vỏ các thẻ nội tuyến (inline) để không bị ngắt câu
                    for inline_tag in div.find_all(['a', 'span', 'strong', 'b', 'em', 'i']):
                        inline_tag.unwrap()
                        
                    # B. Giữ lại cấu trúc danh sách (List) bằng cách thêm dấu gạch ngang
                    for li_tag in div.find_all('li'):
                        # Chèn dấu "- " vào đầu mỗi thẻ <li>
                        li_tag.insert(0, "- ")
                        
                    # C. Đảm bảo các thẻ tiêu đề (H1, H2, H3) có khoảng cách rõ ràng
                    for heading in div.find_all(['h1', 'h2', 'h3', 'h4']):
                        heading.insert(0, "\n[TIÊU ĐỀ] ")
                        heading.append("\n")

                    # -----------------------------------------------------------
                    
                    # Lúc này gọi get_text sẽ mượt mà hơn rất nhiều
                    block_text = div.get_text(separator='\n', strip=True)
                    if block_text:
                        all_text_blocks.append(block_text)
                
                raw_text = "\n\n".join(all_text_blocks)
                
                # Dọn dẹp khoảng trắng: gom nhiều dòng trống thành 1 dòng trống duy nhất
                clean_text = re.sub(r'\n{2,}', '\n\n', raw_text).strip()
                
                # Xử lý tàn dư: Xóa các khoảng trắng thừa ở đầu dòng do unwrap để lại
                clean_text = re.sub(r'^\s+', '', clean_text, flags=re.MULTILINE)
                
                return clean_text
            else:
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"      ⚠️ Lỗi mạng VNA: {e}. Thử lại ({attempt + 1}/{MAX_RETRIES})...")
            time.sleep(3)
            
    return None