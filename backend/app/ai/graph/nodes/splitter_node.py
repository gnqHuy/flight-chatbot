from typing import List

from langchain_core.prompts import ChatPromptTemplate
from app.ai.graph.state import ChatState
from app.ai.llm.llm import llm
from pydantic import BaseModel, Field

class SubQueries(BaseModel):
    queries: List[str] = Field(description="Danh sách các câu đơn độc lập ý nghĩa")

def splitter_node(state: ChatState):    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Bạn là một chuyên gia phân tích ngôn ngữ hàng không. 
        Nhiệm vụ của bạn là chia tin nhắn phức hợp của người dùng thành các câu đơn hoặc cụm câu dựa trên Ý ĐỊNH (Intent).

        QUY TẮC CHIA (CLUSTERING):
        1. GOM NHÓM TÌM VÉ: Tất cả thông tin liên quan đến hành trình (Điểm đi, điểm đến, ngày giờ, hãng hàng không ưu tiên, yêu cầu lọc vé) PHẢI được gom lại thành một câu duy nhất.
        2. TÁCH BIỆT CÂU HỎI QUY ĐỊNH: Các câu hỏi về hành lý, thú cưng, bà bầu, giấy tờ (RAG) phải tách thành câu riêng.
        3. TÁCH BIỆT CHÀO HỎI: Các câu chào hỏi, cảm ơn phải tách riêng.

        VÍ DỤ:
        Input: "Tìm giúp tôi vé đi Đà Nẵng từ Hà Nội vào sáng mai, tiện thể check luôn quy định mang thú cưng lên máy bay thế nào và tôi chỉ muốn đi của Vietnam Airlines thôi nhé."
        Output: [
        "Tìm vé đi Đà Nẵng từ Hà Nội vào sáng mai, tôi chỉ muốn đi của Vietnam Airlines.",
        "Quy định mang thú cưng lên máy bay thế nào?"
        ]
        """),
        ("human", "{input}")
    ])
    
    splitter_chain = prompt | llm.with_structured_output(SubQueries)
    result = splitter_chain.invoke({"input": state["user_message"]})
    print ("\n🔹🔹🔹 --- KẾT QUẢ SPLITTER ---")
    print("Sub-Queries:", result.queries)
    return {"sub_queries": result.queries, "tasks": [], "node_results": ["CLEAR"], 'error_msg': None} 