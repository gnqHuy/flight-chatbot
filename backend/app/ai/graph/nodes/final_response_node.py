from app.ai.graph.state import ChatState

def final_response_node(state: ChatState) -> ChatState:
    if state.response_text:
        return state

    return state.copy(update={
        "response_text": "Mình có thể giúp bạn tìm chuyến bay ✈️"
    })
