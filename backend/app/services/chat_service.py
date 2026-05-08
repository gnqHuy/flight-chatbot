# app/services/chat_service.py
"""
app/services/chat_service.py
"""
import uuid
from langchain_core.messages import HumanMessage

import app.ai_orchestrator.graph.flight_graph as _fg
from app.core.enums import ChatRole
from app.repositories.message_repo import MessageRepository
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.chat_response import ClientAction


class ChatService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        message_repo: MessageRepository,
    ):
        self.conversation_repo = conversation_repo
        self.message_repo      = message_repo

    async def process_message(
        self,
        conversation_id: uuid.UUID | str | None,
        user_message: str,
        ui_context: dict | None = None,
    ):
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self.conversation_repo.create(id=conversation_id, title="New Chat")
        else:
            conversation_id = str(conversation_id)
            if not self.conversation_repo.get_by_id(conversation_id):
                self.conversation_repo.create(
                    id=conversation_id, title="New Chat (Auto-created)"
                )

        self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.USER,
            content=user_message,
        )

        config = {"configurable": {"thread_id": conversation_id}}

        current_state = {}
        try:
            saved = await _fg.flight_graph.aget_state(config)
            if saved and saved.values:
                current_state = saved.values
        except Exception:
            pass

        if ui_context and ui_context.get("active_search_id"):
            current_state["current_search_id"] = ui_context["active_search_id"]
            await _fg.flight_graph.aupdate_state(config, current_state)

        inputs = {
            "messages": [
                HumanMessage(content=user_message),
            ]
        }

        final_state = await _fg.flight_graph.ainvoke(inputs, config=config)
        return self._format_and_save(conversation_id, final_state, current_state)

    async def resume_message(
        self,
        conversation_id: str,
        selected_flight_ids: list[str],
    ):
        """Khách tick chọn chuyến bay trên UI → tiếp tục analyze."""
        conversation_id = str(conversation_id)
        config = {"configurable": {"thread_id": conversation_id}}

        current_state = {}
        try:
            saved = await _fg.flight_graph.aget_state(config)
            if saved and saved.values:
                current_state = saved.values
        except Exception:
            pass

        flight_ids_str = ", ".join(selected_flight_ids)
        user_msg = (
            f"Tôi đã chọn các chuyến bay: {flight_ids_str}. "
            f"Hãy phân tích và so sánh chi tiết giúp mình."
        )

        inputs = {
            "messages": [
                HumanMessage(content=user_msg),
            ]
        }

        final_state = await _fg.flight_graph.ainvoke(inputs, config=config)
        return self._format_and_save(conversation_id, final_state, current_state)

    def _format_and_save(
        self,
        conversation_id: str,
        final_state: dict,
        prev_state: dict,
    ):
        messages = final_state.get("messages", [])

        bot_content = "Xin lỗi, tôi gặp chút trục trặc khi xử lý yêu cầu."
        for msg in reversed(messages):
            msg_type = getattr(msg, "type", "")
            content  = getattr(msg, "content", "")
            if msg_type == "ai" and isinstance(content, str) and content.strip():
                if not (hasattr(msg, "tool_calls") and msg.tool_calls and not content.strip()):
                    bot_content = content
                    break

        current_search_id = (
            final_state.get("current_search_id")
            or prev_state.get("current_search_id")
        )
        if current_search_id == "CLEAR":
            current_search_id = None

        action_dict = final_state.get("action")
        sf          = dict(final_state.get("search_filters") or
                           prev_state.get("search_filters") or {})

        slots = {
            "origin":            sf.get("origin"),
            "destination":       sf.get("destination"),
            "departureDate":     sf.get("departureDate"),
            "current_search_id": current_search_id,
        }

        client_action = None
        if action_dict:
            client_action = ClientAction(
                type=action_dict.get("type", "unknown"),
                payload=action_dict.get("payload", {}),
            )

        saved = self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.ASSISTANT,
            content=bot_content,
            action=action_dict,
        )

        return {
            "conversation_id": conversation_id,
            "message_id":      str(saved.id),
            "role":            saved.role,
            "content":         bot_content,
            "slots":           slots,
            "action":          client_action,
        }