from collections import defaultdict
from app.ai_orchestrator.graph.state import ChatState

from app.core.enums import ChatIntent
from app.utils.helpers import consume_task
from app.core.constants import SUPPORTED_AIRLINES, ContextTag

from app.ai_orchestrator.rag.vector_store import policy_vector_store 

def policy_retrieval_node(state: ChatState) -> dict:
    print("\n🔹🔹🔹 --- VÀO TRẠM TRA CỨU CHÍNH SÁCH (RAG) ---")
    
    search_filters = state.get("search_filters", {})
    action_targets = state.get("action_targets", {})
    tasks = state.get("tasks", [])
    remaining_tasks = consume_task(tasks, "policy_question")
    
    query = ""
    for task in tasks:
        intent_val = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
        if intent_val == ChatIntent.POLICY_QUESTION.value or intent_val == "POLICY_QUESTION":
            query = getattr(task, 'query_context', "")
            break
            
    if not query:
        query = state["user_message"] or ""

    if not query:
        return {
            "node_results": [f"{ContextTag.SYS_ERROR}: Không xác định được câu hỏi để tra cứu chính sách."],
            "tasks": remaining_tasks
        }

    target_airlines = []
    if action_targets.get("compare_airlines"):
        target_airlines = action_targets.get("compare_airlines")
    elif search_filters.get("preferred_airlines"):
        target_airlines = search_filters.get("preferred_airlines")

    if isinstance(target_airlines, str):
        target_airlines = [target_airlines]
    
    try:
        docs = []
        if target_airlines and target_airlines != ["CLEAR"]:
            for al in target_airlines:
                search_kwargs = {"k": 3, "filter": {"airline": al.upper()}}
                res = policy_vector_store.similarity_search(query, **search_kwargs)
                docs.extend(res)
        else:
            for al in SUPPORTED_AIRLINES:
                res = policy_vector_store.similarity_search(
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