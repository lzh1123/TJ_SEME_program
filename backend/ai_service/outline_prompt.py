import os
from pathlib import Path
from typing import Callable, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
try:
    from .parser import OutlinePromptParser
except ImportError:
    from parser import OutlinePromptParser

load_dotenv()

def _invoke_llm_text(llm: ChatOpenAI, messages, stream: bool, on_token: Optional[Callable[[str], None]] = None) -> str:
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


def outline_prompt_build(topic: str, stream: bool = False):
    prompt_path = Path(__file__).resolve().parents[1] / "prompt" / "outline_prompt.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    parser = OutlinePromptParser()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{topic}")
    ]).partial(
        format_instructions=parser.get_format_instructions()
    )

    llm = ChatOpenAI(
        model=os.getenv("LLM_MODEL", "DeepSeek-R1"),
        openai_api_base=os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1"),
        openai_api_key=os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY"),
        temperature=0,
        timeout=float(os.getenv("LLM_TIMEOUT", "60")),
        max_retries=2,
    )

    messages = prompt.format_messages(topic=topic)
    raw_text = _invoke_llm_text(
        llm,
        messages,
        stream=stream,
        on_token=(lambda t: print(t, end="", flush=True)) if stream else None,
    )
    if stream:
        print(flush=True)
    result = parser.parse(raw_text)
    
    return result

# 测试
if __name__ == "__main__":
    i = input("输入主题： ")
    result = outline_prompt_build(i)
    print(result)
