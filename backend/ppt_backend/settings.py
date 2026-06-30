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
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", os.getenv("LLM_MODEL", "Deepseek-V4-pro"))
    deepseek_api_base: str = os.getenv("DEEPSEEK_API_BASE", os.getenv("LLM_API_BASE", "https://api.deepseek.com"))
    deepseek_api_key: str = (
        os.getenv("DEEPSEEK_API_KEY")
        or os.getenv("LLM_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or ""
    )
    qwen_model: str = os.getenv("QWEN_MODEL", "qwen-plus")
    qwen_workspace_id: str = os.getenv("QWEN_WORKSPACE_ID", os.getenv("DASHSCOPE_WORKSPACE_ID", ""))
    qwen_api_base: str = os.getenv(
        "QWEN_API_BASE",
        (
            f"https://{qwen_workspace_id}.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
            if qwen_workspace_id
            else "https://dashscope.aliyuncs.com/compatible-mode/v1"
        ),
    )
    qwen_api_key: str = os.getenv("QWEN_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
    kimi_model: str = os.getenv("KIMI_MODEL", "kimi-k2.6")
    kimi_api_base: str = os.getenv("KIMI_API_BASE", "https://api.moonshot.cn/v1")
    kimi_api_key: str = os.getenv("KIMI_API_KEY", os.getenv("MOONSHOT_API_KEY", ""))

    # Database (PostgreSQL)
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://myuser:qwer1234@119.3.125.141:5432/slideon",
    )
    database_echo: bool = os.getenv("DATABASE_ECHO", "false").lower() == "true"

    @property
    def database_url_sync(self) -> str:
        """Return a sync-style URL (asyncpg → psycopg2) for Alembic / sync engine."""
        return self.database_url.replace("+asyncpg", "")

    # JWT
    jwt_secret_key: str = os.getenv(
        "JWT_SECRET_KEY",
        "slideon-jwt-secret-change-in-production-please",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    jwt_refresh_token_expire_days: int = int(
        os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7")
    )

    # RAG / Milvus
    milvus_uri: str = os.getenv("MILVUS_URI", "http://localhost:19530")
    milvus_db: str = os.getenv("MILVUS_DB", "default")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-zh-v1.5")
    web_search_region: str = os.getenv("WEB_SEARCH_REGION", "wt-wt")
    web_search_provider: str = os.getenv("WEB_SEARCH_PROVIDER", "baidu")
    baidu_search_api_key: str = (
        os.getenv("BAIDU_SEARCH_API_KEY")
        or os.getenv("QIANFAN_API_KEY")
        or os.getenv("WEB_SEARCH_API_KEY")
        or ""
    )
    web_search_timeout: int = int(os.getenv("WEB_SEARCH_TIMEOUT", "20"))
    rag_enabled: bool = os.getenv("RAG_ENABLED", "true").lower() == "true"


settings = Settings()
