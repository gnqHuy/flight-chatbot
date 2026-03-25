from fastapi import APIRouter
from app.api.routes import admin_airline, admin_crawler, auth, conversations, flights

api_router = APIRouter()

api_router.include_router(auth.router)

api_router.include_router(conversations.router) 
    
api_router.include_router(flights.router) 

api_router.include_router(admin_crawler.router)

api_router.include_router(admin_airline.router)


