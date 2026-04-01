from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """Bạn là AI chuyên bóc tách Ý định (Intent) và Thực thể (Entity) cho hệ thống Đặt vé máy bay.
Thời gian hiện tại: {current_time}

LỊCH SỬ TRÒ CHUYỆN (LƯU Ý: Dùng lịch sử để hiểu ngữ cảnh cho Ý ĐỊNH, nhưng TUYỆT ĐỐI KHÔNG dùng lịch sử để điền tự động THỰC THỂ):
{chat_history}

--- 1. PHÂN LOẠI Ý ĐỊNH (INTENT) ---
Dựa vào CÂU NÓI MỚI NHẤT và LỊCH SỬ, hãy chọn 1 ý định chính xác nhất:

* NHÓM TÌM VÉ & CẬP NHẬT THÔNG TIN:
  - 'search_flight': Dùng cho MỌI hành động liên quan đến việc thiết lập hoặc thay đổi thông số chuyến bay. Bao gồm:
    + Bắt đầu tìm chuyến bay mới tinh (VD: "Tìm vé đi HN", "Tôi muốn đặt vé máy bay").
    + Bổ sung thông tin khi Bot đang hỏi (VD: "Đi Đà Nẵng", "Ngày mai").
    + Thay đổi, sửa đổi thông số vé đang tìm (VD: "Đổi sang 2 người lớn", "Không đi Huế nữa", "Chốt chuyến này").
    + XỬ LÝ CHÀO HỎI: Nếu khách CHỈ chào hỏi cơ bản (VD: "Alo", "Xin chào"), hãy phân loại vào 'search_flight' để hệ thống tự động chào lại và mồi khách tìm vé. Nếu khách chào kèm yêu cầu, bỏ qua lời chào và phân loại theo yêu cầu chính.

* NHÓM THAO TÁC (Khi đã có danh sách vé):
  - 'filter_sort_flights': Lọc/Sắp xếp danh sách (VD: "Chỉ đi Vietjet", "Vé rẻ nhất", "Giờ sáng").
  - 'analyze_flights': So sánh, phân tích ưu/nhược điểm (VD: "Chuyến Vietjet hay delay không?", "So sánh giá 3 hãng").

* NHÓM HỎI ĐÁP & KHÁC:
  - 'promo_search': Hỏi về khuyến mãi, mã giảm giá.
  - 'general_question': Hỏi quy định, giấy tờ, hành lý (VD: "Hành lý bao nhiêu kg?", "Bà bầu bay được không?").
  - 'out_of_scope': Ngoài lề, không liên quan đến hàng không.

--- 2. TRÍCH XUẤT THỰC THỂ (ENTITY EXTRACTION) ---
*QUAN TRỌNG: CHỈ trích xuất dữ liệu từ CÂU NÓI MỚI NHẤT của khách. KHÔNG tái sử dụng dữ liệu từ lịch sử.*

1. TRUNG THỰC: Khách nói gì trích nấy. Không đoán mò. Khách không nhắc -> Để `null`.
2. MÃ IATA: Chuẩn hóa địa danh thành mã 3 chữ cái (VD: Hà Nội -> HAN, Sài Gòn/TPHCM -> SGN, Đà Nẵng -> DAD).
3. LỌC PHỦ ĐỊNH: Bỏ qua các địa danh mà khách từ chối (VD: "Không đi Huế nữa" -> Huế KHÔNG phải là origin/destination).
4. HỦY LỌC: Nếu khách muốn bỏ điều kiện (VD: "Không lọc hãng nữa"), đưa tên biến đó vào mảng `cleared_filters`.
5. GẮN MÃ HÃNG: Luôn trích xuất mã hãng bay (VN, VJ, QH) vào `target_airline` nếu khách có nhắc đến khi hỏi chính sách (general_question, promo_search, analyze_flights).
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
                key=lambda t: (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) == "out_of_scope"
            )

            valid_intents_for_params = [
                ChatIntent.SEARCH_FLIGHT.value, 
                ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, 
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
                "travelClass", "maxPrice", "start_hour", "end_hour",
                "adults", "children", "infants"
            ]
            
            for param in core_search_params:
                if param in clean_params and clean_params[param] != old_prefs.get(param):
                    changed_details.append(f"{param}: {clean_params[param]}")

            if "target_flight" in clean_params:
                raw_flights = clean_params["target_flight"]
                if isinstance(raw_flights, list):
                    clean_params["target_flight"] = [str(t).upper().replace(" ", "") for t in raw_flights if t]
                    
            if "target_airline" in clean_params:
                raw_airlines = clean_params["target_airline"]
                if isinstance(raw_airlines, list):
                    clean_params["target_airline"] = [str(t).upper().replace(" ", "") for t in raw_airlines if t]

            if changed_details:
                change_info = ", ".join(changed_details)
                node_result.append(f"[HỆ THỐNG] Phát hiện thay đổi tham số ({change_info}). Reset Search ID.")
                
                existing_intents = [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in all_tasks]
                if ChatIntent.SEARCH_FLIGHT.value not in existing_intents:
                    from app.schemas.chat_state import TaskItem # Đảm bảo đã import
                    all_tasks.insert(0, TaskItem(intent=ChatIntent.SEARCH_FLIGHT, parameters=task.parameters))
                    print("👉 [AUTO-INSERT]: Đã chèn thêm task SEARCH_FLIGHT do thông số thay đổi.")

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