import re
import logging
from enum import Enum
from sqlmodel import Session, select
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.config import OPENAI_API_KEY, DATABASE_URL
from app.database.models.crawler_staging import CrawlerStaging
from app.database.models.crawler_url import CrawlerUrl, UrlType
from app.core.enums import StagingStatus 

logger = logging.getLogger(__name__)

class PolicyDBIngester:
    def __init__(self, session: Session):
        self.session = session
        self.collection_name = "flight_policies"
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=OPENAI_API_KEY
        )
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    def ingest_to_db(self):
        logger.info("🗄️ BƯỚC 3: BẮT ĐẦU CHIA NHỎ VÀ NẠP DỮ LIỆU CHÍNH SÁCH VÀO VECTOR DB...")
        
        if not DATABASE_URL:
            logger.error("❌ Lỗi: DATABASE_URL chưa được cấu hình!")
            return False

        statement = (
            select(CrawlerStaging)
            .join(CrawlerUrl, CrawlerStaging.url_id == CrawlerUrl.id)
            .where(CrawlerStaging.status == StagingStatus.LLM_FORMATTED)
            .where(CrawlerUrl.url_type == UrlType.POLICY_PAGE)
        )
        
        ready_tasks = self.session.exec(statement).all()

        if not ready_tasks:
            logger.warning("⚠️ Không có dữ liệu Policy nào ở trạng thái LLM_FORMATTED để nạp.")
            return False

        all_splits = []
        logger.info(f"📂 Tìm thấy {len(ready_tasks)} bài viết chờ nạp Vector.")
        
        for task in ready_tasks:
            if not task.formatted_data:
                continue
                
            markdown_content = task.formatted_data.get("markdown_content", "")
            task_metadata = task.formatted_data.get("metadata", {})
            
            if not markdown_content:
                continue

            header_splits = self.header_splitter.split_text(markdown_content)
            
            final_chunks = self.text_splitter.split_documents(header_splits)
            
            for chunk in final_chunks:
                chunk.metadata["airline"] = task_metadata.get("airline", "UNKNOWN")
                chunk.metadata["source_url"] = task_metadata.get("source_url", "UNKNOWN")
                chunk.metadata["category"] = task_metadata.get("category", "")
                chunk.metadata["staging_id"] = task.id
                
                chunk.page_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', chunk.page_content)
            
            all_splits.extend(final_chunks)
            logger.info(f"   📄 Đã băm nhỏ ID {task.id} thành {len(final_chunks)} chunks.")
            
            task.status = StagingStatus.COMPLETED
            self.session.add(task)

        if not all_splits:
            logger.warning("⚠️ Không tạo được chunk nào từ dữ liệu.")
            return False

        logger.info(f"🚀 Đang tính toán Vector và nạp {len(all_splits)} chunks vào PGVector...")
        
        try:
            vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name=self.collection_name,
                connection=DATABASE_URL,
                use_jsonb=True,
            )
            vector_store.add_documents(all_splits)
            
            self.session.commit()
            
            logger.info("✅ THÀNH CÔNG: Kho tri thức (Policies) đã sẵn sàng trong Database!")
            return True
            
        except Exception as e:
            self.session.rollback()
            logger.error(f"❌ Lỗi khi nạp DB Chính sách: {e}")
            return False