import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_backend_dir = Path(__file__).resolve().parents[1]
_project_dir = _backend_dir.parent
_env_candidates = [_backend_dir / ".env", _project_dir / ".env"]
for _p in _env_candidates:
    if _p.exists():
        load_dotenv(dotenv_path=_p)
        break
else:
    load_dotenv()

@dataclass(frozen=True)
class Settings:
    app_name: str = "AI PPT Generator"
    data_dir: str = os.getenv("PPT_DATA_DIR", "data")

    llm_model: str = os.getenv("LLM_MODEL", "DeepSeek-R1")
    llm_api_base: str = os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1")
    llm_api_key: str = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "180"))


settings = Settings()
