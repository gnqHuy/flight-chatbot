import re
import logging
from sqlmodel import Session, select
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from constants import OPENAI_API_KEY, DATABASE_URL
from models.crawler_staging import CrawlerStaging
from models.crawler_url import CrawlerUrl, UrlType
from models.enums import StagingStatus

logger = logging.getLogger(__name__)


class PolicyDBIngester:
    def __init__(self, session: Session):
        self.session         = session
        self.collection_name = "flight_policies"
        self.embeddings      = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY,
        )
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#",   "Header 1"),
                ("##",  "Header 2"),
                ("###", "Header 3"),
            ]
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=150
        )

    def ingest_to_db(self, run_id: str = None) -> int:
        logger.info("🗄️ BƯỚC 3: NẠP DỮ LIỆU CHÍNH SÁCH VÀO VECTOR DB...")

        if not DATABASE_URL:
            logger.error("❌ DATABASE_URL chưa cấu hình")
            return 0

        stmt = (
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.LLM_FORMATTED)
            .where(CrawlerUrl.url_type == UrlType.POLICY_PAGE)
        )
        if run_id:
            stmt = stmt.where(CrawlerStaging.pipeline_run_id == run_id)

        ready_tasks = self.session.exec(stmt).all()
        if not ready_tasks:
            logger.warning("⚠️ Không có Policy nào ở trạng thái LLM_FORMATTED")
            return 0

        logger.info(f"📂 {len(ready_tasks)} bài viết chờ nạp vector")
        all_splits = []

        for task in ready_tasks:
            if not task.formatted_data:
                continue
            markdown_content = task.formatted_data.get("markdown_content", "")
            task_metadata    = task.formatted_data.get("metadata", {})
            if not markdown_content:
                continue

            header_splits = self.header_splitter.split_text(markdown_content)
            final_chunks  = self.text_splitter.split_documents(header_splits)

            for chunk in final_chunks:
                chunk.metadata["airline"]     = task_metadata.get("airline", "UNKNOWN")
                chunk.metadata["source_url"]  = task_metadata.get("source_url", "UNKNOWN")
                chunk.metadata["category"]    = task_metadata.get("category", "")
                chunk.metadata["staging_id"]  = task.id
                chunk.page_content = re.sub(
                    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', chunk.page_content
                )

            all_splits.extend(final_chunks)
            logger.info(f"   📄 ID {task.id} → {len(final_chunks)} chunks")
            task.status = StagingStatus.COMPLETED
            self.session.add(task)

        if not all_splits:
            logger.warning("⚠️ Không tạo được chunk nào")
            return 0

        logger.info(f"🚀 Nạp {len(all_splits)} chunks vào PGVector...")
        try:
            vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name=self.collection_name,
                connection=DATABASE_URL,
                use_jsonb=True,
            )
            vector_store.add_documents(all_splits)
            self.session.commit()
            logger.info("✅ HOÀN TẤT!")
            return len(ready_tasks)
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Lỗi: {e}")
            return 0