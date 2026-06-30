from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from langchain_openai import ChatOpenAI

from ...settings import settings


@dataclass(frozen=True)
class LLMProviderSpec:
    provider: str
    label: str
    model: str
    api_base: str
    temperature: float = 0.0


LLM_PROVIDERS: Dict[str, LLMProviderSpec] = {
    "deepseek": LLMProviderSpec(
        provider="deepseek",
        label="DeepSeek",
        model=settings.deepseek_model,
        api_base=settings.deepseek_api_base,
    ),
    "qwen": LLMProviderSpec(
        provider="qwen",
        label="Qwen",
        model=settings.qwen_model,
        api_base=settings.qwen_api_base,
    ),
    "glm": LLMProviderSpec(
        provider="glm",
        label="GLM",
        model=settings.glm_model,
        api_base=settings.glm_api_base,
        temperature=1.0,
    ),
}

_PROVIDER_KEYS = {
    "deepseek": settings.deepseek_api_key,
    "qwen": settings.qwen_api_key,
    "glm": settings.glm_api_key,
}


@dataclass(frozen=True)
class UserLLMConfig:
    provider: str = "deepseek"
    api_key: Optional[str] = None
    model: Optional[str] = None
    api_base: Optional[str] = None

    @property
    def resolved(self) -> LLMProviderSpec:
        spec = LLM_PROVIDERS.get((self.provider or "deepseek").lower())
        if spec is None:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        return LLMProviderSpec(
            provider=spec.provider,
            label=spec.label,
            model=self.model or spec.model,
            api_base=self.api_base or spec.api_base,
            temperature=spec.temperature,
        )

    @property
    def resolved_api_key(self) -> str:
        spec = self.resolved
        return self.api_key or _PROVIDER_KEYS.get(spec.provider, "") or ""


def list_public_providers() -> list[dict]:
    return [
        {
            "provider": spec.provider,
            "label": spec.label,
            "model": spec.model,
            "apiBase": spec.api_base,
            "configured": bool(_PROVIDER_KEYS.get(spec.provider)),
        }
        for spec in LLM_PROVIDERS.values()
    ]


def make_platform_config(provider: Optional[str] = None) -> UserLLMConfig:
    return UserLLMConfig(provider=(provider or "deepseek").lower())


def make_chat_llm(config: Optional[UserLLMConfig] = None) -> ChatOpenAI:
    config = config or make_platform_config("deepseek")
    spec = config.resolved
    api_key = config.resolved_api_key
    if not api_key:
        raise ValueError(f"missing platform LLM api key for provider: {spec.provider}")
    return ChatOpenAI(
        model=spec.model,
        openai_api_base=spec.api_base,
        openai_api_key=api_key,
        temperature=spec.temperature,
        timeout=settings.llm_timeout,
        max_retries=2,
    )
