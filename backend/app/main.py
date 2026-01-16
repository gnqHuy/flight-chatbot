from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.ai.graph.flight_graph import flight_graph
from app.ai.graph.state import ChatState

from app.api import conversations, conversations, messages, users
from app.database import models
from app.database.database import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/chat")
def chat(req: ChatRequest):
    state = ChatState(user_message=req.message)
    result = flight_graph.invoke(state)
    return result

app.include_router(users.router)
app.include_router(conversations.router)
app.include_router(messages.router)
