"""
app/services/chat_service.py
"""
import uuid
import logging
from langchain_core.messages import HumanMessage

import app.ai_orchestrator.graph.flight_graph as _fg
from app.core.enums import ChatRole
from app.repositories.message_repo import MessageRepository
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.chat_response import ClientAction

logger = logging.getLogger(__name__)


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
        logger.info(f"[chat_service] process_message")
        logger.info(f"  conv_id    : {conversation_id}")
        logger.info(f"  user_msg   : {user_message[:100]}")
        logger.info(f"  ui_context : {ui_context}")

        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self.conversation_repo.create(id=conversation_id, title="New Chat")
            logger.info(f"[chat_service] Tạo conversation mới: {conversation_id}")
        else:
            conversation_id = str(conversation_id)
            if not self.conversation_repo.get_by_id(conversation_id):
                self.conversation_repo.create(id=conversation_id, title="New Chat (Auto-created)")
                logger.info(f"[chat_service] Auto-created conversation: {conversation_id}")

        self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.USER,
            content=user_message,
        )

        config = {"configurable": {"thread_id": conversation_id}}

        # Lấy state hiện tại từ graph
        current_state = {}
        try:
            saved = await _fg.flight_graph.aget_state(config)
            if saved and saved.values:
                current_state = saved.values
                logger.info(
                    f"[chat_service] State từ graph — "
                    f"search_id={current_state.get('current_search_id')} | "
                    f"filters={current_state.get('search_filters')}"
                )
            else:
                logger.info("[chat_service] Graph chưa có state (conversation mới)")
        except Exception as e:
            logger.warning(f"[chat_service] Không lấy được state: {e}")

        if ui_context and ui_context.get("active_search_id"):
            new_sid = ui_context["active_search_id"]
            old_sid = current_state.get("current_search_id")
            logger.info(
                f"[chat_service] ui_context inject search_id: {old_sid} → {new_sid}"
            )
            await _fg.flight_graph.aupdate_state(
                config,
                {"current_search_id": new_sid}
            )
            current_state["current_search_id"] = new_sid

        inputs = {"messages": [HumanMessage(content=user_message)]}
        logger.info("[chat_service] Invoke graph...")

        final_state = await _fg.flight_graph.ainvoke(inputs, config=config)

        logger.info(
            f"[chat_service] Graph done — "
            f"search_id={final_state.get('current_search_id')} | "
            f"action={final_state.get('action')}"
        )

        return self._format_and_save(conversation_id, final_state, current_state)

    async def resume_message(
        self,
        conversation_id: str,
        selected_flight_ids: list[str],
    ):
        conversation_id = str(conversation_id)
        logger.info(f"[chat_service] resume_message conv={conversation_id} flights={selected_flight_ids}")

        config = {"configurable": {"thread_id": conversation_id}}

        current_state = {}
        try:
            saved = await _fg.flight_graph.aget_state(config)
            if saved and saved.values:
                current_state = saved.values
                logger.info(f"[chat_service] Resume state — search_id={current_state.get('current_search_id')}")
        except Exception as e:
            logger.warning(f"[chat_service] Không lấy được state khi resume: {e}")

        flight_ids_str = ", ".join(selected_flight_ids)
        user_msg = (
            f"Tôi đã chọn các chuyến bay: {flight_ids_str}. "
            f"Hãy phân tích và so sánh chi tiết giúp mình."
        )

        inputs = {"messages": [HumanMessage(content=user_msg)]}
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
            raw_content = getattr(msg, "content", "")

            parsed_content = ""
            if isinstance(raw_content, str):
                parsed_content = raw_content
            elif isinstance(raw_content, list):
                blocks = []
                for block in raw_content:
                    if isinstance(block, str):
                        blocks.append(block)
                    elif isinstance(block, dict) and "text" in block:
                        blocks.append(str(block["text"]))
                parsed_content = "\n".join(blocks)

            if msg_type == "ai":
                has_tools = bool(getattr(msg, "tool_calls", []))
                
                if parsed_content.strip():
                    bot_content = parsed_content.strip()
                    break
                elif not has_tools:
                    bot_content = parsed_content
                    break

        current_search_id = (
            final_state.get("current_search_id")
            or prev_state.get("current_search_id")
        )
        if current_search_id == "CLEAR":
            current_search_id = None

        action_dict = final_state.get("action")
        sf = dict(
            final_state.get("search_filters") or
            prev_state.get("search_filters") or {}
        )

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

        logger.info(
            f"[chat_service] Lưu response — "
            f"msg_id={saved.id} | search_id={current_search_id} | "
            f"action={action_dict.get('type') if action_dict else None}"
        )
        logger.debug(f"[chat_service] Bot response preview: {bot_content[:100]}...")

        return {
            "conversation_id": conversation_id,
            "message_id":      str(saved.id),
            "role":            saved.role,
            "content":         bot_content,
            "slots":           slots,
            "action":          client_action,
        }