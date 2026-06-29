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


LLM_PROVIDERS: Dict[str, LLMProviderSpec] = {
    "deepseek": LLMProviderSpec(
        provider="deepseek",
        label="DeepSeek",
        model="Deepseek-V4-pro",
        api_base="https://api.deepseek.com",
    ),
    "qwen": LLMProviderSpec(
        provider="qwen",
        label="Qwen",
        model="qwen-plus-latest",
        api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
    "kimi": LLMProviderSpec(
        provider="kimi",
        label="Kimi",
        model="kimi-k2-latest",
        api_base="https://api.moonshot.cn/v1",
    ),
}


@dataclass(frozen=True)
class UserLLMConfig:
    provider: str
    api_key: str
    model: Optional[str] = None
    api_base: Optional[str] = None

    @property
    def resolved(self) -> LLMProviderSpec:
        spec = LLM_PROVIDERS.get(self.provider)
        if spec is None:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        return LLMProviderSpec(
            provider=spec.provider,
            label=spec.label,
            model=self.model or spec.model,
            api_base=self.api_base or spec.api_base,
        )


def make_chat_llm(config: Optional[UserLLMConfig] = None) -> ChatOpenAI:
    if config is None:
        if not settings.llm_api_key:
            raise ValueError("missing LLM api key")
        return ChatOpenAI(
            model=settings.llm_model,
            openai_api_base=settings.llm_api_base,
            openai_api_key=settings.llm_api_key,
            temperature=0,
            timeout=settings.llm_timeout,
            max_retries=2,
        )

    if not config.api_key:
        raise ValueError("missing user LLM api key")
    spec = config.resolved
    return ChatOpenAI(
        model=spec.model,
        openai_api_base=spec.api_base,
        openai_api_key=config.api_key,
        temperature=0,
        timeout=settings.llm_timeout,
        max_retries=2,
    )
