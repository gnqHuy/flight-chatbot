"""
app/core/llm_setup.py

3 Candidate models (tương đương) — xử lý chat:
  - GPT-4o-mini   (OpenAI)
  - Gemini Flash  (Google)
  - Claude Haiku  (Anthropic)

1 Judge model (mạnh hơn hẳn) — đánh giá độc lập cả 3:
  - Gemini 2.5 Pro (Google)
  Lý do chọn Gemini Pro: không tham gia làm candidate,
  mạnh hơn cả 3 candidates, chi phí hợp lý.
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from app.core.config import OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY

# ── 3 Candidate models ────────────────────────────────────────────────────────
llm_openai = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)

llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

llm_claude = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0,
    api_key=ANTHROPIC_API_KEY,
)

# Default dùng trong production
llm = llm_openai

# ── 1 Judge model ─────────────────────────────────────────────────────────────
llm_as_judge = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)