import uuid
from app.core.enums import ChatIntent, ChatRole
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.chat_response import ClientAction, ComponentType, ComponentType

class ChatService:
    def __init__(self, 
                 conversation_repo: ConversationRepository, 
                 message_repo: MessageRepository):
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

        bot_content = f"Mock reply to: {user_content}"
        action = None
        intent = ChatIntent.GENERAL_QUESTION
        
        if "book" in user_content.lower() or "vé" in user_content.lower():
            bot_content = "Tôi tìm thấy một số chuyến bay phù hợp."
            intent = ChatIntent.BOOK_TICKET
            
            action = ClientAction(
                type=ComponentType.FLIGHT_LIST,
                payload={
                    "flights": [
                        {"id": "VN123", "price": "1.500.000", "time": "10:00"},
                        {"id": "VJ456", "price": "1.200.000", "time": "14:00"}
                    ]
                }
            )

        bot_msg_id = uuid.uuid4()
        print(f"Generated bot message ID: {bot_msg_id}")
        self.message_repo.create(
            id=bot_msg_id,
            conversation_id=conversation_id,
            role=ChatRole.ASSISTANT,
            content=bot_content
        )
        
        self.conversation_repo.update_timestamp(conversation_id)

        return {
            "conversation_id": conversation_id,
            "message_id": bot_msg_id,
            "reply": bot_content,
            "intent": intent,
            "slots": {},
            "action": action
        }