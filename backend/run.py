import uvicorn
import os
import sys

# Thêm đường dẫn hiện tại vào path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Đang chuẩn bị khởi động Server...")
    try:
        from app.main import app
        print("✅ Load App thành công, bắt đầu chạy Uvicorn...")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    except Exception as e:
        print(f"❌ Lỗi khi khởi động: {e}")
        import traceback
        traceback.print_exc()