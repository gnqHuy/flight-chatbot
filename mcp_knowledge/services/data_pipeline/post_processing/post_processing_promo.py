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
    '{"promo_code":"string hoặc null","promo_name":"string",'
    '"booking_start_date":"YYYY-MM-DD hoặc null","booking_end_date":"YYYY-MM-DD hoặc null",'
    '"travel_start_date":"YYYY-MM-DD hoặc null","travel_end_date":"YYYY-MM-DD hoặc null",'
    '"description":"string","conditions":"string"}'
)

class PromoLLMExtractor:
    def __init__(self, session: Session):
        self.session      = session
        self.staging_repo = CrawlerStagingRepository(session)
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0,
            api_key=os.getenv("OPENAI_API_KEY", ""),
        )
        self.chain = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", "VĂN BẢN THÔ:\n{raw_text}"),
        ]) | self.llm

    def _extract(self, raw_text: str, max_retries: int = 3) -> dict | None:
        for attempt in range(max_retries):
            try:
                content = self.chain.invoke({"raw_text": raw_text}).content
                return json.loads(content.replace("```json","").replace("```","").strip())
            except json.JSONDecodeError:
                logger.warning(f"JSON parse failed attempt {attempt+1}")
            except Exception as e:
                if "429" in str(e) or "RateLimitError" in str(e):
                    logger.warning("Rate limit, waiting 20s")
                    time.sleep(20)
                else:
                    logger.error(f"LLM error: {e}")
                    return None
        return None

    def process(self):
        logger.info("Starting Promo LLM extraction...")
        tasks = self.staging_repo.get_pending_llm_tasks(url_type=UrlType.PROMO_PAGE)
        if not tasks:
            logger.info("No pending promo tasks")
            return True
        for i, task in enumerate(tasks, 1):
            code = task.url_obj.airline.code if task.url_obj and task.url_obj.airline else "UNKNOWN"
            url  = task.url_obj.url if task.url_obj else "UNKNOWN"
            logger.info(f"[{i}/{len(tasks)}] [{code}] ID {task.id}: {url}")
            data = self._extract(task.raw_text)
            if data:
                data["metadata"] = {"airline_id": task.airline_id, "source_url": url}
                self.staging_repo.update_formatted_data(task.id, data)
                self.session.commit()
                logger.info("  ✅ Done")
            else:
                self.staging_repo.mark_as_error(task.id, "LLM extraction failed")
                self.session.commit()
                logger.error("  ❌ Failed")
            time.sleep(2)
        return True