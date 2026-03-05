from langchain_openai import ChatOpenAI
from app.core.config import OPENAI_API_KEY

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    api_key=OPENAI_API_KEY,
)
