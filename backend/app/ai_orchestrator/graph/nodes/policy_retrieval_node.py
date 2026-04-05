import os
from collections import defaultdict
from app.ai_orchestrator.graph.state import ChatState
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.enums import ChatIntent
from app.utils.helpers import consume_task
from app.core.constants import ContextTag

def policy_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TRA CỨU CHÍNH SÁCH (RAG) ---")
    
    user_prefs = state.get("user_prefs", {})
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "general_question")
    
    query = ""
    for task in tasks:
        intent_val = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
        if intent_val == ChatIntent.GENERAL_QUESTION.value or intent_val == "general_question":
            query = getattr(task, 'query_context', "")
            break
            
    if not query:
        query = state.get("user_message", "")

    if not query:
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không xác định được câu hỏi để tra cứu chính sách."],
            "tasks": remaining_tasks
        }

    connection = os.environ.get("DATABASE_URL")
    target_airlines = user_prefs.get("target_airline", []) 
    if isinstance(target_airlines, str):
        target_airlines = [target_airlines]
    
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_store = PGVector(
            embeddings=embeddings,
            collection_name="flight_policies",
            connection=connection,
            use_jsonb=True,
        )
        
        docs = []
        if target_airlines and target_airlines != ["CLEAR"]:
            for al in target_airlines:
                search_kwargs = {"k": 3, "filter": {"airline": al.upper()}}
                res = vector_store.similarity_search(query, **search_kwargs)
                docs.extend(res)
        else:
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
                "node_results": [f"{ContextTag.SYS_NOT_FOUND}: Không tìm thấy thông tin chính sách nào phù hợp với câu hỏi: '{query}'."],
                "tasks": remaining_tasks 
            }
        
        grouped_docs = defaultdict(list)
        for doc in docs:
            airline = doc.metadata.get('airline', 'UNKNOWN').upper()
            source_url = doc.metadata.get('source_url', 'Không có link đính kèm')
            
            clean_content = " ".join(doc.page_content.replace('\n', ' ').split()).strip()
            
            if not any(item['content'] == clean_content for item in grouped_docs[airline]):
                grouped_docs[airline].append({
                    "content": clean_content,
                    "url": source_url
                })
        
        result_string = f"{ContextTag.POLICY_INFO}\n- CÂU HỎI: '{query}'\n- NỘI DUNG TRA CỨU:\n"
        
        for airline, items in grouped_docs.items():
            result_string += f"\n▶ QUY ĐỊNH CỦA HÃNG {airline}:\n"
            for idx, item in enumerate(items, 1):
                result_string += f"  {idx}. {item['content']}\n"
                result_string += f"     [Link tham khảo]: {item['url']}\n"
        
        return {
            "node_results": [result_string.strip()], 
            "tasks": remaining_tasks 
        }
        
    except Exception as e:
        print(f"ERROR - RAG Node: {e}")
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Hệ thống gặp sự cố kỹ thuật khi tra cứu tài liệu quy định."],
            "tasks": remaining_tasks
        }