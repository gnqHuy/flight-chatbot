"""
app/scripts/test_judge.py
Judge prompts, Pydantic models, và chains.
1 judge model (Gemini 2.5 Pro) đánh giá cả 3 candidates.
"""
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate


UX_JUDGE_PROMPT = """Bạn là Chuyên gia UX QA cho hệ thống AI Chatbot đặt vé máy bay.
Nhiệm vụ: Đánh giá CHẤT LƯỢNG UX + phát hiện HALLUCINATION.
KHÔNG check kỹ thuật (tool calls, action type — đã kiểm tra riêng).

━━━ THÔNG TIN LƯỢT CHAT ━━━
Câu hỏi: {user_query}
Lịch sử hội thoại: {conversation_history}
Hành vi mong đợi: {expected_behavior}
Hành vi cấm: {anti_preference}

━━━ DỮ LIỆU THỰC TẾ TỪ TOOL (ground truth) ━━━
{tool_results_summary}

━━━ CÂU TRẢ LỜI CỦA BOT ━━━
{bot_response}

━━━ TIÊU CHÍ CHẤM ĐIỂM UX (1-5) ━━━
5 — Tự nhiên, thân thiện, đúng nội dung, không vi phạm anti_preference, không hallucinate.
4 — Đúng nội dung nhưng hơi lan man, lặp thông tin, hoặc 1 chi tiết nhỏ thiếu tự nhiên.
3 — Xử lý được ý chính nhưng máy móc, bỏ sót 1 phần yêu cầu, hoặc có hallucination nhẹ.
2 — Vi phạm anti_preference hoặc hallucinate số liệu/thông tin quan trọng.
1 — Vi phạm nghiêm trọng, sai sự thật rõ ràng, hoặc không giải quyết được yêu cầu.

━━━ KIỂM TRA HALLUCINATION (bắt buộc) ━━━
So sánh câu trả lời bot với "DỮ LIỆU THỰC TẾ TỪ TOOL".
Hallucination xảy ra khi bot đề cập thông tin KHÔNG CÓ trong tool results:
  - Giá vé / số lượng chuyến bay không khớp
  - Khuyến mãi khi tool trả về "không tìm thấy"
  - Chính sách khi tool không trả về dữ liệu đó
  - Hãng bay / chuyến cụ thể không có trong tool results

KHÔNG coi là hallucination:
  - Bot nói "mời xem danh sách trên UI"
  - Bot diễn đạt lại thông tin tool theo ngôn ngữ tự nhiên
  - Bot hỏi thêm khi tool báo lỗi/thiếu params
  - Bot nhắc lại thông tin trong user_query 
  - Bot nhắc lại thông tin user đã cung cấp conversation history trước đó dù tool hay user_query không trả về

━━━ LƯU Ý ━━━
- Không trừ điểm vì tool sai (đã kiểm tra ở lớp Technical).
- Nếu expected là "báo không có vé" và bot làm đúng → 5 điểm.
- Để lộ tag hệ thống [DỮ LIỆU...] → trừ 1 điểm.
- Tool trả về lỗi/rỗng mà bot vẫn bịa → tối đa 2 điểm.
"""

SCENARIO_JUDGE_PROMPT = """Bạn là Chuyên gia UX QA. Đánh giá TỔNG THỂ kịch bản hội thoại.

Mục tiêu kịch bản: {description}
Model đang đánh giá: {model_label}
Lịch sử hội thoại:
{conversation_history}

TIÊU CHÍ (1-5):
5 — Xuất sắc. Luồng mượt mà, giải quyết trọn vẹn mục tiêu.
4 — Khá tốt. Đạt mục tiêu nhưng 1-2 chỗ hơi máy móc.
3 — Trung bình. Có vấp váp nhưng cuối cùng qua được.
2 — Kém. Đứt gãy giữa chừng hoặc bỏ sót intent quan trọng.
1 — Thất bại hoàn toàn. Không giải quyết được mục tiêu kịch bản.
"""


class TurnUXScore(BaseModel):
    score:                int  = Field(description="Điểm UX 1-5")
    reason:               str  = Field(description="Lý do ngắn gọn về UX")
    hallucination_found:  bool = Field(description="True nếu phát hiện hallucination")
    hallucination_detail: str  = Field(description="Mô tả hallucination nếu có")


class ScenarioUXScore(BaseModel):
    score:  int = Field(description="Điểm tổng thể 1-5")
    reason: str = Field(description="Đánh giá tổng thể")


def build_judge_chains(_judge_llm_unused=None) -> dict:
    """
    Gọi Gemini trực tiếp qua google.genai SDK (không qua LangChain).
    LangSmith không trace → không tính cost vào project.
    """
    import json as _json
    import os
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    MODEL  = "gemini-2.5-pro"

    JSON_TURN_SUFFIX = """

TRẢ VỀ JSON THUẦN TÚY (không markdown), đúng format:
{"score": <1-5>, "reason": "<lý do>", "hallucination_found": <true|false>, "hallucination_detail": "<mô tả hoặc rỗng>"}"""

    JSON_SCENARIO_SUFFIX = """

TRẢ VỀ JSON THUẦN TÚY (không markdown), đúng format:
{"score": <1-5>, "reason": "<đánh giá tổng thể>"}"""

    def _parse(text: str) -> dict:
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return _json.loads(text.strip())

    def _call(prompt: str) -> str:
        resp = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0),
        )
        return resp.text

    def judge_turn(
        user_query,
        conversation_history,
        expected_behavior,
        anti_preference,
        tool_results_summary,
        bot_response,
    ) -> TurnUXScore:
        prompt = (
            UX_JUDGE_PROMPT
            .replace("{user_query}", user_query)
            .replace("{conversation_history}", conversation_history or "(chưa có lịch sử trước đó)")
            .replace("{expected_behavior}", expected_behavior)
            .replace("{anti_preference}", anti_preference)
            .replace("{tool_results_summary}", tool_results_summary)
            .replace("{bot_response}", bot_response)
            + JSON_TURN_SUFFIX
        )
        data = _parse(_call(prompt))
        return TurnUXScore(
            score=int(data.get("score", 0)),
            reason=str(data.get("reason", "")),
            hallucination_found=bool(data.get("hallucination_found", False)),
            hallucination_detail=str(data.get("hallucination_detail", "")),
        )

    def judge_scenario(description, model_label, conversation_history) -> ScenarioUXScore:
        prompt = (
            SCENARIO_JUDGE_PROMPT
            .replace("{description}", description)
            .replace("{model_label}", model_label)
            .replace("{conversation_history}", conversation_history)
            + JSON_SCENARIO_SUFFIX
        )
        data = _parse(_call(prompt))
        return ScenarioUXScore(
            score=int(data.get("score", 0)),
            reason=str(data.get("reason", "")),
        )

    return {"turn": judge_turn, "scenario": judge_scenario}