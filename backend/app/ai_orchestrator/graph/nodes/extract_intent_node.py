from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import ContextTag
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """Bạn là AI chuyên bóc tách Ý định (Intent) và Thực thể (Entity) cho hệ thống Đặt vé máy bay.
Thời gian hiện tại: {current_time}

LỊCH SỬ TRÒ CHUYỆN (LƯU Ý: Dùng lịch sử để hiểu ngữ cảnh cho Ý ĐỊNH, nhưng TUYỆT ĐỐI KHÔNG dùng lịch sử để điền tự động THỰC THỂ):
{chat_history}

--- 1. PHÂN LOẠI Ý ĐỊNH (INTENT) ---
Dựa vào CÂU NÓI MỚI NHẤT và LỊCH SỬ, hãy chọn 1 ý định chính xác nhất:

* NHÓM TÌM VÉ (SEARCH_FLIGHT):
  - CHỈ CHỌN intent này khi khách hàng cung cấp HOẶC thay đổi các thông số CỐT LÕI tạo nên chuyến đi: Điểm đi (origin), Điểm đến (destination), Ngày đi/về (date), Số lượng người (adults/children/infants).
  - VD: "Tìm vé đi HN", "Đổi sang ngày mai", "Đi 2 người lớn".
  - LƯU Ý: Kể cả khi khách đang ở bước lọc, nhưng nếu họ ĐỔI NGÀY hoặc ĐỔI ĐIỂM ĐẾN, bắt buộc phải trả về 'search_flight'.
  - XỬ LÝ CHÀO HỎI: Nếu khách CHỈ chào hỏi cơ bản (VD: "Alo", "Xin chào"), hãy phân loại vào 'search_flight' để hệ thống tự động chào lại.

* NHÓM THAO TÁC (FILTER_SORT_FLIGHTS):
  - CHỈ CHỌN intent này khi hành trình (Điểm đi/đến/ngày) KHÔNG ĐỔI, và khách CHỈ MUỐN THU HẸP danh sách vé bằng các tiêu chí: Hãng bay, Khung giờ, Mức giá, Sắp xếp.
  - VD: "Chỉ bay Vietjet", "Có chuyến nào buổi sáng không?", "Lọc vé rẻ nhất".
  - LƯU Ý SINH TỬ: Nếu kết quả tìm kiếm trước đó là RỖNG (0 vé), nhưng câu nói của khách VẪN MANG Ý NGHĨA LỌC (VD: "Tìm thử chuyến đêm xem", "Xem Vietjet có ko"), bạn VẪN PHẢI TRẢ VỀ 'filter_sort_flights'. Tuyệt đối không tự ý đổi sang search_flight.

* NHÓM HỎI ĐÁP & KHÁC:
  - 'analyze_flights': So sánh, phân tích ưu/nhược điểm (VD: "Chuyến Vietjet hay delay không?", "So sánh giá 3 hãng").
  - 'promo_search': Hỏi về khuyến mãi, mã giảm giá.
  - 'general_question': Hỏi quy định, giấy tờ, hành lý (VD: "Hành lý bao nhiêu kg?", "Bà bầu bay được không?").
  - 'out_of_scope': Ngoài lề, không liên quan đến hàng không.

--- 2. TRÍCH XUẤT THỰC THỂ (ENTITY EXTRACTION) ---
*QUAN TRỌNG: CHỈ trích xuất dữ liệu từ CÂU NÓI MỚI NHẤT của khách. KHÔNG tái sử dụng dữ liệu từ lịch sử.*

1. TRUNG THỰC: Khách nói gì trích nấy. Không đoán mò. Khách KHÔNG nhắc đến -> Bắt buộc để `null` (Không được tự bịa).
2. MÃ IATA: Chuẩn hóa địa danh thành mã 3 chữ cái (VD: Hà Nội -> HAN, Sài Gòn/TPHCM -> SGN, Đà Nẵng -> DAD).
3. HỦY LỌC: Nếu khách muốn bỏ điều kiện lọc (VD: "Không lọc hãng nữa", "Hãng nào cũng được", "Bỏ lọc giá"), hãy trả về mảng rỗng `[]` (với target_airline) hoặc số `0` (với maxPrice).
4. GẮN MÃ HÃNG: Luôn trích xuất mã hãng bay (VN, VJ, QH) vào trường `target_airline` khi khách có nhắc đến trong bất kỳ tình huống nào.
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
    
    old_prefs = state.get("user_prefs", {}) or {}
    current_prefs = old_prefs.copy()
    
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
                    
                    for k, v in raw_dump.items():
                        if isinstance(v, str) and v.strip().lower() in ["clear", "none"]:
                            clean_params[k] = [] if k in ["target_airline", "excludedAirlines"] else 0
                        else:
                            clean_params[k] = v

            for arr_field in ["target_flight", "target_airline", "excludedAirlines"]:
                if arr_field in clean_params and isinstance(clean_params[arr_field], list):
                    clean_params[arr_field] = [str(t).upper().replace(" ", "") for t in clean_params[arr_field] if t]

            CORE_PARAMS = ["origin", "destination", "departureDate", "returnDate", "is_roundtrip", "adults", "children", "infants", "travel_class"]
            SOFT_PARAMS = ["target_airline", "excludedAirlines", "nonStop", "maxPrice", "start_hour", "end_hour", "criteria", "sort_preference", "target_flight"]
            
            core_changed = []
            soft_changed = []
            
            for param in CORE_PARAMS:
                if param in clean_params and clean_params[param] != old_prefs.get(param):
                    core_changed.append(f"{param}: {clean_params[param]}")

            for param in SOFT_PARAMS:
                if param in clean_params and clean_params[param] != old_prefs.get(param):
                    soft_changed.append(f"{param}: {clean_params[param]}")

            if core_changed:
                change_info = ", ".join(core_changed)
                node_result.append(f"{ContextTag.USER_UPDATE}: Thay đổi CORE Param ({change_info}). Yêu cầu tìm kiếm mới.")
                # for param in SOFT_PARAMS:
                #     if param in current_prefs and current_prefs[param] not in ["CLEAR", "", None]:
                #         if param not in clean_params:
                #             clean_params[param] = "CLEAR"
            elif soft_changed:
                change_info = ", ".join(soft_changed)
                node_result.append(f"{ContextTag.USER_UPDATE}: Thay đổi SOFT Param ({change_info}). Áp dụng lọc cục bộ.")

            current_prefs.update(clean_params)

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: Không thể bóc tách dữ liệu: {e}")
        
    result_dict = {
        "tasks": all_tasks,
        "user_prefs": current_prefs,
        "node_results": node_result
    }

    if core_changed:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW PREFS]: ", current_prefs)
    print("👉 [DEBUG - TASK]: ", [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in all_tasks])
    print("🔹🔹🔹 ------------------------------------")

    return result_dict