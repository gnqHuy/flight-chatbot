from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.database.checkpointer import async_pool, checkpointer
from app.database.database import init_db

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
    # 1. Init DB schema (sync)
    init_db()
    print("✅ DB schema OK")

    # 2. Mở async pool cho LangGraph checkpointer
    await async_pool.open()
    await checkpointer.setup()
    print("✅ Checkpointer OK")

    # 3. Compile ReAct agent graph — PHẢI sau khi checkpointer ready
    from app.ai_orchestrator.graph.flight_graph import init_flight_graph
    await init_flight_graph()
    print("✅ Flight graph OK")

    # 4. Kết nối MCP servers (non-blocking — chỉ kiểm tra, không block startup)
    try:
        from app.ai_orchestrator.graph.tools.mcp_client import flight_mcp, knowledge_mcp
        print("✅ MCP clients ready")
    except Exception as e:
        print(f"⚠️  MCP clients warning: {e} (sẽ retry khi gọi tool)")

    print("🚀 Server sẵn sàng nhận request!")


app.include_router(api_router, prefix="/api/v1")