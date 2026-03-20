import os
import time
from openai import OpenAI
from dotenv import load_dotenv

# 1. Tải API Key từ file .env
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# 2. Khởi tạo Client OpenAI
client = OpenAI(api_key=API_KEY)

# Cấu hình thư mục
INPUT_DIR = "data/policies"
OUTPUT_DIR = "data/cleaned_policies"

# Sử dụng model gpt-4o-mini (Nhanh, rẻ, thông minh)
MODEL_ID = 'gpt-4o-mini'

SYSTEM_INSTRUCTION = """
Bạn là một chuyên gia Data Engineer. Nhiệm vụ của bạn là nhận văn bản thô cào từ website hàng không và định dạng lại thành Markdown (.md) chuẩn xác để nạp vào hệ thống RAG.
QUY TẮC TỐI THƯỢNG:
1. KHÔNG thêm, bớt, tóm tắt hay bịa đặt bất kỳ thông tin nào (đặc biệt là giá tiền, con số, số kg, kích thước).
2. Dùng Heading (##, ###) cho các tiêu đề chính/phụ.
3. Dùng Bullet points (- ) cho các danh sách, các mức giá, hoặc các khu vực (A, B, C...).
4. In đậm (**) các từ khóa quan trọng, số tiền, và trọng lượng.
5. Xóa bỏ hoàn toàn các thông tin rác lọt lưới ở cuối trang (như bản quyền, địa chỉ công ty, menu footer) nếu có.
Chỉ trả về nội dung Markdown, không giải thích gì thêm.
"""

def format_text_with_llm(raw_text, max_retries=3):
    """Gửi text thô cho OpenAI để lấy về bản Markdown siêu sạch"""
    
    for attempt in range(max_retries):
        try:
            # 3. Cú pháp gọi API của OpenAI
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": f"VĂN BẢN THÔ CẦN ĐỊNH DẠNG:\n{raw_text}"}
                ],
                temperature=0.1, # Khóa tính sáng tạo để giữ nguyên số liệu
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_msg = str(e)
            # Bắt lỗi Rate Limit 429 của OpenAI
            if "429" in error_msg or "RateLimitError" in error_msg:
                print(f"      ⏳ OpenAI API đang quá tải (Rate limit). Tạm nghỉ 20 giây trước khi thử lại (Lần {attempt + 1}/{max_retries})...")
                time.sleep(20) # Giới hạn của OpenAI thường phục hồi nhanh hơn
            else:
                print(f"      ⚠️ Lỗi OpenAI: {e}")
                return None
                
    print("      ❌ Đã thử lại nhiều lần nhưng vẫn thất bại do quá tải API.")
    return None

def process_all_policies():
    print("🚀 BẮT ĐẦU QUÁ TRÌNH LLM FORMATTING VỚI OPENAI (GPT-4o-mini)...")
    
    for airline in os.listdir(INPUT_DIR):
        airline_in_path = os.path.join(INPUT_DIR, airline)
        if not os.path.isdir(airline_in_path):
            continue
            
        airline_out_path = os.path.join(OUTPUT_DIR, airline)
        os.makedirs(airline_out_path, exist_ok=True)
        
        for filename in os.listdir(airline_in_path):
            if not filename.endswith(".txt"):
                continue
                
            input_file = os.path.join(airline_in_path, filename)
            output_file = os.path.join(airline_out_path, filename.replace(".txt", ".md"))
            
            # Tính năng bỏ qua file đã làm xong (giúp bạn chạy lại thoải mái không tốn tiền)
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                print(f"⏭️ Bỏ qua (Đã xử lý): {airline}/{filename}")
                continue
                
            print(f"✨ Đang dùng LLM format: {airline}/{filename} ...")
            
            with open(input_file, "r", encoding="utf-8") as f:
                raw_text = f.read()
                
            lines = raw_text.split('\n')
            metadata = "\n".join(lines[:4])
            actual_content = "\n".join(lines[4:])
            
            clean_markdown = format_text_with_llm(actual_content)
            
            if clean_markdown:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(metadata + "\n\n")
                    f.write(clean_markdown)
                print(f"   ✅ Xong!")
            else:
                print(f"   ❌ Thất bại.")
                
            # Nghỉ 2 giây giữa các request để mượt mà luồng chạy
            time.sleep(2) 
            
    print("\n🎉 HOÀN TẤT! DỮ LIỆU ĐÃ SẴN SÀNG CHO RAG.")

if __name__ == "__main__":
    process_all_policies()