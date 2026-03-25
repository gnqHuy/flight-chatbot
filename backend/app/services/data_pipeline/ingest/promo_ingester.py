import os
import json
import logging
from datetime import datetime
from sqlmodel import Session, create_engine
from langchain_openai import OpenAIEmbeddings

from app.core.config import OPENAI_API_KEY, DATABASE_URL 
from app.database.models.flight_promotion import FlightPromotion

logger = logging.getLogger(__name__)

class PromoDBIngester:
    def __init__(self):
        self.default_json_path = os.path.join("app", "data", "promotions", "cleaned_promotions", "processed_promotions.json")
        self.engine = create_engine(DATABASE_URL)
        self.embedder = OpenAIEmbeddings(
            model="text-embedding-3-small", 
            api_key=OPENAI_API_KEY
        )

    def ingest_to_db(self, json_path: str = None):
        target_path = json_path or self.default_json_path
        
        logger.info("🗄️ BƯỚC 3: BẮT ĐẦU NẠP DỮ LIỆU KHUYẾN MÃI VÀO DATABASE...")
        
        if not os.path.exists(target_path):
            logger.error(f"❌ Không tìm thấy file JSON tại: {target_path}")
            return False

        with open(target_path, "r", encoding="utf-8") as f:
            promotions_data = json.load(f)

        logger.info(f"🚀 Bắt đầu xử lý {len(promotions_data)} khuyến mãi...")

        texts_to_embed = []
        for promo in promotions_data:
            rag_text = f"Tên khuyến mãi: {promo['promo_name']}\nMô tả: {promo['description']}\nĐiều kiện áp dụng: {promo['conditions']}"
            texts_to_embed.append(rag_text)

        logger.info("🧠 Đang gọi OpenAI API để tạo Vector Embeddings (Vui lòng đợi)...")
        embeddings_list = self.embedder.embed_documents(texts_to_embed)
        logger.info("   ✅ Đã lấy xong Vector Embeddings!")

        logger.info("🗄️ Đang nạp dữ liệu vào Database...")
        try:
            with Session(self.engine) as session:
                # Tùy chọn: Xóa data cũ trước khi nạp mới (Nếu bạn muốn refresh mỗi tuần)
                # session.query(FlightPromotion).delete() 
                
                for idx, promo in enumerate(promotions_data):
                    start_date = None
                    if promo.get("booking_start_date"):
                        start_date = datetime.strptime(promo["booking_start_date"], "%Y-%m-%d").date()
                        
                    end_date = None
                    if promo.get("booking_end_date"):
                        end_date = datetime.strptime(promo["booking_end_date"], "%Y-%m-%d").date()

                    t_start_date = None
                    if promo.get("travel_start_date"):
                        t_start_date = datetime.strptime(promo["travel_start_date"], "%Y-%m-%d").date()
                        
                    t_end_date = None
                    if promo.get("travel_end_date"):
                        t_end_date = datetime.strptime(promo["travel_end_date"], "%Y-%m-%d").date()

                    db_promo = FlightPromotion(
                        airline=promo["airline"],
                        promo_code=promo.get("promo_code"),
                        promo_name=promo["promo_name"],
                        booking_start_date=start_date,
                        booking_end_date=end_date,
                        travel_start_date=t_start_date,
                        travel_end_date=t_end_date,
                        description=promo["description"],
                        conditions=promo["conditions"],
                        url=promo["url"],
                        embedding=embeddings_list[idx] 
                    )
                    session.add(db_promo)
                    
                session.commit()
            logger.info("🎉 THÀNH CÔNG! Đã lưu toàn bộ khuyến mãi vào bảng 'flight_promotions'.")
            return True
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi nạp DB Khuyến mãi: {e}")
            return False