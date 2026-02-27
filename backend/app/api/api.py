from fastapi import APIRouter
from app.api.routes import auth, conversations, flights

api_router = APIRouter()

api_router.include_router(auth.router)

api_router.include_router(conversations.router) 
    
api_router.include_router(flights.router) 
