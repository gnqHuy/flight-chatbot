import os
import time
import logging
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_setup import llm

logger = logging.getLogger(__name__)

class PolicyLLMFormatter:
    def __init__(self):
        self.input_dir = os.path.join("data", "policies")
        self.output_dir = os.path.join("data", "cleaned_policies")
        
        self.system_instruction = (
            "Bạn là một chuyên gia Data Engineer. Nhiệm vụ của bạn là nhận văn bản thô cào từ website "
            "hàng không và định dạng lại thành Markdown (.md) siêu sạch để nạp vào hệ thống RAG.\n\n"
            "QUY TẮC TỐI THƯỢNG:\n"
            "1. KHÔNG thêm, bớt hay bịa đặt bất kỳ thông tin nào (đặc biệt là giá tiền, con số, số kg, kích thước).\n"
            "2. Dùng Heading (##, ###) cho các tiêu đề chính/phụ để phân tách rõ ràng các hạng mục.\n"
            "3. XỬ LÝ BẢNG BIỂU (QUAN TRỌNG): TUYỆT ĐỐI KHÔNG dùng định dạng bảng (Table |...|...|). "
            "Hãy chuyển đổi mọi bảng biểu thành các gạch đầu dòng (Bullet points) mang đầy đủ ngữ cảnh.\n"
            "   - Ví dụ SAI (Bảng): | Chặng bay | 20kg | 30kg |\n"
            "   - Ví dụ ĐÚNG (Danh sách):\n"
            "     - Chặng bay nội địa: Hành lý 20kg giá 150.000 VNĐ, Hành lý 30kg giá 250.000 VNĐ.\n"
            "4. In đậm (**) các từ khóa quan trọng, số tiền, và trọng lượng.\n"
            "5. Xóa bỏ hoàn toàn các thông tin rác (như bản quyền, menu footer, các câu 'click vào đây').\n"
            "Chỉ trả về nội dung Markdown, không giải thích gì thêm."
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_instruction),
            ("user", "VĂN BẢN THÔ CẦN ĐỊNH DẠNG:\n{raw_text}")
        ])
        
        self.chain = self.prompt_template | llm

    def _format_text_with_llm(self, raw_text, max_retries=3):
        for attempt in range(max_retries):
            try:
                response = self.chain.invoke({"raw_text": raw_text})
                return response.content
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RateLimitError" in error_msg:
                    print(f"      ⏳ OpenAI API đang quá tải (Rate limit). Tạm nghỉ 20 giây trước khi thử lại (Lần {attempt + 1}/{max_retries})...")
                    time.sleep(20) 
                else:
                    print(f"      ⚠️ Lỗi OpenAI: {e}")
                    return None
                    
        print("      ❌ Đã thử lại nhiều lần nhưng vẫn thất bại do quá tải API.")
        return None

    def process(self):
        print("🚀 BƯỚC 2: BẮT ĐẦU QUÁ TRÌNH LLM FORMATTING VỚI OPENAI...")
        
        for airline in os.listdir(self.input_dir):
            airline_in_path = os.path.join(self.input_dir, airline)
            if not os.path.isdir(airline_in_path):
                continue
                
            airline_out_path = os.path.join(self.output_dir, airline)
            os.makedirs(airline_out_path, exist_ok=True)
            
            for filename in os.listdir(airline_in_path):
                if not filename.endswith(".txt"):
                    continue
                    
                input_file = os.path.join(airline_in_path, filename)
                output_file = os.path.join(airline_out_path, filename.replace(".txt", ".md"))
                
                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    print(f"⏭️ Bỏ qua (Đã xử lý): {airline}/{filename}")
                    continue
                    
                print(f"✨ Đang dùng LLM format: {airline}/{filename} ...")
                
                with open(input_file, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                    
                lines = raw_text.split('\n')
                metadata = "\n".join(lines[:4])
                actual_content = "\n".join(lines[4:])
                
                clean_markdown = self._format_text_with_llm(actual_content)
                
                if clean_markdown:
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write(metadata + "\n\n")
                        f.write(clean_markdown)
                    print(f"   ✅ Xong!")
                else:
                    print(f"   ❌ Thất bại.")
                    
                time.sleep(2) 
                
        print("\n🎉 HOÀN TẤT! DỮ LIỆU ĐÃ SẴN SÀNG CHO RAG.")
        return True