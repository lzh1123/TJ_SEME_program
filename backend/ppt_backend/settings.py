import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    app_name: str = "AI PPT Generator"
    data_dir: str = os.getenv("PPT_DATA_DIR", "backend/data")

    llm_model: str = os.getenv("LLM_MODEL", "DeepSeek-R1")
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1")
    llm_api_key: str = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY") or ""
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "60"))


settings = Settings()

