"""
app/core/llm_setup.py

3 Candidate models — xử lý chat:
  - GPT-4o-mini   (OpenAI)
  - Gemini Flash  (Google)
  - Claude Haiku  (Anthropic)

1 Judge model — đánh giá độc lập cả 3:
  - Gemini 2.5 Pro (Google)
  Lý do chọn Gemini Pro: không tham gia làm candidate, 
  mạnh hơn cả 3 candidates, chi phí hợp lý.
"""
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from app.core.config import DEEPSEEK_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, ANTHROPIC_API_KEY

# ── 3 Candidate models ────────────────────────────────────────────────────────
llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY,
)

llm_claude = ChatAnthropic(
    model="claude-haiku-3-5",
    temperature=0,
    api_key=ANTHROPIC_API_KEY,
)

llm_deepseek = ChatOpenAI(
    model="deepseek-chat",
    temperature=0,
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    max_tokens=4095
)

llm_openai = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)

llm = llm_gemini

# ── 1 Judge model ─────────────────────────────────────────────────────────────
llm_as_judge = ChatOpenAI(
    model="gpt-5",
    temperature=0,
    api_key=OPENAI_API_KEY,
)