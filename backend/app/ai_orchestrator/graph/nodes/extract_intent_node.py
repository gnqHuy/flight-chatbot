from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """Bạn là AI chuyên trích xuất thông tin đặt vé máy bay.
Thời gian hiện tại: {current_time}

LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY (Sử dụng để tham khảo ngữ cảnh và quyết định Ý định, nhưng TUYỆT ĐỐI KHÔNG tự động lấy tham số từ lịch sử nạp vào nếu khách không nhắc lại hoặc xác nhận trong tin nhắn mới):
{chat_history}

NHIỆM VỤ: Phân loại tin nhắn của người dùng vào một trong các Ý định (Intents) sau:
1. 'search_flight': Tìm kiếm chuyến bay, kiểm tra giá vé.
2. 'filter_sort_flights': Lọc/sắp xếp danh sách chuyến bay đã tìm kiếm dựa trên các tiêu chí (Chỉ dùng khi khách đã có danh sách vé và muốn thao tác trên đó).
3. 'analyze_flights': So sánh giá cả, thời gian bay, hoặc phân tích chi tiết giữa các chuyến bay/hãng bay.
4. 'provide_info': Cung cấp thêm thông tin (VD: khách trả lời câu hỏi của bot về ngày đi, điểm đến).
5. 'greeting': Chào hỏi cơ bản, cảm ơn, tạm biệt (VD: Xin chào, cảm ơn em, bye).
6. 'general_question': Các câu hỏi chung về chính sách chuyến bay, hành lý, giấy tờ, phụ nữ mang thai, hoặc quy định của hãng (Kích hoạt luồng tra cứu RAG).
7. 'out_of_scope': CHỈ DÙNG CHO các chủ đề ngoài lề, hoàn toàn không liên quan đến hàng không.
8. 'promo_search': Tìm kiếm các chương trình khuyến mãi, ưu đãi đặc biệt, mã giảm giá.

NGUYÊN TẮC TRÍCH XUẤT (CỰC KỲ QUAN TRỌNG):
1. TRUNG THỰC TUYỆT ĐỐI: CHỈ trích xuất những thông tin CÓ XUẤT HIỆN trong câu nói hiện tại của khách. KHÔNG ĐƯỢC tự động điền hay mặc định bất kỳ biến nào. Nếu khách không nhắc tới, hãy để trống (null).
2. MÃ IATA: Mọi địa danh phải được quy đổi ra mã IATA 3 chữ cái (VD: Hà Nội -> HAN, TPHCM/Sài Gòn -> SGN, Đà Nẵng -> DAD). Không lưu tên tiếng Việt.
3. HỦY BỘ LỌC: Nếu khách yêu cầu hủy/bỏ qua một bộ lọc (VD: "không đi khứ hồi nữa", "không lọc giờ nữa"), KHÔNG điền vào biến đó, mà hãy ném tên biến đó vào mảng `cleared_filters`.
4. ÉP BUỘC RAG: Nếu Ý định là 'general_question', 'promo_search' hoặc 'analyze_flights' VÀ khách có nhắc đến tên hãng bay (VD: Vietjet, Vietnam Airlines, Bamboo...), BẮT BUỘC phải tạo object `parameters` và điền mã hãng vào trường `target_airline` (VD: ['VJ'], ['VN'], ['QH']). TUYỆT ĐỐI KHÔNG để parameters là null nếu có nhắc tên hãng.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO TRẠM NHẬN DIỆN Ý ĐỊNH (EXTRACT INTENT) ---")
    
    if state.get("tasks"):
        return {} 

    all_tasks = []
    node_result = [] 
    current_prefs = {}
    changed_details = []
    old_prefs = state.get("user_prefs", {}) 
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "Chưa có lịch sử trò chuyện."
    
    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": state.get("user_message", ""),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "chat_history": history_str
        })

        if result and result.tasks:
            all_tasks = result.tasks
            all_tasks.sort(
                key=lambda t: (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) in ["greeting", "out_of_scope"]
            )

            valid_intents_for_params = [
                ChatIntent.SEARCH_FLIGHT.value, 
                ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, 
                ChatIntent.PROVIDE_INFO.value,
                ChatIntent.PROMO_SEARCH.value,
                ChatIntent.GENERAL_QUESTION.value
            ]
            
            clean_params = {}
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                
                if intent_str in valid_intents_for_params and task.parameters:
                    raw_dump = task.parameters.model_dump(exclude_none=True)
                    
                    filters_to_clear = raw_dump.get("cleared_filters", [])
                    if filters_to_clear:
                        for field in filters_to_clear:
                            clean_params[field] = "CLEAR"
                        clean_params["cleared_filters"] = "CLEAR"
                            
                    for k, v in raw_dump.items():
                        if k == "cleared_filters": continue
                        if isinstance(v, str) and v.strip().lower() in ["", "null", "none", "clear"]: continue
                            
                        if v == "CLEAR" or v == ["CLEAR"]:
                            clean_params[k] = v
                        elif v is not None and v != []:
                            clean_params[k] = v

            core_search_params = [
                "origin", "destination", "departureDate", "returnDate", 
                "includedAirlines", "excludedAirlines", "nonStop", 
                "travelClass", "maxPrice", "start_hour", "end_hour"
            ]
            
            for param in core_search_params:
                if param in clean_params and clean_params[param] != old_prefs.get(param):
                    changed_details.append(f"{param}: {clean_params[param]}")

            if changed_details:
                change_info = ", ".join(changed_details)
                node_result.append(f"[CẬP NHẬT THÔNG TIN] Khách hàng vừa cung cấp hoặc thay đổi tham số: {change_info}")

            if "target_flight" in clean_params:
                raw_flights = clean_params["target_flight"]
                if isinstance(raw_flights, list):
                    clean_params["target_flight"] = [str(t).upper().replace(" ", "") for t in raw_flights if t]
                    
            if "target_airline" in clean_params:
                raw_airlines = clean_params["target_airline"]
                if isinstance(raw_airlines, list):
                    clean_params["target_airline"] = [str(t).upper().replace(" ", "") for t in raw_airlines if t]

            current_prefs.update(clean_params)

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: Không thể bóc tách dữ liệu: {e}")
        
    result_dict = {
        "tasks": all_tasks,
        "user_prefs": current_prefs,
        "node_results": node_result
    }

    if changed_details:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW PREFS]: ", current_prefs)
    print("👉 [DEBUG - TASK]: ", all_tasks)
    print("🔹🔹🔹 ------------------------------------")

    return result_dict