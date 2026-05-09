import os
from dotenv import load_dotenv
from pathlib import Path

_env_path = Path(__file__).resolve().parents[1] / ".env"
if _env_path.exists():
    load_dotenv(dotenv_path=_env_path)
else:
    load_dotenv()

print(os.getenv("LLM_MODEL", "DeepSeek-R1"))
print(os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1"))
print(os.getenv("DEEPSEEK_API_KEY") or "")