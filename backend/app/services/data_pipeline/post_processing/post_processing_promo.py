import os
import json
import glob
import logging
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_setup import llm
from app.schemas.promotion import Promotion

logger = logging.getLogger(__name__)

class PromoLLMExtractor:
    def __init__(self):
        self.raw_dir = os.path.join("data", "promotions", "raw")
        self.output_dir = os.path.join("data", "promotions", "cleaned_promotions")
        
        self.structured_llm = llm.with_structured_output(Promotion)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Bạn là một chuyên gia phân tích dữ liệu hàng không.\nNhiệm vụ của bạn là đọc nội dung bài viết khuyến mãi và trích xuất thông tin theo đúng định dạng được yêu cầu.\nLưu ý quan trọng:\n- Hiện tại đang là năm 2026. Hãy dùng năm 2026 làm hệ quy chiếu nếu trong bài viết chỉ nhắc đến ngày/tháng mà không nhắc đến năm.\n- Tuyệt đối không tự bịa ra thông tin. Nếu trong bài không có thông tin cho một trường nào đó, hãy để giá trị null.\n- Định dạng ngày tháng phải chuẩn ISO (YYYY-MM-DD) cho booking_start_date và booking_end_date."),
            ("human", "Nội dung bài viết:\n{raw_text}")
        ])
        self.extractor_chain = self.prompt | self.structured_llm

    def process(self):
        print("🚀 BƯỚC 2: BẮT ĐẦU DÙNG LLM BÓC TÁCH DỮ LIỆU KHUYẾN MÃI...\n")
        
        os.makedirs(self.output_dir, exist_ok=True)
        output_file = os.path.join(self.output_dir, "processed_promotions.json")
        
        file_paths = glob.glob(os.path.join(self.raw_dir, "*", "*.txt"))
        total_files = len(file_paths)
        
        if total_files == 0:
            print("⚠️ Không tìm thấy file txt nào trong thư mục raw.")
            return False
            
        processed_data = []
        
        for idx, file_path in enumerate(file_paths, 1):
            print(f"[{idx}/{total_files}] 🧠 Đang phân tích: {file_path}")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                if len(lines) < 5:
                    continue
                    
                airline = lines[0].replace("HÃNG: ", "").strip()
                source_url = lines[2].replace("NGUỒN: ", "").strip()
                raw_text = "".join(lines[4:]).strip()
                
                if not raw_text:
                    continue
                
                ai_extracted_data = self.extractor_chain.invoke({"raw_text": raw_text})
                promo_dict = ai_extracted_data.model_dump()
                
                promo_dict["airline"] = airline
                promo_dict["url"] = source_url
                
                processed_data.append(promo_dict)
                print(f"   ✅ Bóc tách xong: {promo_dict.get('promo_name', 'Không có tên')}")
                
            except Exception as e:
                print(f"   ❌ Lỗi xử lý file {file_path}: {e}")
                
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=4)
            
        print(f"\n🎉 HOÀN TẤT TRÍCH XUẤT! Đã lưu {len(processed_data)} khuyến mãi vào {output_file}")
        return output_file