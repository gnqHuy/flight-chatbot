from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.state import ChatState
from app.core.constants import ContextTag
from app.core.llm_setup import llm
from app.schemas.chat_state import ExtractionOutput
from app.core.enums import ChatIntent

SYSTEM_PROMPT = """Bạn là AI chuyên bóc tách Ý định (Intent) và Thực thể (Entity) cho hệ thống Đặt vé máy bay.
Thời gian hiện tại: {current_time}

LỊCH SỬ TRÒ CHUYỆN (Dùng để hiểu ngữ cảnh, TUYỆT ĐỐI KHÔNG điền tự động thực thể từ lịch sử nếu câu mới nhất không nhắc đến):
{chat_history}

--- 1. PHÂN LOẠI Ý ĐỊNH (INTENT) ---
Chọn 1 ý định chính xác nhất:
* SEARCH_FLIGHT: Khi khách hàng cung cấp/thay đổi thông số CỐT LÕI (Điểm đi, điểm đến, ngày, số lượng người) hoặc có ý định chào hỏi.
* FILTER_SORT_FLIGHTS: Khi khách chỉ muốn thu hẹp/sắp xếp danh sách (Hãng bay hiển thị, Giờ, Giá).
* ANALYZE_FLIGHTS: Khi khách muốn so sánh chi tiết giữa các chuyến/hãng (VD: "Chuyến VJ hay delay không?", "So sánh giá 2 hãng").
* GENERAL_QUESTION: Hỏi quy định, giấy tờ, hành lý (VD: "Bà bầu bay được không?").
* PROMO_SEARCH: Hỏi mã giảm giá.
* OUT_OF_SCOPE: Ngoài lề.

--- 2. PHÂN LOẠI THỰC THỂ VÀO 2 GIỎ (RẤT QUAN TRỌNG) ---
Bạn phải bỏ đúng thông số vào 2 giỏ `search_filters` hoặc `action_targets` theo quy tắc sau:

GIỎ 1: `search_filters` (DÀI HẠN - BỘ LỌC HIỂN THỊ)
- Chỉ chứa các điều kiện LỌC DANH SÁCH VÉ.
- Nếu khách nói "Mình chỉ thích bay Vietjet" -> Bỏ "VJ" vào `search_filters.preferred_airlines`.

GIỎ 2: `action_targets` (NGẮN HẠN - MỤC TIÊU PHÂN TÍCH/SO SÁNH)
- Chỉ chứa các mã chuyến, mã hãng khi khách muốn HỎI/SO SÁNH (Intent là ANALYZE_FLIGHTS hoặc GENERAL_QUESTION).
- Nếu khách nói "So sánh Vietjet và Bamboo xem hãng nào xách tay rộng hơn" -> Bỏ "VJ", "QH" vào `action_targets.compare_airlines`. Bỏ "xách tay", "chỗ ngồi" vào `analysis_criteria`.

--- 3. QUY TẮC TRÍCH XUẤT CHUNG ---
- Chuẩn hóa địa danh thành mã IATA 3 chữ cái (Hà Nội -> HAN, Sài Gòn -> SGN).
- Khách không nhắc đến -> Bắt buộc để `null`.
- Muốn hủy bộ lọc (VD: "Không lọc hãng nữa") -> Trả về mảng rỗng `[]` hoặc số `0`.
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
    
    old_search_filters = state.get("search_filters", {}) or {}
    new_search_filters = {}
    new_action_targets = {}
    
    history_dict = state.get("chat_history", {"messages": [], "search_ids": []})
    history_list = history_dict.get("messages", [])
    history_str = "\n".join(history_list[-10:]) if history_list else "Chưa có lịch sử trò chuyện."
    
    core_changed = False
    
    try:
        result: ExtractionOutput = extraction_chain.invoke({
            "query": state.get("user_message", ""),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "chat_history": history_str
        })

        if result and result.tasks:
            all_tasks = result.tasks
            all_tasks.sort(key=lambda t: (t.intent.value if hasattr(t.intent, 'value') else str(t.intent)) == "out_of_scope")

            valid_intents = [
                ChatIntent.SEARCH_FLIGHT.value, 
                ChatIntent.FILTER_SORT_FLIGHTS.value,
                ChatIntent.ANALYZE_FLIGHTS.value, 
                ChatIntent.PROMO_SEARCH.value,
                ChatIntent.GENERAL_QUESTION.value
            ]
            
            for task in all_tasks:
                intent_str = task.intent.value if hasattr(task.intent, 'value') else str(task.intent)
                
                if intent_str in valid_intents:
                    if task.search_filters:
                        raw_filters = task.search_filters.model_dump(exclude_none=True)
                        for k, v in raw_filters.items():
                            if isinstance(v, str) and v.strip().lower() in ["clear", "none"]:
                                new_search_filters[k] = [] if "airlines" in k.lower() else 0
                            elif isinstance(v, list):
                                new_search_filters[k] = [str(i).upper().replace(" ", "") for i in v if i]
                            else:
                                new_search_filters[k] = v

                    if task.action_targets:
                        raw_targets = task.action_targets.model_dump(exclude_none=True)
                        for k, v in raw_targets.items():
                            if isinstance(v, list):
                                new_action_targets[k] = [str(i).upper().replace(" ", "") for i in v if i]
                            else:
                                new_action_targets[k] = v

            CORE_FIELDS = ["origin", "destination", "departureDate", "returnDate", "roundTrip", "adults", "children", "infants"]
            
            core_changes_str = []
            filter_changes_str = []
            
            for k, v in new_search_filters.items():
                if v != old_search_filters.get(k):
                    if k in CORE_FIELDS:
                        core_changed = True
                        core_changes_str.append(f"{k}: {v}")
                    else:
                        filter_changes_str.append(f"{k}: {v}")

            if core_changed:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi thông số cốt lõi ({', '.join(core_changes_str)}). Yêu cầu tìm vé mới.")
            elif filter_changes_str:
                node_result.append(f"{ContextTag.USER_UPDATE}: Đổi bộ lọc hiển thị ({', '.join(filter_changes_str)}).")
                
            if new_action_targets:
                targets_info = []
                if new_action_targets.get("compare_airlines"): targets_info.append(f"Hãng: {new_action_targets['compare_airlines']}")
                if new_action_targets.get("compare_flights"): targets_info.append(f"Chuyến: {new_action_targets['compare_flights']}")
                if targets_info:
                    node_result.append(f"{ContextTag.USER_UPDATE}: Yêu cầu thao tác trên mục tiêu: {', '.join(targets_info)}.")

    except Exception as e:
        print(f"❌ [LỖI EXTRACT INTENT]: Không thể bóc tách dữ liệu: {e}")
        
    result_dict = {
        "tasks": all_tasks,
        "search_filters": new_search_filters,
        "action_targets": new_action_targets,
        "node_results": node_result
    }

    if core_changed:
        result_dict["current_search_id"] = "CLEAR"

    print("👉 [DEBUG - NEW FILTERS]: ", new_search_filters)
    print("👉 [DEBUG - NEW TARGETS]: ", new_action_targets)
    print("👉 [DEBUG - TASK]: ", [t.intent.value if hasattr(t.intent, 'value') else str(t.intent) for t in all_tasks])
    print("🔹🔹🔹 ------------------------------------")

    return result_dict