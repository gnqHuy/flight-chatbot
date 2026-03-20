import os
import re
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

# 1. Cấu hình ban đầu
load_dotenv()
INPUT_DIR = "data/cleaned_policies"
CONNECTION_STRING = os.environ.get("DATABASE_URL")
COLLECTION_NAME = "flight_policies"

# Định nghĩa các đầu mục để cắt file Markdown (Giúp giữ ngữ cảnh cho bảng biểu)
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

def ingest_all_cleaned_md():
    if not CONNECTION_STRING:
        print("❌ Lỗi: DATABASE_URL không tồn tại trong file .env")
        return

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)

    all_splits = []

    print(f"📂 Đang quét thư mục: {INPUT_DIR}")
    
    for airline in os.listdir(INPUT_DIR):
        airline_path = os.path.join(INPUT_DIR, airline)
        if not os.path.isdir(airline_path): continue

        for filename in os.listdir(airline_path):
            if filename.endswith(".md"):
                file_path = os.path.join(airline_path, filename)
                
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                header_splits = header_splitter.split_text(raw_content)
                
                final_chunks = text_splitter.split_documents(header_splits)
                
                for chunk in final_chunks:
                    chunk.metadata["airline"] = airline.upper()
                    chunk.metadata["source"] = filename
                    chunk.page_content = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', chunk.page_content)
                
                all_splits.extend(final_chunks)
                print(f"   📄 Đã xử lý: {airline}/{filename} ({len(final_chunks)} chunks)")

    if not all_splits:
        print("⚠️ Không tìm thấy dữ liệu Markdown nào để nạp.")
        return

    print(f"🚀 Đang nạp {len(all_splits)} chunks vào PostgreSQL (pgvector)...")
    
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )

    vector_store.add_documents(all_splits)
    print("\n✅ THÀNH CÔNG: Kho tri thức đã sẵn sàng trong PostgreSQL!")

if __name__ == "__main__":
    ingest_all_cleaned_md()