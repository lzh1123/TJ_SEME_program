from __future__ import annotations

import json
from typing import Any, Callable, Optional, Type, TypeVar

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, TypeAdapter

from ...settings import settings


def _strip_markdown_fences(text: str) -> str:
    if "```" not in text:
        return text.strip()
    start = text.find("```")
    if start < 0:
        return text.strip()
    end = text.find("```", start + 3)
    if end < 0:
        return text.strip()
    inner = text[start + 3 : end].lstrip()
    if inner.lower().startswith("json"):
        inner = inner[4:].lstrip()
    return inner.strip()


def make_llm() -> ChatOpenAI:
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


def invoke_llm_text(
    llm: ChatOpenAI,
    prompt: ChatPromptTemplate,
    values: dict,
    stream: bool = False,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    messages = prompt.format_messages(**values)
    if not stream:
        resp = llm.invoke(messages)
        return getattr(resp, "content", "") or ""
    parts = []
    for chunk in llm.stream(messages):
        delta = getattr(chunk, "content", None)
        if not delta:
            continue
        parts.append(delta)
        if on_token:
            on_token(delta)
    return "".join(parts)


T = TypeVar("T", bound=BaseModel)


def parse_model(model_cls: Type[T], raw_text: str) -> T:
    text = _strip_markdown_fences(raw_text)
    data = json.loads(text)
    return TypeAdapter(model_cls).validate_python(data)


def parse_json(raw_text: str) -> Any:
    return json.loads(_strip_markdown_fences(raw_text))
