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
    # 查找所有的代码块
    lines = text.split("\n")
    in_code_block = False
    code_block_lines = []
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code_block:
                # 结束代码块
                break
            else:
                # 开始代码块
                in_code_block = True
                continue
        if in_code_block:
            code_block_lines.append(line)
    
    if code_block_lines:
        inner = "\n".join(code_block_lines).strip()
        # 移除可能的语言标识
        if inner.lower().startswith("json"):
            inner = inner[4:].lstrip()
        return inner.strip()
    
    # 如果没有找到完整的代码块，使用原始方法
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

def _extract_json_substring(text: str) -> str:
    s = text.strip()
    if not s:
        return s
    
    # 尝试找到第一个 { 或 [
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = s.find(open_ch)
        if start < 0:
            continue
            
        # 从 start 开始，找到匹配的结束括号
        balance = 1
        end = -1
        for i in range(start + 1, len(s)):
            if s[i] == open_ch:
                balance += 1
            elif s[i] == close_ch:
                balance -= 1
                if balance == 0:
                    end = i
                    break
        
        if end > start:
            result = s[start : end + 1].strip()
            # 确保结果是有效的 JSON 开始
            if result.startswith(("{", "[")):
                return result
    
    return s


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
    # 第一阶段：清理文本
    text = _strip_markdown_fences(raw_text)
    text = _extract_json_substring(text)
    
    try:
        data = json.loads(text)
        return TypeAdapter(model_cls).validate_python(data)
    except Exception as e1:
        # 尝试更激进的清理
        try:
            # 移除任何可能的尾随内容
            if text.strip().endswith("}") or text.strip().endswith("]"):
                # 已经是完整的，尝试其他方式
                pass
            else:
                # 尝试找到最后一个完整的 JSON
                text = _extract_json_substring(text)
            
            data = json.loads(text)
            return TypeAdapter(model_cls).validate_python(data)
        except Exception as e2:
            # 最后尝试：从原始文本中重新提取
            final_text = _extract_json_substring(raw_text)
            data = json.loads(final_text)
            return TypeAdapter(model_cls).validate_python(data)


def parse_json(raw_text: str) -> Any:
    text = _extract_json_substring(_strip_markdown_fences(raw_text))
    try:
        return json.loads(text)
    except Exception:
        # 最后尝试：直接从原始文本提取
        return json.loads(_extract_json_substring(raw_text))
