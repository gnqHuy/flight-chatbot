from app.ai.llm.intent_extractor import extract_intent_and_slots

tests = [
    "Tôi muốn tìm chuyến bay từ Hà Nội đi HCM",
    "Bay từ Đà Nẵng vào Sài Gòn ngày 20 tháng 3",
    "So sánh vé rẻ nhất",
    "Hello bạn",
]

for t in tests:
    print("INPUT:", t)
    print("OUTPUT:", extract_intent_and_slots(t))
    print("------")
