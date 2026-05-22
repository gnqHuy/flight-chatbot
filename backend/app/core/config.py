import os
from dotenv import load_dotenv

load_dotenv()

def get_env(var_name: str, default_value: str = None, required: bool = False) -> str:
    value = os.getenv(var_name)
    if value is not None:
        return value
    if required:
        raise ValueError(f"CRITICAL ERROR: Biến môi trường bắt buộc '{var_name}' chưa được cấu hình!")
    return default_value

OPENAI_API_KEY = get_env("OPENAI_API_KEY", required=True)
GOOGLE_API_KEY = get_env("GOOGLE_API_KEY", required=True)
ANTHROPIC_API_KEY = get_env("ANTHROPIC_API_KEY", required=True)
DEEPSEEK_API_KEY = get_env("DEEPSEEK_API_KEY", required=True)
BACKEND_DATABASE_URL = get_env("BACKEND_DATABASE_URL", required=True)
CHECKPOINT_DATABASE_URL = get_env("BACKEND_CHECKPOINT_DATABASE_URL", default_value=BACKEND_DATABASE_URL)
SECRET_KEY = get_env("SECRET_KEY", required=True)

ALGORITHM = get_env("ALGORITHM", default_value="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_env("ACCESS_TOKEN_EXPIRE_MINUTES", default_value="60"))