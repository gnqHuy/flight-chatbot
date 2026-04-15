import asyncio
from langchain_core.prompts import ChatPromptTemplate
from app.ai_orchestrator.graph.prompts.final_prompt import FINAL_NODE_SYSTEM_PROMPT
from app.ai_orchestrator.graph.state import ChatState
from app.core.llm_setup import llm
from app.core.constants import CURRENT_TIME_STR, MAX_HISTORY_TURNS, ContextTag


async def final_response_node(state: ChatState):
    print("\n🔹🔹🔹 --- VÀO NODE TỔNG HỢP CÂU TRẢ LỜI ---")

    lang              = state.get("language") or "vi"
    user_message      = state.get("user_message", "")
    search_filters    = state.get("search_filters", {})
    node_results      = state.get("node_results", [])
    action            = state.get("action")
    error_msg         = state.get("error_msg")
    current_search_id = state.get("current_search_id")

    history_dict = state.get("chat_history", {})
    history_list = history_dict.get("messages", []) if isinstance(history_dict, dict) else []
    history_str  = "\n".join(history_list[-MAX_HISTORY_TURNS:]) if history_list else "Chưa có lịch sử."

    system_instructions = []
    if error_msg:
        system_instructions.append(f"{ContextTag.SYS_ERROR}: {error_msg}. Hãy xin lỗi và giải thích ngắn gọn.")

    if not node_results and not action and not error_msg:
        system_instructions.append(
            "[HỆ THỐNG]: Khách đang chào hỏi hoặc hỏi ngoài lề. Hãy giao tiếp lịch sự và hướng về dịch vụ vé máy bay."
        )
    else:
        system_instructions.extend([r for r in node_results if r])

    combined_context = "\n\n".join(system_instructions)

    if ContextTag.FLIGHT_FOUND in combined_context and current_search_id:
        loop = asyncio.get_running_loop()
        from app.utils.promo_injector import check_and_inject_promos
        promo_ctx = await loop.run_in_executor(None, check_and_inject_promos, current_search_id)
        if promo_ctx:
            combined_context += f"\n\n{promo_ctx}"

    known_info = {k: v for k, v in search_filters.items() if v and k != "current_search_id"}

    prompt = ChatPromptTemplate.from_messages([
        ("system", FINAL_NODE_SYSTEM_PROMPT),
        ("human", "{question}"),
    ])
    formatted_messages = prompt.format_messages(
        context=combined_context, history=history_str,
        known_info=known_info, question=user_message,
        lang=lang, current_time=CURRENT_TIME_STR,
    )

    print(f"\n👉 [CONTEXT]: {combined_context}")

    response  = await llm.ainvoke(formatted_messages)
    bot_reply = response.content

    print("\n🔹🔹🔹 ------------------------------------")
    return {
        "response_text": bot_reply,
        "chat_history":  {"messages": [f"User: {user_message}\nBot: {bot_reply}"]},
    }