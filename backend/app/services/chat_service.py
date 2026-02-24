import uuid
from langchain_core.messages import HumanMessage
from fastapi.concurrency import run_in_threadpool
from app.ai.graph.flight_graph import build_flight_graph
from app.core.enums import ChatIntent, ChatRole
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.chat_response import ClientAction

bot_app = build_flight_graph()

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
            "user_message": user_content
        }

        final_state = await run_in_threadpool(bot_app.invoke, inputs, config=config)

        print("--- FINAL STATE ---", final_state)

        bot_message_content = final_state.get("response_text")
        if not bot_message_content:
             bot_message_content = "Xin lỗi, tôi gặp chút trục trặc khi xử lý yêu cầu."

        extracted_slots = {
            "origin": final_state.get("origin"),
            "destination": final_state.get("destination"),
            "departureDate ": final_state.get("departureDate") or final_state.get("departureDate"),
        }

        action_type = "none" 
        action_payload = None

        if final_state.get("flight_offers") or final_state.get("search_results"):
            action_type = "flight_list"
            action_payload = final_state.get("flight_offers") or final_state.get("search_results")

        formatted_payload = {"flights": action_payload} if action_payload else {}

        client_action = ClientAction(
            type=action_type, 
            payload=formatted_payload
        )

        if final_state.get("search_results"):
            client_action = ClientAction(type="search_flight", payload=final_state.get("search_results"))
            
        elif final_state.get("error_msg"):
            client_action = ClientAction(type="error", payload={"msg": final_state.get("error_msg")})

        saved_bot_msg = self.message_repo.create(
            conversation_id=conversation_id,
            role=ChatRole.ASSISTANT,
            content=bot_message_content,
        )

        return {
            "conversation_id": conversation_id,
            "message_id": saved_bot_msg.id,
            "role": saved_bot_msg.role,
            "content": bot_message_content,
            "intent": final_state.get("intent", "unknown"),
            "slots": extracted_slots,
            "action": client_action
        }