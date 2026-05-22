"""
app/scripts/test_config.py
Cấu hình models và constants cho test automation.
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATE = "2026-05-20 10:00"

CANDIDATES = [
    {"id": "gemini", "label": "Gemini 2.5 Flash", "llm_key": "llm_gemini"},
    {"id": "claude", "label": "Claude Haiku",      "llm_key": "llm_claude"},
    {"id": "deepseek", "label": "DeepSeek V4",      "llm_key": "llm_deepseek"},
]

# ── Chọn model chạy test ──────────────────────────────────────────────────────
# Đổi giá trị này để chạy model khác: "gemini" | "claude" | "deepseek"
CANDIDATE_ID = "gemini"

# Đổi giá trị này để chạy model judge khác: "gemini-2.5-pro" | "gpt-4.1"
JUDGE_ID = "gpt-4.1"
class C:
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    GRAY    = "\033[90m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"