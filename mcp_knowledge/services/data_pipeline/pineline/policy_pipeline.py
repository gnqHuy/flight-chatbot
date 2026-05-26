import uuid
import logging
from datetime import datetime
from sqlmodel import Session, select
from constants import COST_PER_TOKEN
from utils.database import engine
from models.airline import Airline
from models.pipeline_run import PipelineRun
from services.data_pipeline.extractors.policy_extractor import PolicyExtractor
from services.data_pipeline.ingest.policy_ingester import PolicyDBIngester
from services.data_pipeline.post_processing.post_processing_policies import PolicyLLMFormatter

logger = logging.getLogger(__name__)

class PolicyETLPipeline:
    def run_pipeline(self):
        logger.info("🚀 BẮT ĐẦU PIPELINE CHÍNH SÁCH")

        run_id = str(uuid.uuid4())
        with Session(engine) as s:
            s.add(PipelineRun(id=run_id, pipeline_type="policy", status="running"))
            s.commit()
        logger.info(f"Pipeline run ID: {run_id}")

        try:
            # Bước 0: Sync URLs mới
            urls_discovered = 0
            with Session(engine) as s:
                airlines  = s.exec(select(Airline)).all()
                extractor = PolicyExtractor(s)
                for airline in airlines:
                    added = extractor.sync_urls(airline.code, airline.id)
                    urls_discovered += added
            logger.info(f"  URLs discovered: {urls_discovered}")

            # Bước 1: Crawl + extract
            urls_crawled = 0
            with Session(engine) as s:
                urls_crawled = PolicyExtractor(s).extract_all(run_id=run_id)
            logger.info(f"  URLs crawled: {urls_crawled}")

            # Bước 2: LLM format
            tokens_used = 0
            with Session(engine) as s:
                _, tokens_used = PolicyLLMFormatter(s).process(run_id=run_id)
            logger.info(f"  Tokens used: {tokens_used} | Cost: ${tokens_used * COST_PER_TOKEN:.4f}")

            # Bước 3: Ingest vector DB
            urls_ingested = 0
            with Session(engine) as s:
                urls_ingested = PolicyDBIngester(s).ingest_to_db(run_id=run_id)
            logger.info(f"  URLs ingested: {urls_ingested}")

            # Cập nhật pipeline run → completed
            with Session(engine) as s:
                run = s.get(PipelineRun, run_id)
                run.status          = "completed"
                run.finished_at     = datetime.now()
                run.urls_discovered = urls_discovered
                run.urls_crawled    = urls_crawled
                run.urls_ingested   = urls_ingested
                run.llm_tokens_used = tokens_used
                run.llm_cost_usd    = round(tokens_used * COST_PER_TOKEN, 6)
                duration = (datetime.now() - run.started_at).seconds

                s.add(run)
                s.commit()

            logger.info(
                f"🎉 HOÀN TẤT [{duration}s]: "
                f"discovered={urls_discovered}, crawled={urls_crawled}, "
                f"ingested={urls_ingested}, tokens={tokens_used}, "
                f"cost=${tokens_used * COST_PER_TOKEN:.4f}"
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