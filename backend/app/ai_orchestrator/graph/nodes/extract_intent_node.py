from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """Bạn là AI trích xuất thông tin đặt vé máy bay.
Thời gian hiện tại: {current_time}

LỊCH SỬ TRÒ CHUYỆN GẦN ĐÂY, HÃY SỬ DỤNG ĐỂ THAM KHẢO VÀ QUYẾT ĐỊNH INTENTS, NHƯNG KHÔNG ĐƯỢC LẤY THAM SỐ TỪ LỊCH SỬ NẾU KHÁCH KHÔNG NHẮC TỚI TRONG TIN NHẮN MỚI.:
{chat_history}

NHIỆM VỤ: Phân loại tin nhắn của người dùng vào một trong các Ý định (Intents) sau:
1. 'search_flight': Tìm kiếm chuyến bay, kiểm tra giá vé.
2. 'filter_sort_flights': Lọc/sắp xếp danh sách chuyến bay đã tìm kiếm dựa trên các tiêu chí như giá, giờ bay, hãng hàng không, v.v. (Chỉ dùng khi khách đã có một danh sách chuyến bay hiện tại và muốn thao tác trên đó).
3. 'analyze_flights': So sánh giá cả, thời gian bay, hoặc các hãng hàng không giữa các lựa chọn vé khác nhau.
4. 'provide_info': Khi câu hỏi trước đó hỏi thêm về thông tin cho khách hàng.
5. 'greeting': Chào hỏi cơ bản, cảm ơn, tạm biệt (VD: Xin chào, cảm ơn em, bye).
6. 'general_question': Các câu hỏi chung về chính sách chuyến bay, hành lý, giấy tờ, phụ nữ mang thai, hoặc quy định của hãng (Dùng intent này cho tác vụ tra cứu RAG).
7. 'out_of_scope': CHỈ DÙNG CHO các chủ đề ngoài lề, không liên quan đến hàng không.

NGUYÊN TẮC TRÍCH XUẤT (CỰC KỲ QUAN TRỌNG):
1. TRUNG THỰC TUYỆT ĐỐI: CHỈ trích xuất những thông tin CÓ XUẤT HIỆN trong câu nói của khách. KHÔNG ĐƯỢC tự động điền hay mặc định bất kỳ biến nào. Nếu khách không nhắc tới, để trống.
2. MÃ IATA: Mọi địa danh phải được quy đổi ra mã IATA 3 chữ cái (VD: Hà Nội -> HAN, TPHCM/Sài Gòn -> SGN, Đà Nẵng -> DAD). Không lưu tên tiếng Việt.
3. HỦY BỘ LỌC: Nếu khách yêu cầu hủy/bỏ qua một bộ lọc (VD: "không đi khứ hồi nữa", "không lọc giờ nữa"), KHÔNG điền vào biến đó, mà hãy thêm tên biến đó vào mảng `cleared_filters`.
"""

prompt_template = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{query}")
])

extraction_chain = prompt_template | llm.with_structured_output(ExtractionOutput)

def extract_intent_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE EXTRACT INTENT ---")
    
    if state.get("tasks"):
        return {} 

    all_tasks = []
    node_result = [] 
    current_prefs = {}
    changed_details = []
    old_prefs = state.get("user_prefs", {}) 
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "No previous history."
    
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

            flight_data_intents = [
                ChatIntent.SEARCH_FLIGHT.value, 
                ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, 
                ChatIntent.PROVIDE_INFO.value
            ]
            
            clean_params = {}
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                
                if intent_str in flight_data_intents and task.parameters:
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
                node_result.append(f"[Cập nhật]: {change_info}")

            if "analysis_targets" in clean_params:
                raw_targets = clean_params["analysis_targets"]
                if isinstance(raw_targets, list):
                    clean_params["analysis_targets"] = [str(t).upper().replace(" ", "") for t in raw_targets if t]

            current_prefs.update(clean_params)

    except Exception as e:
        print(f"Lỗi extract intent: {e}")
        
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