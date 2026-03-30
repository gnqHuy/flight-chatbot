import time
import logging
from sqlmodel import Session
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm_setup import llm
from app.repositories.crawler_staging_repo import CrawlerStagingRepository
from app.database.models.crawler_url import UrlType

logger = logging.getLogger(__name__)

class PolicyLLMFormatter:
    def __init__(self, session: Session):
        self.session = session
        self.staging_repo = CrawlerStagingRepository(self.session)
        
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
            "5. Xóa bỏ hoàn toàn các thông tương rác (như bản quyền, menu footer, các câu 'click vào đây').\n"
            "Chỉ trả về nội dung Markdown, không giải thích gì thêm."
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_instruction),
            ("user", "VĂN BẢN THÔ CẦN ĐỊNH DẠNG:\n{raw_text}")
        ])
        
        self.chain = self.prompt_template | llm

    def _format_text_with_llm(self, raw_text: str, max_retries: int = 3) -> str | None:
        for attempt in range(max_retries):
            try:
                response = self.chain.invoke({"raw_text": raw_text})
                return response.content
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "RateLimitError" in error_msg:
                    logger.warning(f"⏳ OpenAI API quá tải (Rate limit). Chờ 20s (Lần {attempt + 1}/{max_retries})...")
                    time.sleep(20) 
                else:
                    logger.error(f"⚠️ Lỗi OpenAI: {e}")
                    return None
                    
        logger.error("❌ Đã thử lại nhiều lần nhưng vẫn thất bại do quá tải API.")
        return None

    def process(self):
        logger.info("🚀 BƯỚC 2: BẮT ĐẦU QUÁ TRÌNH LLM FORMATTING CHO POLICY...")
        
        pending_tasks = self.staging_repo.get_pending_llm_tasks(url_type=UrlType.POLICY_PAGE, limit=500)
        
        if not pending_tasks:
            logger.info("🎉 Không có dữ liệu Policy nào cần bóc tách lúc này.")
            return True

        total = len(pending_tasks)
        processed = 0

        for task in pending_tasks:
            processed += 1
            airline_code = task.url_obj.airline.code if task.url_obj and task.url_obj.airline else "UNKNOWN"
            source_url = task.url_obj.url if task.url_obj else "UNKNOWN"
            
            logger.info(f"[{processed}/{total}] ✨ Đang dùng LLM format [{airline_code}] ID {task.id}: {source_url}")
            
            clean_markdown = self._format_text_with_llm(task.raw_text)
            
            if clean_markdown:
                json_data = {
                    "markdown_content": clean_markdown,
                    "metadata": {
                        "airline": airline_code,
                        "source_url": source_url,
                        "category": task.url_obj.category if task.url_obj else ""
                    }
                }
                
                self.staging_repo.update_formatted_data(task.id, json_data)
                self.session.commit()
                logger.info(f"   ✅ Xong!")
            else:
                self.staging_repo.mark_as_error(task.id, "LLM trả về rỗng hoặc gọi API thất bại.")
                self.session.commit()
                logger.error(f"   ❌ Thất bại.")
                
            time.sleep(2)
            
        logger.info("\n🎉 HOÀN TẤT MẺ DỮ LIỆU! ĐÃ SẴN SÀNG CHO NHÚNG VECTOR RAG.")
        return True