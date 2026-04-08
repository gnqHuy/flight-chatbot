from datetime import datetime
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from langchain_core.prompts import ChatPromptTemplate
from app.utils.promo_injector import check_and_inject_promos
from app.core.constants import ContextTag

def final_response_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE TỔNG HỢP CÂU TRẢ LỜI ---")
    
    lang = state.get("language") or "vi"
    user_message = state.get("user_message", "")
    user_prefs = state.get("user_prefs", {})
    node_results = state.get("node_results", [])
    action = state.get("action")
    error_msg = state.get("error_msg")
    current_search_id = state.get("current_search_id")
    
    history_dict = state.get("chat_history", {})
    history_list = history_dict.get("messages", []) if isinstance(history_dict, dict) else []
    history_str = "\n".join(history_list[-10:]) if history_list else "Chưa có lịch sử."
    
    current_time_str = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

    system_instructions = []

    if error_msg:
        system_instructions.append(f"{ContextTag.SYS_ERROR}: {error_msg}. Hãy xin lỗi khách và giải thích ngắn gọn.")

    if not node_results and not action and not error_msg:
        system_instructions.append("[HỆ THỐNG]: Khách đang chào hỏi hoặc hỏi ngoài lề (không kích hoạt tác vụ tìm kiếm nào). Hãy giao tiếp lịch sự, tự nhiên và hướng họ về dịch vụ vé máy bay nếu cần.")
    else:
        valid_results = [res for res in node_results if res]
        system_instructions.extend(valid_results)

    combined_context = "\n\n".join(system_instructions)

    if ContextTag.FLIGHT_FOUND in combined_context:
        promo_context = check_and_inject_promos(current_search_id)
        if promo_context:
            combined_context += f"\n\n{ContextTag.PROMO_INFO}:\n{promo_context}"
            print("👉 [DEBUG]: Đã tiêm thành công khuyến mãi vào Context cho LLM!")

    known_info = {k: v for k, v in user_prefs.items() if v and k != "current_search_id"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", 
        "Bạn là chuyên viên tư vấn vé máy bay xuất sắc, chuyên nghiệp và tận tâm.\n"
        "NHIỆM VỤ: Tổng hợp dữ liệu từ hệ thống và phản hồi khách hàng bằng ngôn ngữ {lang}. Phản hồi phải TỰ NHIÊN, NGẮN GỌN và ĐÚNG TRỌNG TÂM.\n\n"
        
        "--- 1. NGỮ CẢNH HỆ THỐNG ---\n"
        "[THÔNG TIN ĐÃ BIẾT]: {known_info}\n"
        "[CHỈ THỊ TỪ BACKEND]: {context}\n"
        "[LỊCH SỬ CHAT]: {history}\n\n"
        
        "--- 2. NGUYÊN TẮC 'THÉP' (CHỐNG ẢO GIÁC) ---\n"
        "- TRUNG THỰC: CHỈ dùng thông tin có trong [THÔNG TIN ĐÃ BIẾT] và [CHỈ THỊ TỪ BACKEND]. Tuyệt đối KHÔNG tự bịa giá vé, giờ bay hay chính sách.\n"
        "- KHÔNG TỰ TÍNH TOÁN: Chỉ đọc đúng giá trị `departureDate`, `returnDate` mà hệ thống cung cấp. KHÔNG tự suy luận ngày tháng (VD khách nói 'tuần sau' thì không tự cộng ngày).\n"
        "- ẨN MÃ LỆNH: Tuyệt đối KHÔNG để lọt các thẻ hệ thống (VD: [USER_UPDATE], [SYS_FOUND]...) vào câu trả lời.\n\n"

        "--- 3. ĐỊNH HƯỚNG PHẢN HỒI (TÙY THEO CHỈ THỊ) ---\n"
        "Hãy đọc kỹ [CHỈ THỊ TỪ BACKEND] để chọn cách trả lời phù hợp nhất (Chỉ chọn 1-2 ý chính, KHÔNG nói dài dòng):\n\n"
        
        "A. TRẠNG THÁI 'TÌM THẤY VÉ' (Có nhắc đến danh sách vé/kết quả):\n"
        "   - Tóm tắt nhẹ nhàng (VD: 'Em đã tìm thấy các chuyến bay đi Đà Nẵng ngày 20/5...').\n"
        "   - BẮT BUỘC: Thêm 1 câu mời khách xem danh sách vé đang hiển thị trên màn hình.\n"
        "   - Nếu có khuyến mãi -> Nhắc nhẹ 1 câu như một mẹo nhỏ để chốt vé.\n\n"
        
        "B. TRẠNG THÁI 'CẬP NHẬT/LỌC VÉ' (Có nhắc đến việc áp dụng bộ lọc/sắp xếp):\n"
        "   - Xác nhận ngay hành động (VD: 'Dạ em đã lọc ra các chuyến bay buổi sáng của Vietjet theo ý anh rồi ạ').\n"
        "   - Mời khách xem lại màn hình.\n\n"
        
        "C. TRẠNG THÁI 'THIẾU THÔNG TIN' (Đang thu thập thông tin cốt lõi):\n"
        "   - Chỉ hỏi 1-2 thông tin quan trọng nhất còn thiếu (Ngày bay, Điểm đến, Số người).\n"
        "   - Hỏi một cách tự nhiên, KHÔNG hỏi dồn dập như tra khảo.\n\n"
        
        "D. TRẠNG THÁI 'PHÂN TÍCH / HỎI ĐÁP' (Có dữ liệu so sánh hoặc chính sách):\n"
        "   - Trả lời trực tiếp vào câu hỏi. Bố cục rõ ràng, dễ đọc.\n"
        "   - BẮT BUỘC đính kèm [Link tham khảo] ở cuối câu nếu trong chỉ thị có cung cấp link.\n\n"

        "--- 4. NGHỆ THUẬT GIAO TIẾP ---\n"
        "- Giọng điệu ân cần, dạ thưa lịch sự (nếu dùng tiếng Việt).\n"
        "- Không lặp lại như vẹt toàn bộ [THÔNG TIN ĐÃ BIẾT] nếu khách không hỏi.\n"
        "- Câu trả lời hoàn hảo dài từ 2-5 câu."
        ),
        ("human", "{question}")
    ])

    formatted_messages = prompt.format_messages(
        context=combined_context, 
        history=history_str,
        known_info=known_info,
        question=user_message,
        lang=lang,
        current_time=current_time_str
    )

    response = llm.invoke(formatted_messages)
    bot_reply = response.content 
    
    current_exchange = f"User: {state.get('user_message')}\nBot: {bot_reply}"
    print("\n🔹🔹🔹 ------------------------------------")

    return {"response_text": bot_reply, "chat_history": {"messages": [current_exchange]}}