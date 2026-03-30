from datetime import datetime
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from langchain_core.prompts import ChatPromptTemplate
from app.utils.promo_injector import check_and_inject_promos

def final_response_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE TỔNG HỢP CÂU TRẢ LỜI ---")
    print("\n👉 [DEBUG - PREFS]: ", state.get("user_prefs", {}))
    print("\n👉 [DEBUG - NODE]: ", state.get("node_results", {}))
    print("\n🔹🔹🔹 ------------------------------------")
    
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
        system_instructions.append(f"[LỖI HỆ THỐNG]: {error_msg}. Hãy xin lỗi khách và giải thích ngắn gọn.")

    if not node_results and not action and not error_msg:
        system_instructions.append("[HỆ THỐNG]: Khách đang chào hỏi hoặc hỏi ngoài lề (không kích hoạt tác vụ tìm kiếm nào). Hãy giao tiếp lịch sự, tự nhiên và hướng họ về dịch vụ vé máy bay nếu cần.")
    else:
        for result in node_results:
            if not result: continue
            
            result_upper = result.upper()
            
            if "[CẬP NHẬT THÔNG TIN]" in result_upper:
                system_instructions.append(f"[CẬP NHẬT TỪ KHÁCH HÀNG]:\n{result}")
                
            elif "[YÊU CẦU THÔNG TIN]" in result_upper or "[INVALID]" in result_upper:
                system_instructions.append(f"[YÊU CẦU THÔNG TIN]:\n{result}")
                
            elif "[KHÔNG_TÌM_THẤY]" in result_upper or "[LỖI]" in result_upper:
                system_instructions.append(f"[TRỤC TRẶC HỆ THỐNG]:\n{result}")
                
            elif "[BÁO CÁO PHÂN TÍCH]" in result_upper or "SO SÁNH" in result_upper:
                system_instructions.append(f"[DỮ LIỆU SO SÁNH CHUYẾN BAY]: \n{result}")
                
            elif "[TRA CỨU CHÍNH SÁCH]" in result_upper:
                system_instructions.append(f"[KIẾN THỨC NGHIỆP VỤ (CHÍNH SÁCH)]: \n{result}")
                
            elif "[TRA CỨU KHUYẾN MÃI]" in result_upper: 
                system_instructions.append(f"[THÔNG TIN KHUYẾN MÃI TỪ HỆ THỐNG]: \n{result}")
                
            elif "[THÔNG TIN CHUYẾN BAY]" in result_upper or "[TÌM_THẤY]" in result_upper: 
                system_instructions.append(f"[DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC]:\n{result}")
                
            else:
                system_instructions.append(f"[THÔNG TIN BỔ SUNG]:\n{result}")

    combined_context = "\n\n".join(system_instructions)

    if "THÔNG TIN CHUYẾN BAY" in combined_context or "BÁO CÁO PHÂN TÍCH" in combined_context:
        print("👉 [DEBUG]: Đang rà soát Khuyến mãi ẩn để bán chéo...")
        promo_context = check_and_inject_promos(current_search_id)
        if promo_context:
            combined_context += f"\n\n{promo_context}"
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
         "2. XÁC NHẬN THÔNG TIN: Dựa vào [NGỮ CẢNH], hãy lồng ghép khéo léo các thông tin đã biết (điểm đi, điểm đến, ngày...) vào câu trả lời để khách yên tâm.\n"
         "3. XỬ LÝ SỰ THAY ĐỔI: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [CẬP NHẬT TỪ KHÁCH HÀNG], bạn PHẢI chủ động thông báo bạn đã tìm kiếm lại/lọc lại dữ liệu theo tham số mới đó (VD: 'Dạ em đã cập nhật danh sách vé sang các chuyến bay buổi sáng theo ý chị rồi ạ...').\n"
         "4. GỢI Ý MỞ RỘNG TỰ NHIÊN (OPTIONAL): Đừng chỉ hỏi các thông tin bắt buộc. Dựa vào những gì khách CHƯA cung cấp, hãy khéo léo chọn 1-2 tiêu chí trong danh sách sau để gợi ý (TUYỆT ĐỐI không hỏi dồn dập như trả bài):\n"
         "   - Ngày về (để mua vé khứ hồi).\n"
         "   - Số lượng người đi cùng (người lớn, trẻ em).\n"
         "   - Khung giờ bay mong muốn (sáng, trưa, chiều, tối hoặc giờ cụ thể).\n"
         "   - Hãng hàng không yêu thích hoặc hãng muốn tránh.\n"
         "   - Ưu tiên bay thẳng (không điểm dừng).\n"
         "   - Hạng ghế (Thương gia, Phổ thông, ...).\n"
         "   - Ngân sách / Mức giá tối đa mong muốn.\n"
         "   - Tiêu chí ưu tiên khi so sánh (muốn tìm chuyến rẻ nhất, bay nhanh nhất, hay cất cánh sớm nhất).\n"
         "5. ĐÓNG VAI HOÀN HẢO: Dịch các trường dữ liệu thô sang lời nói tự nhiên. Tuyệt đối KHÔNG lộ các thẻ mã lệnh hệ thống (VD: [HÀNH ĐỘNG CỦA UI], [CẬP NHẬT...]) ra ngoài.\n"
         "6. MỜI XEM MÀN HÌNH: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [DỮ LIỆU CHUYẾN BAY TÌM ĐƯỢC], bạn BẮT BUỘC phải thêm 1 câu mời khách xem danh sách vé/kết quả đang hiển thị trên giao diện.\n"
         "7. KHÉO LÉO BÁN CHÉO (CROSS-SELL): Nếu trong [CHỈ THỊ NỘI BỘ] có cung cấp thông tin mã giảm giá/khuyến mãi cho các chuyến bay khách đang xem, BẮT BUỘC phải lồng ghép vào câu trả lời như một 'mẹo nhỏ' hoặc 'đặc quyền' để thôi thúc khách chốt vé.\n"
         "8. TRÍCH DẪN NGUỒN (RẤT QUAN TRỌNG): Khi trả lời dựa trên thông tin từ [KIẾN THỨC NGHIỆP VỤ (CHÍNH SÁCH)], bạn PHẢI sao chép Y NGUYÊN và đính kèm [Link tham khảo] ở cuối câu trả lời. TUYỆT ĐỐI không được bỏ qua link này.\n"
         "9. XỬ LÝ LOGIC GIỚI HẠN: Khi khách hàng hỏi về một mốc số liệu (ví dụ: đúng 32 tuần tuổi thai), hãy chú ý phân biệt rõ giữa 'ĐẾN 32 tuần' (được phép bay nhưng cần giấy tờ) và 'TRÊN 32 tuần' (từ chối vận chuyển) dựa trên tài liệu được cung cấp. Cung cấp cả 2 trường hợp để khách tự đối chiếu.\n\n"
         "--- CHỈ THỊ NỘI BỘ TỪ CÁC NODE ---\n"
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

    print("\n👉 [DEBUG - PROMPT MESSAGES]: ", formatted_messages)
    
    response = llm.invoke(formatted_messages)

    bot_reply = response.content 
    
    current_exchange = f"User: {state.get('user_message')}\nBot: {bot_reply}"

    return {"response_text": response.content, "chat_history": {"messages": [current_exchange]}}