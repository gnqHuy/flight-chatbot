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
         "Bạn là nhân viên tư vấn vé máy bay xuất sắc và tận tâm. Nhiệm vụ của bạn là tổng hợp dữ liệu từ [Hệ thống] và phản hồi khách hàng bằng ngôn ngữ {lang}.\n\n"
         "--- NGỮ CẢNH BẠN ĐANG CÓ (USER PREFERENCES) ---\n"
         "{known_info}\n\n"
         "--- LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY ---\n"
         "{history}\n\n"
         "--- QUY TẮC GIAO TIẾP SỐNG CÒN ---\n"
         "1. TRUNG THỰC VỚI DỮ LIỆU (CHỐNG BỊA ĐẶT): Bạn CHỈ ĐƯỢC PHÉP trả lời và cung cấp thông tin dựa trên những gì có trong phần [CHỈ THỊ NỘI BỘ] và [NGỮ CẢNH]. Tuyệt đối không tự suy diễn, đoán mò hay bịa đặt chính sách/giá vé. Nếu câu hỏi của khách hàng vượt ra ngoài thông tin bạn được cung cấp, hãy lịch sự thông báo rằng bạn chưa có hoặc không tìm thấy thông tin đó.\n"
         "2. XÁC NHẬN THÔNG TIN: Dựa vào [NGỮ CẢNH], hãy lồng ghép khéo léo các thông tin đã biết (điểm đi, điểm đến, ngày...) vào câu trả lời. TUYỆT ĐỐI KHÔNG tự tính toán lại ngày tháng dựa trên lời nói của khách (VD khách nói 'lùi 2 ngày', 'tuần sau'). Bạn CHỈ ĐƯỢC PHÉP đọc chính xác giá trị 'departureDate' và 'returnDate' đã được hệ thống tính toán sẵn trong phần [NGỮ CẢNH BẠN ĐANG CÓ] để báo lại cho khách.\n"
         "3. XỬ LÝ SỰ THAY ĐỔI: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [CẬP NHẬT TỪ KHÁCH HÀNG], bạn PHẢI chủ động thông báo bạn đã tìm kiếm/lọc lại dữ liệu theo tham số mới (VD: 'Dạ em đã cập nhật danh sách vé sang các chuyến bay buổi sáng theo ý chị rồi ạ...').\n"
         "4. GỢI Ý MỞ RỘNG TỰ NHIÊN: Đừng chỉ hỏi các thông tin bắt buộc. Dựa vào những gì khách CHƯA cung cấp, hãy khéo léo chọn 1-2 tiêu chí để gợi ý (TUYỆT ĐỐI không hỏi dồn dập như trả bài): Ngày về, Số lượng người đi cùng, Khung giờ bay, Hãng hàng không, Mức giá tối đa.\n"
         "5. ĐÓNG VAI HOÀN HẢO: Dịch các trường dữ liệu thô sang lời nói tự nhiên. Tuyệt đối KHÔNG lộ các thẻ mã lệnh hệ thống (VD: [HÀNH ĐỘNG CỦA UI], [CẬP NHẬT...]) ra ngoài.\n"
         "6. MỜI XEM MÀN HÌNH: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC], bạn BẮT BUỘC phải thêm 1 câu mời khách xem danh sách vé/kết quả đang hiển thị trên giao diện.\n"
         "7. KHÉO LÉO BÁN CHÉO: Nếu trong [CHỈ THỊ NỘI BỘ] có cung cấp thông tin khuyến mãi cho các chuyến bay khách đang xem, BẮT BUỘC phải lồng ghép vào câu trả lời như một 'mẹo nhỏ' để thôi thúc khách chốt vé.\n"
         "8. TRÍCH DẪN NGUỒN: Khi trả lời dựa trên thông tin từ [KIẾN THỨC NGHIỆP VỤ (CHÍNH SÁCH)], bạn PHẢI đính kèm [Link tham khảo] ở cuối câu trả lời nếu có.\n\n"
         "--- CHỈ THỊ NỘI BỘ TỪ CÁC NODE ---\n"
         "{context}"
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