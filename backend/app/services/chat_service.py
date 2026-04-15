import uuid
import app.ai_orchestrator.graph.flight_graph as _fg
from app.core.enums import ChatRole
from app.repositories.message_repo import MessageRepository
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.chat_response import ClientAction
from app.schemas.chat_state import Task
from app.core.enums import ChatIntent


class ChatService:
    def __init__(self, conversation_repo: ConversationRepository, message_repo: MessageRepository):
        self.conversation_repo = conversation_repo
        self.message_repo      = message_repo

    async def process_message(self, conversation_id: uuid.UUID | None, user_message: str, ui_context: dict | None = None):
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self.conversation_repo.create(id=conversation_id, title="New Chat")
        else:
            if not self.conversation_repo.get_by_id(conversation_id):
                self.conversation_repo.create(id=conversation_id, title="New Chat (Auto-created)")

        self.message_repo.create(conversation_id=conversation_id, role=ChatRole.USER, content=user_message)

        graph_config = {"configurable": {"thread_id": conversation_id}}
        inputs = {
            "user_message":   user_message,
            "node_results":   ["CLEAR"],
            "action":         None,
            "error_msg":      None,
            "tasks":          [],
            "search_filters": {},
            "action_targets": {},
            "current_search_id": None,
        }
        if ui_context and ui_context.get("active_search_id"):
            inputs["current_search_id"] = ui_context["active_search_id"]

        final_state = await _fg.flight_graph.ainvoke(inputs, config=graph_config)
        return self._format_and_save_response(conversation_id, final_state)

    async def resume_message(self, conversation_id: str, selected_flight_ids: list[str]):
        graph_config = {"configurable": {"thread_id": conversation_id}}

        fake_task = Task(intent=ChatIntent.ANALYZE_FLIGHTS)

        inputs = {
            "user_message":   "Tôi đã tick chọn các chuyến bay trên màn hình.",
            "action_targets": {"compare_flights": selected_flight_ids},
            "tasks":          [fake_task],
            "action":         None,
            "node_results":   ["CLEAR"],
        }

        final_state = await _fg.flight_graph.ainvoke(inputs, config=graph_config)
        return self._format_and_save_response(conversation_id, final_state)

    def _format_and_save_response(self, conversation_id: str, final_state: dict):
        content = final_state.get("response_text") or "Xin lỗi, tôi gặp chút trục trặc khi xử lý yêu cầu."
        sf = final_state.get("search_filters", {})
        slots = {
            "origin":            sf.get("origin"),
            "destination":       sf.get("destination"),
            "departureDate":     sf.get("departureDate"),
            "current_search_id": final_state.get("current_search_id"),
        }
        action_dict = final_state.get("action")
        error_msg   = final_state.get("error_msg")
        if error_msg and not action_dict:
            action_dict = {"type": "error", "payload": {"msg": error_msg}}

        client_action = None
        if action_dict:
            client_action = ClientAction(
                type=action_dict.get("type", "unknown"),
                payload=action_dict.get("payload", {}),
            )

        saved = self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.ASSISTANT,
            content=content,
            action=action_dict,
        )
        return {
            "conversation_id": conversation_id,
            "message_id":      str(saved.id),
            "role":            saved.role,
            "content":         content,
            "slots":           slots,
            "action":          client_action,
        }