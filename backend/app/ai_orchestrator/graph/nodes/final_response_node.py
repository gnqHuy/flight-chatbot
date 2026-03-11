from datetime import datetime
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.llm.llm import llm
from langchain_core.prompts import ChatPromptTemplate

def final_response_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE TỔNG HỢP CÂU TRẢ LỜI ---")
    print("Current State in Final Response Node: \n", state)
    
    lang = state.get("language") or "vi"
    user_message = state.get("user_message", "")
    tasks = state.get("tasks", [])
    node_results = state.get("node_results", [])
    action = state.get("action")
    error_msg = state.get("error_msg")
    history_list = state.get("chat_history", [])

    history_str = "\n".join(history_list) if history_list else "Chưa có lịch sử."
    
    intents = [task.intent.value if hasattr(task.intent, 'value') else str(task.intent) for task in tasks]

    current_time_str = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

    system_instructions = []

    if not intents:
        system_instructions.append("[HỆ THỐNG]: Không rõ ý định của khách. Hãy lịch sự hỏi lại họ cần giúp gì về vé máy bay.")
    elif "out_of_scope" in intents:
        system_instructions.append("[HỆ THỐNG]: Khách hỏi ngoài lề. Hãy từ chối khéo léo và nhắc họ bạn chỉ hỗ trợ đặt vé máy bay.")

    if error_msg:
        system_instructions.append(f"[LỖI HỆ THỐNG]: Lỗi API hoặc Backend: {error_msg}. Hãy xin lỗi khách.")

    for result in node_results:
        if not result: continue
        
        if "[SLOT_FILLING_REQUIRED]" in result or "[INVALID" in result:
            system_instructions.append(f"[YÊU CẦU THÔNG TIN]: {result}")
            
        elif "[BÁO CÁO PHÂN TÍCH SO SÁNH]" in result:
            system_instructions.append(f"[DỮ LIỆU SO SÁNH]: \n{result}")
            
        elif "[KIẾN THỨC NGHIỆP VỤ]" in result or "general_question" in intents:
            system_instructions.append(f"[KIẾN THỨC NGHIỆP VỤ]: \n{result}")
            
        elif "FOUND" in result: 
            system_instructions.append(f"[THÔNG TIN CHUYẾN BAY]: {result}")
            
        else:
            system_instructions.append(f"[THÔNG TIN BỔ SUNG]: {result}")

    if action and action.get("type") == "flight_list":
        system_instructions.append("[HÀNH ĐỘNG]: Đã hiển thị danh sách vé trên màn hình của khách.")

    if "greeting" in intents and not node_results:
        system_instructions.append("[HỆ THỐNG]: Khách đang chào. Hãy chào lại vui vẻ và đề nghị giúp đỡ tìm chuyến bay.")

    combined_context = "\n\n".join(system_instructions)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Bạn là nhân viên tư vấn vé máy bay xuất sắc. Nhiệm vụ của bạn là truyền đạt lại [CHỈ THỊ NỘI BỘ] tới khách hàng bằng ngôn ngữ {lang}.\n\n"
         "THÔNG TIN THỜI GIAN THỰC:\n"
         "Hôm nay là: {current_time}\n\n"
         "QUY TẮC SỐNG CÒN (CRITICAL RULES):\n"
         "1. ĐÓNG VAI HOÀN HẢO: Bạn LÀ hệ thống. Bạn CÓ dữ liệu thực tế. TUYỆT ĐỐI KHÔNG xưng là AI, KHÔNG nói 'tôi không thể tìm kiếm', KHÔNG bảo khách tự lên web hãng.\n"
         "2. DỊCH THUẬT DỮ LIỆU THÔ: [CHỈ THỊ] có thể chứa dữ liệu thô (tiếng Anh). Hãy dịch sang lời nói tự nhiên (VD: 'FOUND: 20 flights' -> 'Dạ em tìm thấy 20 chuyến bay', 'origin' -> 'điểm đi').\n"
         "3. TIN TƯỞNG DỮ LIỆU: Nếu khách hỏi 'ngày mai' và [CHỈ THỊ] trả về kết quả, hãy tự tin trả lời kết quả đó dựa vào thời gian thực ở trên.\n"
         "4. KHÔNG lộ mã lệnh kỹ thuật ([SLOT_FILLING_REQUIRED], [HÀNH ĐỘNG]...).\n"
         "5. Lịch sử trò chuyện giúp bạn hiểu ngữ cảnh và xưng hô.\n\n"
         "--- LỊCH SỬ TRÒ CHUYỆN ---\n{history}\n\n"
         "--- CHỈ THỊ NỘI BỘ ---\n{context}"
        ),
        ("human", "{question}")
    ])

    formatted_messages = prompt.format_messages(
        context=combined_context, 
        history=history_str,
        question=user_message,
        lang=lang,
        current_time=current_time_str
    )

    print("\n" + "="*60)
    print("🚀 [FULL PROMPT GỬI LLM]")
    for msg in formatted_messages:
        print(f"\n[{msg.type.upper()} MESSAGE]:\n{msg.content}")
    print("="*60 + "\n")
    
    response = llm.invoke(formatted_messages)

    return {"response_text": response.content}