import os
from dotenv import load_dotenv

load_dotenv(override=True)

def get_env(var_name: str, default_value: str = None, required: bool = False) -> str:
    value = os.getenv(var_name)
    if value is not None:
        return value
    if required:
        raise ValueError(f"CRITICAL ERROR: Biến môi trường bắt buộc '{var_name}' chưa được cấu hình!")
    return default_value

OPENAI_API_KEY = get_env("OPENAI_API_KEY", required=True)
AMADEUS_API_KEY = get_env("AMADEUS_API_KEY", required=True)
AMADEUS_API_SECRET = get_env("AMADEUS_API_SECRET", required=True)
DATABASE_URL = get_env("DATABASE_URL", required=True)
SECRET_KEY = get_env("SECRET_KEY", required=True)

ALGORITHM = get_env("ALGORITHM", default_value="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(get_env("ACCESS_TOKEN_EXPIRE_MINUTES", default_value="60"))