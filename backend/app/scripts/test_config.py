"""
app/scripts/test_config.py
Cấu hình models và constants cho test automation.
"""
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEST_DATE = "2026-05-15 10:00"

CANDIDATES = [
    {"id": "openai", "label": "GPT-4o-mini",     "llm_key": "llm_openai"},
    {"id": "gemini", "label": "Gemini 2.0 Flash", "llm_key": "llm_gemini"},
    {"id": "claude", "label": "Claude Haiku",      "llm_key": "llm_claude"},
]

JUDGE_LABEL = "Gemini 2.5 Pro"


class C:
    GREEN   = "\033[92m"
    RED     = "\033[91m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    GRAY    = "\033[90m"
    BOLD    = "\033[1m"
    RESET   = "\033[0m"