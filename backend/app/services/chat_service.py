import uuid
from fastapi.concurrency import run_in_threadpool
from app.ai_orchestrator.graph.flight_graph import flight_graph 
from app.core.enums import ChatRole
from app.repositories.message_repo import MessageRepository
from app.repositories.conversation_repo import ConversationRepository
from app.schemas.chat_response import ClientAction

class ChatService:
    def __init__(self, conversation_repo: ConversationRepository, message_repo: MessageRepository):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo

    async def process_message(self, conversation_id: str | None, user_content: str):
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            self.conversation_repo.create(id=conversation_id, title="New Chat")
        else:
            existing_conversation = self.conversation_repo.get_by_id(conversation_id)
            if not existing_conversation:
                self.conversation_repo.create(id=conversation_id, title="New Chat (Auto-created)")

        self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.USER,
            content=user_content
        )

        config = {"configurable": {"thread_id": conversation_id}}
        inputs = {
            "user_message": user_content,
            "node_results": ["CLEAR"],  
            "action": None,
            "error_msg": None,
            "tasks": []
        }
        
        final_state = await run_in_threadpool(flight_graph.invoke, inputs, config=config)
        
        bot_message_content = final_state.get("response_text")
        if not bot_message_content:
             bot_message_content = "Xin lỗi, tôi gặp chút trục trặc khi xử lý yêu cầu."

        new_history = [
            f"User: {user_content}",
            f"Bot: {bot_message_content}"
        ]

        await run_in_threadpool(flight_graph.update_state, config, {"chat_history": new_history})

        user_prefs = final_state.get("user_prefs", {})

        extracted_slots = {
            "origin": user_prefs.get("origin"),
            "destination": user_prefs.get("destination"),
            "departureDate": user_prefs.get("departureDate"),
            "current_search_id": user_prefs.get("current_search_id")
        }

        tasks = final_state.get("tasks", [])
        all_intents = [
            task.intent.value if hasattr(task.intent, 'value') else str(task.intent) 
            for task in tasks
        ]

        action_dict = final_state.get("action")
        error_msg = final_state.get("error_msg")

        if error_msg and not action_dict:
            action_dict = {
                "type": "error",
                "payload": {"msg": error_msg}
            }

        client_action = None
        if action_dict:
            client_action = ClientAction(
                type=action_dict.get("type", "unknown"),
                payload=action_dict.get("payload", {})
            )

        saved_bot_msg = self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.ASSISTANT,
            content=bot_message_content,
            action=action_dict,
        )

        return {
            "conversation_id": conversation_id,
            "message_id": str(saved_bot_msg.id),
            "role": saved_bot_msg.role,
            "content": bot_message_content,
            "intents": all_intents,
            "slots": extracted_slots,
            "action": client_action
        }