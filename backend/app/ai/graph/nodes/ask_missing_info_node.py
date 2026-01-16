from app.ai.graph.state import ChatState

def ask_missing_info_node(state: ChatState) -> ChatState:
    if not state.origin:
        msg = "Bạn muốn bay từ đâu?"
    elif not state.destination:
        msg = "Bạn muốn bay đến đâu?"
    elif not state.departureDate:
        msg = "Bạn muốn bay ngày nào?"
    else:
        msg = "Bạn vui lòng cung cấp thêm thông tin."

    return state.copy(update={"response_text": msg})
