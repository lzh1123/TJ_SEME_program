from functools import lru_cache

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Auth Backend"
    auth_mode: str = Field(default="both", alias="AUTH_MODE")
    app_base_url: str = Field(default="http://localhost:8000", alias="APP_BASE_URL")
    force_https: bool = Field(default=False, alias="FORCE_HTTPS")
    trust_proxy_headers: bool = Field(default=False, alias="TRUST_PROXY_HEADERS")
    hsts_enabled: bool = Field(default=False, alias="HSTS_ENABLED")
    hsts_max_age: int = Field(default=31536000, alias="HSTS_MAX_AGE")
    hsts_include_subdomains: bool = Field(default=True, alias="HSTS_INCLUDE_SUBDOMAINS")
    hsts_preload: bool = Field(default=False, alias="HSTS_PRELOAD")
    allowed_hosts: str = Field(default="*", alias="ALLOWED_HOSTS")

    database_url_override: str | None = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="auth_backend", alias="POSTGRES_DATABASE")

    redis_url_override: str | None = Field(default=None, alias="REDIS_URL")
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_ttl_minutes: int = Field(default=15, alias="JWT_ACCESS_TTL")
    jwt_refresh_ttl_days: int = Field(default=30, alias="JWT_REFRESH_TTL")
    session_ttl_days: int = Field(default=30, alias="SESSION_TTL_DAYS")

    auth_user_table: str = Field(default="users", alias="AUTH_USER_TABLE")
    postgres_user_table_legacy: str | None = Field(default=None, alias="POSTGRES_USER_TABLE")
    verify_code_table: str = Field(default="auth_verify_codes", alias="VERIFY_CODE_TABLE")
    refresh_token_table: str = Field(default="auth_refresh_tokens", alias="AUTH_REFRESH_TOKEN_TABLE")
    role_table: str = Field(default="roles", alias="AUTH_ROLE_TABLE")
    permission_table: str = Field(default="permissions", alias="AUTH_PERMISSION_TABLE")
    user_role_table: str = Field(default="user_roles", alias="AUTH_USER_ROLE_TABLE")
    role_permission_table: str = Field(
        default="role_permissions", alias="AUTH_ROLE_PERMISSION_TABLE"
    )
    policy_rule_table: str = Field(default="policy_rules", alias="AUTH_POLICY_RULE_TABLE")
    service_credential_table: str = Field(
        default="service_credentials", alias="AUTH_SERVICE_CREDENTIAL_TABLE"
    )

    internal_service_token: str = Field(default="internal-token", alias="INTERNAL_SERVICE_TOKEN")
    redis_session_prefix: str = Field(default="auth:session", alias="REDIS_SESSION_PREFIX")
    smtp_host: str = Field(default="", alias="EMAIL_SMTP_HOST")
    smtp_ssl_port: int = Field(default=465, alias="EMAIL_SMTP_SSL_PORT")
    smtp_starttls_port: int = Field(default=25, alias="EMAIL_SMTP_STARTTLS_PORT")
    smtp_user: str = Field(default="", alias="EMAIL_USER")
    smtp_password: str = Field(default="", alias="EMAIL_PASSWORD")
    smtp_sender_name: str = Field(default="Auth Backend", alias="EMAIL_SENDER_NAME")
    smtp_use_ssl: bool = Field(default=True, alias="EMAIL_SMTP_USE_SSL")
    smtp_enabled: bool = Field(default=False, alias="EMAIL_SMTP_ENABLED")

    @computed_field
    @property
    def database_url(self) -> str:
        if self.database_url_override:
            return self.database_url_override
        database = self.postgres_database or "auth_backend"
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{database}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        if self.redis_url_override:
            return self.redis_url_override
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def user_table(self) -> str:
        return self.postgres_user_table_legacy or self.auth_user_table

    @property
    def jwt_enabled(self) -> bool:
        return self.auth_mode in {"jwt", "both"}

    @property
    def session_enabled(self) -> bool:
        return self.auth_mode in {"session", "both"}

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
