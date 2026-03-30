import time
import logging
from sqlmodel import Session
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_setup import llm
from app.schemas.promotion import Promotion
from app.repositories.crawler_staging_repo import CrawlerStagingRepository
from app.database.models.crawler_url import UrlType

logger = logging.getLogger(__name__)

class PromoLLMExtractor:
    def __init__(self, session: Session):
        self.session = session
        self.staging_repo = CrawlerStagingRepository(self.session)
        
        self.structured_llm = llm.with_structured_output(Promotion)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Bạn là một chuyên gia phân tích dữ liệu hàng không.\n"
             "Nhiệm vụ của bạn là đọc nội dung bài viết khuyến mãi và trích xuất thông tin theo đúng định dạng JSON được yêu cầu.\n"
             "LƯU Ý QUAN TRỌNG:\n"
             "- Hiện tại đang là năm 2026. Hãy dùng năm 2026 làm hệ quy chiếu nếu trong bài viết chỉ nhắc đến ngày/tháng mà không nhắc đến năm.\n"
             "- Tuyệt đối không tự bịa ra thông tin. Nếu trong bài không có thông tin cho một trường nào đó, hãy để giá trị null.\n"
             "- Định dạng ngày tháng phải chuẩn ISO (YYYY-MM-DD) cho booking_start_date và booking_end_date."),
            ("human", "NỘI DUNG BÀI VIẾT:\n{raw_text}")
        ])
        
        self.extractor_chain = self.prompt | self.structured_llm

    def _extract_with_llm(self, raw_text: str, max_retries: int = 3):
        for attempt in range(max_retries):
            try:
                response = self.extractor_chain.invoke({"raw_text": raw_text})
                return response
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RateLimitError" in error_msg:
                    logger.warning(f"⏳ OpenAI API quá tải. Chờ 20s (Lần {attempt + 1}/{max_retries})...")
                    time.sleep(20) 
                else:
                    logger.error(f"⚠️ Lỗi OpenAI: {e}")
                    return None
                    
        logger.error("❌ Đã thử lại nhiều lần nhưng API vẫn thất bại.")
        return None

    def process(self):
        logger.info("🚀 BƯỚC 2: BẮT ĐẦU DÙNG LLM BÓC TÁCH DỮ LIỆU KHUYẾN MÃI (PROMO)...")
        
        pending_tasks = self.staging_repo.get_pending_llm_tasks(url_type=UrlType.PROMO_PAGE, limit=50)
        
        if not pending_tasks:
            logger.info("🎉 Không có dữ liệu Khuyến mãi nào cần bóc tách lúc này.")
            return True
            
        total_tasks = len(pending_tasks)
        processed = 0
        
        for task in pending_tasks:
            processed += 1
            
            airline_id = task.url_obj.airline_id if task.url_obj else None
            airline_code = task.url_obj.airline.code if task.url_obj and task.url_obj.airline else "UNKNOWN"
            source_url = task.url_obj.url if task.url_obj else "UNKNOWN"
            
            logger.info(f"[{processed}/{total_tasks}] 🧠 Đang phân tích [{airline_code}] ID {task.id}...")
            
            if not task.raw_text or not task.raw_text.strip():
                self.staging_repo.mark_as_error(task.id, "Nội dung raw_text bị trống.")
                self.session.commit()
                continue
            
            ai_extracted_data = self._extract_with_llm(task.raw_text)
            
            if ai_extracted_data:
                promo_dict = ai_extracted_data.model_dump()
                
                promo_dict["metadata"] = {
                    "airline_id": airline_id,
                    "source_url": source_url
                }
                
                self.staging_repo.update_formatted_data(task.id, promo_dict)
                self.session.commit()
                
                promo_name = promo_dict.get('promo_name') or "Không xác định được tên"
                logger.info(f"   ✅ Bóc tách xong: {promo_name}")
            else:
                self.staging_repo.mark_as_error(task.id, "LLM không thể trích xuất dữ liệu.")
                self.session.commit()
                logger.error(f"   ❌ Thất bại ID {task.id}.")
                
            time.sleep(2)
            
        logger.info("\n🎉 HOÀN TẤT TRÍCH XUẤT! CÁC KHUYẾN MÃI ĐÃ ĐƯỢC LƯU JSON VÀO DATABASE STAGING.")
        return True