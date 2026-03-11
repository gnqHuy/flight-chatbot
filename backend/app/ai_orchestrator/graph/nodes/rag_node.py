import os
from app.ai_orchestrator.graph.state import ChatState
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

from app.core.enums import ChatIntent

def rag_node(state: ChatState) -> dict:
    query = ""
    tasks = state.get("tasks", [])
    for task in tasks:
        if task.intent == ChatIntent.GENERAL_QUESTION and task.query_context:
            query = task.query_context
            break
            
    if not query:
        query = state["messages"][-1].content

    connection = os.environ.get("DATABASE_URL")
    
    vector_store = PGVector(
        embeddings=OpenAIEmbeddings(),
        collection_name="flight_policies",
        connection=connection,
        use_jsonb=True,
    )
    
    docs = vector_store.similarity_search(query, k=3)
    
    if not docs:
        return {"node_results": ["Không tìm thấy thông tin quy định nào liên quan."]}
    
    retrieved_context = "THÔNG TIN QUY ĐỊNH/CHÍNH SÁCH TÌM ĐƯỢC:\n" + "\n\n".join([doc.page_content for doc in docs])
    
    return {
        "node_results": [retrieved_context]
    }