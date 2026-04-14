from pydantic import BaseModel, Field
from typing import Optional

class Promotion(BaseModel):
    promo_code: Optional[str] = Field(
        description="Mã giảm giá (Ví dụ: THU5RR, FALL2024...). Nếu trong bài không đề cập mã cụ thể, trả về null."
    )
    promo_name: str = Field(
        description="Tên chương trình khuyến mãi hoặc Tiêu đề tóm tắt."
    )
    booking_start_date: Optional[str] = Field(
        description="Ngày bắt đầu mở bán/áp dụng (Định dạng YYYY-MM-DD). Nếu không rõ, trả về null."
    )
    booking_end_date: Optional[str] = Field(
        description="Ngày kết thúc mở bán/hết hạn (Định dạng YYYY-MM-DD). RẤT QUAN TRỌNG. Nếu không rõ, trả về null."
    )
    travel_start_date: Optional[str] = Field(
        description="Ngày bắt đầu thời gian bay áp dụng (Định dạng YYYY-MM-DD). Trả về null nếu không có."
    )
    travel_end_date: Optional[str] = Field(
        description="Ngày kết thúc thời gian bay áp dụng (Định dạng YYYY-MM-DD). Trả về null nếu không có."
    )
    description: str = Field(
        description="Mô tả ngắn gọn về mức giảm giá, chặng bay áp dụng (Khoảng 4-5 câu)."
    )
    conditions: str = Field(
        description="Điều kiện áp dụng (hạng vé, ngoại trừ lễ tết, đối tượng áp dụng...). Tóm tắt dạng gạch đầu dòng."
    )