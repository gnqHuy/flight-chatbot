import os
from collections import defaultdict
from app.ai_orchestrator.graph.state import ChatState
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.enums import ChatIntent
from app.utils.helpers import consume_task

def policy_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE RAG (TRA CỨU CHÍNH SÁCH) ---")
    
    user_prefs = state.get("user_prefs", {})
    print("\n👉 [DEBUG - PREFS]: ", user_prefs)
    
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "general_question")
    
    query = ""
    if tasks and hasattr(tasks[0], 'intent') and tasks[0].intent == ChatIntent.GENERAL_QUESTION:
        query = getattr(tasks[0], 'query_context', "")
            
    if not query:
        query = state.get("user_message", "")

    if not query:
        return {
            "node_results": ["Không xác định được câu hỏi để tra cứu."],
            "tasks": remaining_tasks
        }

    connection = os.environ.get("DATABASE_URL")
    target_airline = user_prefs.get("target_airline") 
    
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="flight_policies",
            connection=connection,
            use_jsonb=True,
        )
        
        docs = []
        
        if target_airline:
            search_kwargs = {"k": 3, "filter": {"airline": target_airline.upper()}}
            docs = vector_store.similarity_search(query, **search_kwargs)
            print(f"👉 [DEBUG - RAG]: Tìm kiếm tập trung vào hãng {target_airline.upper()}")
            
        else:
            print("👉 [DEBUG - RAG]: Câu hỏi chung, đang quét dữ liệu của CẢ 3 HÃNG...")
            supported_airlines = ["VN", "VJ", "QH"]
            
            for al in supported_airlines:
                res = vector_store.similarity_search(
                    query, 
                    k=2, 
                    filter={"airline": al}
                )
                docs.extend(res)

        if not docs:
            return {
                "node_results": [f"[TRA CỨU CHÍNH SÁCH]\n- Câu hỏi: {query}\n- Kết quả: Không tìm thấy thông tin."],
                "tasks": remaining_tasks 
            }
        
        grouped_docs = defaultdict(list)
        for doc in docs:
            airline = doc.metadata.get('airline', 'UNKNOWN').upper()
            clean_content = doc.page_content.replace('\n', ' ').strip() 
            grouped_docs[airline].append(clean_content)
        
        result_string = f"[TRA CỨU CHÍNH SÁCH]\n- CÂU HỎI CỦA KHÁCH: '{query}'\n- KẾT QUẢ TÌM ĐƯỢC TỪ HỆ THỐNG:\n"
        
        for airline, contents in grouped_docs.items():
            result_string += f"\n▶ QUY ĐỊNH CỦA HÃNG {airline}:\n"
            for idx, content in enumerate(contents, 1):
                result_string += f"  {idx}. {content}\n"
                
        print("\n👉 [DEBUG - RAG RESULT]: Trích xuất thành công", len(docs), "đoạn văn.")
        
        return {
            "node_results": [result_string.strip()], 
            "tasks": remaining_tasks 
        }
        
    except Exception as e:
        print(f"Lỗi kết nối hoặc truy vấn Vector DB: {e}")
        return {
            "node_results": ["[RAG_ERROR]: Lỗi hệ thống khi tra cứu tài liệu quy định."],
            "tasks": remaining_tasks
        }