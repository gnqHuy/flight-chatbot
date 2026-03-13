import os
from app.ai_orchestrator.graph.state import ChatState
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.enums import ChatIntent

def rag_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO NODE RAG (TRA CỨU CHÍNH SÁCH) ---")
    print("\n👉 [DEBUG - PREFS]: ", state.get("user_prefs", {}))
    print("\n 👉 [DEBUG - NODE]: ", state.get("node_results", {}))
    print("\n🔹🔹🔹 ------------------------------------")
    
    tasks = state.get("tasks", [])
    remaining_tasks = tasks[1:] if tasks else []
    
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
    
    try:
        vector_store = PGVector(
            embeddings=OpenAIEmbeddings(),
            collection_name="flight_policies",
            connection=connection,
            use_jsonb=True,
        )
        
        docs = vector_store.similarity_search(query, k=3)
        
        if not docs:
            return {
                "node_results": ["Không tìm thấy thông tin quy định nào liên quan đến câu hỏi."],
                "tasks": remaining_tasks 
            }
        
        retrieved_context = "THÔNG TIN QUY ĐỊNH/CHÍNH SÁCH TÌM ĐƯỢC:\n" + "\n\n".join([doc.page_content for doc in docs])
        
        return {
            "node_results": [retrieved_context],
            "tasks": remaining_tasks 
        }
        
    except Exception as e:
        print(f"Lỗi kết nối hoặc truy vấn Vector DB: {e}")
        return {
            "node_results": ["[RAG_ERROR]: Lỗi hệ thống khi tra cứu tài liệu quy định."],
            "tasks": remaining_tasks
        }