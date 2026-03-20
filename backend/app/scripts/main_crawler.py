import os
import time
from crawler_for_VJ import crawl_vj_policy
from crawler_for_VN import crawl_vn_policy
from crawler_for_QH import crawl_qh_policy

from link_web import POLICY_URLS

DATA_DIR = "data/policies"

def run_crawler():
    print("🚀 BẮT ĐẦU HỆ THỐNG CRAWLER ĐA MÔ-ĐUN...")
    total_links = sum(len(links) for links in POLICY_URLS.values())
    processed = 0
    
    for airline, categories in POLICY_URLS.items():
        airline_dir = os.path.join(DATA_DIR, airline)
        os.makedirs(airline_dir, exist_ok=True)
        
        for category, url in categories.items():
            processed += 1
            file_path = os.path.join(airline_dir, f"{category}.txt")
            
            if os.path.exists(file_path):
                print(f"[{processed}/{total_links}] ⏭️ Bỏ qua: [{airline}] {category}.txt")
                continue
                
            print(f"[{processed}/{total_links}] 🕸️ Đang cào: [{airline}] {category}...")
            
            # --- ĐỊNH TUYẾN (ROUTING) THEO HÃNG ---
            clean_text = None
            if airline == "VN":
                clean_text = crawl_vn_policy(url)
            elif airline == "VJ":
                clean_text = crawl_vj_policy(url)
            elif airline == "QH":
                clean_text = crawl_qh_policy(url)
            
            if clean_text:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"HÃNG: {airline.upper()}\n")
                    f.write(f"CHỦ ĐỀ: {category}\n")
                    f.write(f"NGUỒN: {url}\n")
                    f.write("-" * 40 + "\n\n")
                    f.write(clean_text)
                print(f"   ✅ Thành công!")
            else:
                print(f"   ❌ THẤT BẠI: {url}")
            
            time.sleep(2)
            
    print("\n🎉 HOÀN TẤT QUÁ TRÌNH CÀO DỮ LIỆU!")

if __name__ == "__main__":
    run_crawler()