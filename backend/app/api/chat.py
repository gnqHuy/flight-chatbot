# from fastapi import APIRouter
# from pydantic import BaseModel

# from app.ai.llm.intent_extractor import extract_intent_and_slots

# router = APIRouter()


# class ChatRequest(BaseModel):
#     message: str


# class ChatResponse(BaseModel):
#     reply: str
#     intent: str
#     slots: dict


# @router.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     result = extract_intent_and_slots(req.message)

#     return ChatResponse(
#         reply=f"Tôi đã hiểu yêu cầu của bạn: {result.intent}",
#         intent=result.intent,
#         slots={
#             "origin": result.origin,
#             "destination": result.destination,
#             "departureDate": result.departureDate,
#             "returnDate": result.returnDate,
#             "adults": result.adults,
#         },
#     )
