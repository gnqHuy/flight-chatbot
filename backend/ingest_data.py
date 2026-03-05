import os
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

load_dotenv()

dummy_text = """
1. Quy định hành lý xách tay: Hành khách hạng Phổ thông (Economy) được mang tối đa 1 kiện hành lý xách tay nặng không quá 7kg. Hành khách hạng Thương gia (Business) được mang 2 kiện, mỗi kiện không quá 7kg.
2. Quy định hoàn/hủy vé: Vé khuyến mãi (Promo) không được phép hoàn tiền dưới mọi hình thức. Vé hạng Phổ thông tiêu chuẩn được phép hoàn vé nhưng mất phí 500,000 VND.
3. Quy định phụ nữ mang thai: Phụ nữ mang thai dưới 28 tuần được tham gia chuyến bay bình thường. Phụ nữ mang thai từ 28 tuần đến 32 tuần bắt buộc phải có giấy xác nhận sức khỏe của bác sĩ cấp trong vòng 7 ngày trước chuyến bay.
4. Giấy tờ tùy thân: Hành khách bay nội địa cần mang theo một trong các giấy tờ sau: Chứng minh nhân dân, Căn cước công dân, Hộ chiếu hoặc Giấy phép lái xe. Trẻ em dưới 14 tuổi cần có Giấy khai sinh bản gốc hoặc bản sao trích lục.
"""

def ingest_dummy_data():
    os.makedirs("data/policies", exist_ok=True)
    file_path = "data/policies/dummy_policy.txt"
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(dummy_text)
        
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=50,
    )
    docs = [Document(page_content=text)]
    splits = text_splitter.split_documents(docs)

    connection = os.environ.get("DATABASE_URL")
    collection_name = "flight_policies"
    embeddings = OpenAIEmbeddings()

    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=connection,
        use_jsonb=True,
    )

    vector_store.add_documents(splits)
    print(f"Success: Ingested {len(splits)} chunks to PostgreSQL.")

if __name__ == "__main__":
    ingest_dummy_data()