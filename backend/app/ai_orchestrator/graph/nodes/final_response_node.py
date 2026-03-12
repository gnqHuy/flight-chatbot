from datetime import datetime
from app.ai_orchestrator.graph.state import ChatState
from app.ai_orchestrator.llm.llm import llm
from langchain_core.prompts import ChatPromptTemplate

def final_response_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE TỔNG HỢP CÂU TRẢ LỜI ---")
    
    lang = state.get("language") or "vi"
    user_message = state.get("user_message", "")
    user_prefs = state.get("user_prefs", {})
    node_results = state.get("node_results", [])
    action = state.get("action")
    error_msg = state.get("error_msg")
    
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
            
            if "[Cập nhật thông tin]" in result:
                system_instructions.append(f"[CẬP NHẬT TỪ KHÁCH HÀNG]: {result}")
            elif "[SLOT_FILLING_REQUIRED]" in result or "[INVALID" in result:
                system_instructions.append(f"[YÊU CẦU THÔNG TIN]: {result}")
            elif "NOT_FOUND" in result or "ERROR" in result:
                system_instructions.append(f"[TRỤC TRẶC TÌM KIẾM/PHÂN TÍCH]: {result}")
            elif "[BÁO CÁO PHÂN TÍCH" in result or "SO SÁNH" in result:
                system_instructions.append(f"[DỮ LIỆU SO SÁNH]: \n{result}")
            elif "THÔNG TIN QUY ĐỊNH" in result:
                system_instructions.append(f"[KIẾN THỨC NGHIỆP VỤ (RAG)]: \n{result}")
            elif "FOUND" in result: 
                system_instructions.append(f"[THÔNG TIN CHUYẾN BAY]: {result}")
            else:
                system_instructions.append(f"[THÔNG TIN BỔ SUNG]: {result}")

    combined_context = "\n\n".join(system_instructions)

    known_info = {k: v for k, v in user_prefs.items() if v and v != "CLEAR" and k != "current_search_id"}
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", 
         "Bạn là nhân viên tư vấn vé máy bay xuất sắc và tận tâm. Nhiệm vụ của bạn là tổng hợp dữ liệu từ [Hệ thống] và phản hồi khách hàng bằng ngôn ngữ {lang}.\n\n"
         "--- NGỮ CẢNH BẠN ĐANG CÓ (USER PREFERENCES) ---\n"
         "{known_info}\n\n"
         "--- QUY TẮC GIAO TIẾP SỐNG CÒN ---\n"
         "1. XÁC NHẬN THÔNG TIN: Dựa vào [NGỮ CẢNH], hãy lồng ghép khéo léo các thông tin đã biết (điểm đi, điểm đến, ngày...) vào câu trả lời để khách yên tâm.\n"
         "2. XỬ LÝ SỰ THAY ĐỔI: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [CẬP NHẬT TỪ KHÁCH HÀNG], bạn PHẢI chủ động thông báo bạn đã tìm kiếm lại/lọc lại dữ liệu theo tham số mới đó (VD: 'Dạ em đã cập nhật danh sách vé sang các chuyến bay buổi sáng theo ý chị rồi ạ...').\n"
         "3. GỢI Ý MỞ RỘNG TỰ NHIÊN (OPTIONAL): Đừng chỉ hỏi các thông tin bắt buộc. Dựa vào những gì khách CHƯA cung cấp, hãy khéo léo chọn 1-2 tiêu chí trong danh sách sau để gợi ý (TUYỆT ĐỐI không hỏi dồn dập như trả bài):\n"
         "   - Ngày về (để mua vé khứ hồi).\n"
         "   - Số lượng người đi cùng (người lớn, trẻ em).\n"
         "   - Khung giờ bay mong muốn (sáng, trưa, chiều, tối hoặc giờ cụ thể).\n"
         "   - Hãng hàng không yêu thích hoặc hãng muốn tránh.\n"
         "   - Ưu tiên bay thẳng (không điểm dừng).\n"
         "   - Hạng ghế (Thương gia, Phổ thông, ...).\n"
         "   - Ngân sách / Mức giá tối đa mong muốn.\n"
         "   - Tiêu chí ưu tiên khi so sánh (muốn tìm chuyến rẻ nhất, bay nhanh nhất, hay cất cánh sớm nhất).\n"
         "4. ĐÓNG VAI HOÀN HẢO: Dịch các trường dữ liệu thô sang lời nói tự nhiên. Tuyệt đối KHÔNG lộ các thẻ mã lệnh hệ thống (VD: [HÀNH ĐỘNG CỦA UI], [CẬP NHẬT...]) ra ngoài.\n"
         "5. MỜI XEM MÀN HÌNH: Nếu trong [CHỈ THỊ NỘI BỘ] có thẻ [THÔNG TIN CHUYẾN BAY], bạn BẮT BUỘC phải thêm 1 câu mời khách xem danh sách vé/kết quả đang hiển thị trên giao diện.\n\n"
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

    return {"response_text": response.content}