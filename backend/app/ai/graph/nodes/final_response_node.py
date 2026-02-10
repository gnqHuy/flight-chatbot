from app.ai.graph.state import ChatState

def final_response_node(state: ChatState):
    print("\n--- NODE: final response ---", state, "\n")   

    missing_slots = []
    if not state.origin:
        missing_slots.append("điểm đi")
    if not state.destination:
        missing_slots.append("điểm đến")
    if not state.departureDate:
        missing_slots.append("ngày đi")

    if missing_slots:
        missing_str = ", ".join(missing_slots)
        return {
            "response_text": f"Bạn vui lòng cung cấp thêm thông tin về: {missing_str} để mình tìm vé nhé."
        }

    return {
        "response_text": f"Tuyệt vời! Mình đã có đủ thông tin. Đang tìm chuyến bay từ {state.origin} đi {state.destination} vào ngày {state.departureDate}. Bạn đợi một chút nhé..."
    }