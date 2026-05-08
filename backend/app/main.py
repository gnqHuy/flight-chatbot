from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.database.checkpointer import async_pool, checkpointer
from app.database.database import init_db
from app.database.checkpointer import async_pool
from app.ai_orchestrator.graph.flight_graph import init_flight_graph
from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp, knowledge_mcp

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:3000",
        "http://192.168.174.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    init_db()
    print("✅ DB schema OK")

    await async_pool.open()
    await checkpointer.setup()
    print("✅ Checkpointer OK")

    await init_flight_graph()
    print("✅ Flight graph OK")

    try:
        await flight_mcp.connect()
        await knowledge_mcp.connect()
        print("✅ MCP clients ready")
    except Exception as e:
        print(f"⚠️  MCP clients warning: {e} (sẽ retry khi gọi tool)")

    print("🚀 Server sẵn sàng nhận request!")

@app.on_event("shutdown")
async def on_shutdown():
    await async_pool.close()
    print("[OK] Connection pool closed")

app.include_router(api_router, prefix="/api/v1")