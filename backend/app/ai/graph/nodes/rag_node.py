import os
from app.ai.graph.state import ChatState
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector

def rag_node(state: ChatState) -> ChatState:
    connection = os.environ.get("DATABASE_URL")
    
    vector_store = PGVector(
        embeddings=OpenAIEmbeddings(),
        collection_name="flight_policies",
        connection=connection,
        use_jsonb=True,
    )
    
    docs = vector_store.similarity_search(state.user_message, k=3)
    
    retrieved_context = "\n\n".join([doc.page_content for doc in docs])
    
    return state.copy(update={"context": retrieved_context})