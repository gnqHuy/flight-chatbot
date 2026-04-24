"""
app/scripts/draw_graph.py
Vẽ sơ đồ ReAct flight graph.
Chạy: python -m app.scripts.draw_graph
"""
import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main():
    from app.database.checkpointer import async_pool, checkpointer
    await async_pool.open()
    await checkpointer.setup()

    from app.ai_orchestrator.graph.flight_graph import init_flight_graph
    import app.ai_orchestrator.graph.flight_graph as _fg
    await init_flight_graph()
    graph = _fg.flight_graph

    print("🎨 Đang vẽ sơ đồ Graph...")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(out_dir, "flight_graph.png")
    mmd_path = os.path.join(out_dir, "flight_graph.mmd")

    # PNG
    try:
        img = graph.get_graph().draw_mermaid_png()
        with open(png_path, "wb") as f:
            f.write(img)
        print(f"✅ PNG: {png_path}")
    except Exception as e:
        print(f"⚠️  Không tạo được PNG (thiếu playwright/graphviz?): {e}")

    # Mermaid text (luôn hoạt động)
    try:
        mmd = graph.get_graph().draw_mermaid()
        with open(mmd_path, "w", encoding="utf-8") as f:
            f.write(mmd)
        print(f"✅ Mermaid: {mmd_path}")
        print("\n--- Mermaid diagram ---")
        print(mmd)
    except Exception as e:
        print(f"⚠️  Mermaid: {e}")

    # ASCII fallback
    try:
        print("\n--- ASCII ---")
        print(graph.get_graph().draw_ascii())
    except Exception as e:
        print(f"⚠️  ASCII: {e}")

    await async_pool.close()


if __name__ == "__main__":
    asyncio.run(main())