import os, time, json, logging
from sqlmodel import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from repositories.crawler_staging_repo import CrawlerStagingRepository
from models.enums import UrlType

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Bạn là chuyên gia phân tích dữ liệu. Nhận văn bản thô của một trang khuyến mãi hàng không, "
    "trích xuất thông tin và trả về ĐÚNG định dạng JSON sau (không có backtick, không giải thích):\n"
    '{{"promo_code":"string hoặc null","promo_name":"string",'
    '"booking_start_date":"YYYY-MM-DD hoặc null","booking_end_date":"YYYY-MM-DD hoặc null",'
    '"travel_start_date":"YYYY-MM-DD hoặc null","travel_end_date":"YYYY-MM-DD hoặc null",'
    '"description":"string","conditions":"string"}}'
)

class PromoLLMExtractor:
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
            ("user", "VĂN BẢN THÔ:\n{raw_text}"),
        ]) | self.llm

    def _extract(self, raw_text: str, max_retries: int = 3) -> tuple[dict | None, int]:
        """Trả về (json_data, tokens_used)."""
        for attempt in range(max_retries):
            try:
                resp   = self.chain.invoke({"raw_text": raw_text})
                tokens = 0
                if hasattr(resp, "response_metadata"):
                    usage  = resp.response_metadata.get("token_usage", {})
                    tokens = usage.get("total_tokens", 0)
                data = json.loads(
                    resp.content.replace("```json", "").replace("```", "").strip()
                )
                return data, tokens
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed attempt {attempt+1}")
            except Exception as e:
                if "429" in str(e) or "RateLimitError" in str(e):
                    logger.warning("Rate limit, waiting 20s")
                    time.sleep(20)
                else:
                    logger.error(f"LLM error: {e}")
                    return None, 0
        return None, 0

    def process(self, run_id: str = None) -> tuple[bool, int]:
        """
        Extract JSON từ raw text.
        Trả về (success, total_tokens_used).
        """
        logger.info("Starting Promo LLM extraction...")
        tasks = self.staging_repo.get_pending_llm_tasks(
            url_type=UrlType.PROMO_PAGE,
            pipeline_run_id=run_id,
        )
        if not tasks:
            logger.info("No pending promo tasks")
            return True, 0

        logger.info(f"{len(tasks)} tasks to extract")
        total_tokens = 0

        for i, task in enumerate(tasks, 1):
            code = task.url_obj.airline.code if task.url_obj and task.url_obj.airline else "UNKNOWN"
            url  = task.url_obj.url          if task.url_obj else "UNKNOWN"

            logger.info(f"[{i}/{len(tasks)}] [{code}] ID {task.id}: {url}")

            data, tokens = self._extract(task.raw_text)
            total_tokens += tokens

            if data:
                data["metadata"] = {
                    "airline_id": task.airline_id,
                    "source_url": url,
                }
                self.staging_repo.update_formatted_data(task.id, data)
                self.session.commit()
                logger.info(f"  ✅ Done ({tokens} tokens)")
            else:
                self.staging_repo.mark_as_error(task.id, "LLM extraction failed")
                self.session.commit()
                logger.error("  ❌ Failed")

            time.sleep(2)

        return True, total_tokens