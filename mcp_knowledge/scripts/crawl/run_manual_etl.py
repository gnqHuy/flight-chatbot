import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.data_pipeline.pineline.policy_pipeline import PolicyETLPipeline
from app.services.data_pipeline.pineline.promo_pipeline import PromotionETLPipeline
def main():
    print("🤖 HỆ THỐNG CẬP NHẬT DỮ LIỆU CHATBOT HÀNG KHÔNG 🤖")
    print("1. Chạy toàn bộ (Cả Chính sách & Khuyến mãi)")
    print("2. Chỉ chạy Pipeline Chính sách (Policy)")
    print("3. Chỉ chạy Pipeline Khuyến mãi (Promotion)")
    print("0. Thoát")
    
    choice = input("\n👉 Nhập lựa chọn của bạn (0-3): ").strip()
    
    if choice == '1':
        PolicyETLPipeline().run_pipeline()
        PromotionETLPipeline().run_pipeline()
    elif choice == '2':
        PolicyETLPipeline().run_pipeline()
    elif choice == '3':
        PromotionETLPipeline().run_pipeline()
    elif choice == '0':
        print("👋 Tạm biệt!")
    else:
        print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()