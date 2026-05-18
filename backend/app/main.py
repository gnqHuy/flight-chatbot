import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# Imports
import app.ai_orchestrator.graph.flight_graph as _fg
from app.api.api import api_router
from app.database.database import init_db
from app.database.checkpointer import async_pool
from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp, knowledge_mcp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Khởi động server...")
    init_db()
    print("✅ DB schema OK")

    await async_pool.open()
    checkpointer = AsyncPostgresSaver(async_pool)
    await checkpointer.setup() 
    print("✅ Checkpointer OK")
    
    _fg.flight_graph = _fg.builder.compile(checkpointer=checkpointer)
    print("✅ Flight graph OK")

    try:
        await flight_mcp.connect()
        await knowledge_mcp.connect()
        print("✅ MCP Persistent Clients ready")
    except Exception as e:
        print(f"⚠️ MCP clients warning: {e} (Sẽ tự động retry khi LLM gọi tool)")

    print("🚀 Server sẵn sàng nhận request!")
    
    yield
    
    print("🛑 Tắt server...")
    await async_pool.close()
    
    await flight_mcp.close()
    await knowledge_mcp.close()
    
    print("[OK] All connections closed")

app = FastAPI(lifespan=lifespan)

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

app.include_router(api_router, prefix="/api/v1")