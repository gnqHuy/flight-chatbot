import os
import re
import logging
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.config import OPENAI_API_KEY, DATABASE_URL

logger = logging.getLogger(__name__)

class PolicyDBIngester:
    def __init__(self):
        self.input_dir = os.path.join("app", "data", "policies", "cleaned_policies")
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
        logger.info("🗄️ BƯỚC 3: BẮT ĐẦU CHIA NHỎ VÀ NẠP DỮ LIỆU CHÍNH SÁCH VÀO DATABASE...")
        
        if not DATABASE_URL:
            logger.error("❌ Lỗi: DATABASE_URL chưa được cấu hình!")
            return False

        all_splits = []
        logger.info(f"📂 Đang quét thư mục: {self.input_dir}")
        
        for airline in os.listdir(self.input_dir):
            airline_path = os.path.join(self.input_dir, airline)
            if not os.path.isdir(airline_path): 
                continue

            for filename in os.listdir(airline_path):
                if filename.endswith(".md"):
                    file_path = os.path.join(airline_path, filename)
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        raw_content = f.read()

                    header_splits = self.header_splitter.split_text(raw_content)
                    
                    final_chunks = self.text_splitter.split_documents(header_splits)
                    
                    for chunk in final_chunks:
                        chunk.metadata["airline"] = airline.upper()
                        chunk.metadata["source"] = filename
                        chunk.page_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', chunk.page_content)
                    
                    all_splits.extend(final_chunks)
                    logger.info(f"   📄 Đã xử lý: {airline}/{filename} ({len(final_chunks)} chunks)")

        if not all_splits:
            logger.warning("⚠️ Không tìm thấy dữ liệu Markdown nào để nạp.")
            return False

        logger.info(f"🚀 Đang nạp {len(all_splits)} chunks vào PostgreSQL (pgvector)...")
        
        try:
            vector_store = PGVector(
                embeddings=self.embeddings,
                collection_name=self.collection_name,
                connection=DATABASE_URL,
                use_jsonb=True,
            )
            vector_store.add_documents(all_splits)
            logger.info("✅ THÀNH CÔNG: Kho tri thức (Policies) đã sẵn sàng trong PostgreSQL!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi nạp DB Chính sách: {e}")
            return False