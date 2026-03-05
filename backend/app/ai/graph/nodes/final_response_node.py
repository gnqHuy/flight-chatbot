from app.ai.graph.state import ChatState
from app.core.i18n_service import i18n
from app.ai.llm.llm import llm
from langchain_core.prompts import ChatPromptTemplate

def final_response_node(state: ChatState):
    lang = state.get("language") or "vi"
    user_message = state.get("user_message", "")
    tasks = state.get("tasks", [])
    node_results = state.get("node_results", [])
    action = state.get("action")
    error_msg = state.get("error_msg")

    intents = [task.intent for task in tasks]

    if not intents:
        return {"response_text": i18n.get_msg("unknown_intent", lang=lang)}
    
    if "out_of_scope" in intents:
        return {"response_text": i18n.get_msg("ood_response", lang=lang)}

    system_instructions = []

    if error_msg:
        err = i18n.get_msg("api_error", lang=lang) or error_msg
        system_instructions.append(f"[LỖI HỆ THỐNG]: {err}")

    for result in node_results:
        if not result: continue
        
        if "[SLOT_FILLING_REQUIRED]" in result:
            system_instructions.append(f"[YÊU CẦU THÔNG TIN]: {result}")
            
        elif "[BÁO CÁO PHÂN TÍCH SO SÁNH]" in result:
            system_instructions.append(f"[DỮ LIỆU SO SÁNH]: {result}")
            
        elif "[Quy định hàng không]" in result or "general_question" in intents:
            system_instructions.append(f"[KIẾN THỨC NGHIỆP VỤ]: {result}")
            
        else:
            system_instructions.append(f"[THÔNG TIN CHUYẾN BAY]: {result}")

    if action and action.get("type") == "flight_list":
        system_instructions.append("[HÀNH ĐỘNG]: Đã hiển thị danh sách vé bên dưới.")

    if "greeting" in intents and not system_instructions:
        return {"response_text": i18n.get_msg("greeting_response", lang=lang)}

    if system_instructions:
        combined_context = "\n\n".join(system_instructions)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "Bạn là trợ lý hàng không chuyên nghiệp. Hãy đọc [CHỈ THỊ NỘI BỘ] "
             "để tạo câu trả lời tự nhiên bằng ngôn ngữ {lang}.\n\n"
             "QUY TẮC:\n"
             "1. Không lặp lại mã lệnh [SLOT_FILLING_REQUIRED] hay [BÁO CÁO].\n"
             "2. Ưu tiên hỏi thông tin thiếu nếu có.\n"
             "3. Kết nối các ý mạch lạc.\n"
             "4. Lịch sự, chuyên nghiệp.\n\n"
             "--- CHỈ THỊ NỘI BỘ ---\n{context}"
            ),
            ("human", "{question}")
        ])
        
        chain = prompt | llm
        response = chain.invoke({
            "context": combined_context, 
            "question": user_message,
            "lang": lang
        })
        
        return {"response_text": response.content}

    return {"response_text": i18n.get_msg("unknown_intent", lang=lang)}