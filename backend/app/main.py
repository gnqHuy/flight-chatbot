from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.database.database import init_db
from app.ai_orchestrator.graph.flight_graph import init_flight_graph
from app.database.checkpointer import async_pool, checkpointer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3000",
        "http://192.168.174.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    init_db()

    await async_pool.open()
    await checkpointer.setup()
    print("✅ Checkpointer ready")

    await init_flight_graph()

    print("✅ Backend startup complete")


@app.on_event("shutdown")
async def on_shutdown():
    await async_pool.close()


app.include_router(api_router, prefix="/api/v1")