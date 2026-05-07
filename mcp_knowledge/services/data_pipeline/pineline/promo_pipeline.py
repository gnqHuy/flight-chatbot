import uuid
import logging
from datetime import datetime
from sqlmodel import Session
from constants import COST_PER_TOKEN
from utils.database import engine
from models.pipeline_run import PipelineRun
from services.data_pipeline.extractors.promo_extractor import PromoExtractor
from services.data_pipeline.ingest.promo_ingester import PromoDBIngester
from services.data_pipeline.post_processing.post_processing_promo import PromoLLMExtractor

logger = logging.getLogger(__name__)

class PromotionETLPipeline:
    def run_pipeline(self):
        logger.info("🚀 BẮT ĐẦU PIPELINE KHUYẾN MÃI")

        run_id = str(uuid.uuid4())
        with Session(engine) as s:
            s.add(PipelineRun(id=run_id, pipeline_type="promo", status="running"))
            s.commit()
        logger.info(f"Pipeline run ID: {run_id}")

        try:
            # Bước 1: Discover + crawl
            urls_crawled = 0
            with Session(engine) as s:
                urls_crawled = PromoExtractor(s).extract_all(run_id=run_id)
            logger.info(f"  URLs crawled: {urls_crawled}")

            # Bước 2: LLM extract JSON
            tokens_used = 0
            with Session(engine) as s:
                _, tokens_used = PromoLLMExtractor(s).process(run_id=run_id)
            logger.info(f"  Tokens used: {tokens_used} | Cost: ${tokens_used * COST_PER_TOKEN:.4f}")

            # Bước 3: Ingest DB + embedding
            urls_ingested = 0
            with Session(engine) as s:
                urls_ingested = PromoDBIngester(s).ingest_to_db(run_id=run_id)
            logger.info(f"  URLs ingested: {urls_ingested}")

            # Cập nhật pipeline run → completed
            with Session(engine) as s:
                run = s.get(PipelineRun, run_id)
                run.status          = "completed"
                run.finished_at     = datetime.now()
                run.urls_crawled    = urls_crawled
                run.urls_ingested   = urls_ingested
                run.llm_tokens_used = tokens_used
                run.llm_cost_usd    = round(tokens_used * COST_PER_TOKEN, 6)
                duration = (datetime.now() - run.started_at).seconds

                s.add(run)
                s.commit()

            logger.info(
                f"🎉 HOÀN TẤT [{duration}s]: "
                f"crawled={urls_crawled}, ingested={urls_ingested}, "
                f"tokens={tokens_used}, cost=${tokens_used * COST_PER_TOKEN:.4f}"
            )
            return True

        except Exception as e:
            logger.exception(f"❌ PIPELINE THẤT BẠI: {e}")
            with Session(engine) as s:
                run               = s.get(PipelineRun, run_id)
                run.status        = "failed"
                run.finished_at   = datetime.now()
                run.error_message = str(e)
                s.add(run)
                s.commit()
            return False