from app.ai.graph.flight_graph import build_flight_graph


app = build_flight_graph()

print("🎨 Đang vẽ sơ đồ Graph...")

try:
    graph_image = app.get_graph().draw_mermaid_png()
    
    output_file = "flight_bot_structure.png"
    with open(output_file, "wb") as f:
        f.write(graph_image)
        
    print(f"✅ Đã lưu sơ đồ thành công: {output_file}")
    print("👉 Bạn hãy mở file ảnh này lên để xem luồng đi.")

except Exception as e:
    print(f"❌ Không thể vẽ ảnh (có thể do thiếu thư viện): {e}")
    
    print("\n--- Sơ đồ dạng Text (ASCII) ---")
    print(app.get_graph().draw_ascii())