import os, time, logging
from sqlmodel import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from repositories.crawler_staging_repo import CrawlerStagingRepository
from models.enums import UrlType

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Bạn là một chuyên gia Data Engineer. Nhiệm vụ: nhận văn bản thô cào từ website hàng không "
    "và định dạng lại thành Markdown sạch để nạp vào hệ thống RAG.\n\n"
    "QUY TẮC:\n"
    "1. KHÔNG thêm, bớt hay bịa đặt thông tin (đặc biệt là giá tiền, số kg, kích thước).\n"
    "2. Dùng Heading (##, ###) cho tiêu đề chính/phụ.\n"
    "3. TUYỆT ĐỐI KHÔNG dùng bảng (|...|). Chuyển bảng thành bullet points đầy đủ ngữ cảnh.\n"
    "4. In đậm (**) các từ khóa quan trọng, số tiền, trọng lượng.\n"
    "5. Xóa nội dung rác (bản quyền, menu, footer).\n"
    "Chỉ trả về Markdown, không giải thích."
)

class PolicyLLMFormatter:
    def __init__(self, session: Session):
        self.session      = session
        self.staging_repo = CrawlerStagingRepository(session)
        self.llm          = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        self.chain = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "VĂN BẢN THÔ CẦN ĐỊNH DẠNG:\n{raw_text}"),
        ]) | self.llm

    def _format_text_with_llm(self, raw_text: str, max_retries: int = 3) -> tuple[str | None, int]:
        """Trả về (markdown_content, tokens_used)."""
        for attempt in range(max_retries):
            try:
                resp   = self.chain.invoke({"raw_text": raw_text})
                tokens = 0
                if hasattr(resp, "response_metadata"):
                    usage  = resp.response_metadata.get("token_usage", {})
                    tokens = usage.get("total_tokens", 0)
                return resp.content, tokens
            except Exception as e:
                if "429" in str(e) or "RateLimitError" in str(e):
                    logger.warning(f"Rate limit. Waiting 20s (attempt {attempt+1})")
                    time.sleep(20)
                else:
                    logger.error(f"LLM error: {e}")
                    return None, 0
        return None, 0

    def process(self, run_id: str = None) -> tuple[bool, int]:
        """
        Format raw text → Markdown.
        Trả về (success, total_tokens_used).
        """
        logger.info("Starting Policy LLM formatting...")
        tasks = self.staging_repo.get_pending_llm_tasks(
            url_type=UrlType.POLICY_PAGE,
            pipeline_run_id=run_id,
        )
        if not tasks:
            logger.info("No pending policy tasks")
            return True, 0

        logger.info(f"{len(tasks)} tasks to format")
        total_tokens = 0

        for i, task in enumerate(tasks, 1):
            code = task.url_obj.airline.code if task.url_obj and task.url_obj.airline else "UNKNOWN"
            url  = task.url_obj.url          if task.url_obj else "UNKNOWN"
            cat  = task.url_obj.category     if task.url_obj else ""

            logger.info(f"[{i}/{len(tasks)}] [{code}] {url}")

            md, tokens = self._format_text_with_llm(task.raw_text)
            total_tokens += tokens

            if md:
                self.staging_repo.update_formatted_data(task.id, {
                    "markdown_content": md,
                    "metadata": {
                        "airline":    code,
                        "source_url": url,
                        "category":   cat,
                    },
                })
                self.session.commit()
                logger.info(f"  ✅ Done ({tokens} tokens)")
            else:
                self.staging_repo.mark_as_error(task.id, "LLM returned empty")
                self.session.commit()
                logger.error("  ❌ Failed")

            time.sleep(2)

        return True, total_tokens