import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from outline_prompt import outline_prompt_build
from outline_schema import OutlinePromptSchema, OutlineBuildSchema
from parser import OutlineBuildParser


load_dotenv()


def _make_llm():
    model = os.getenv("LLM_MODEL", "DeepSeek-R1")
    api_base = os.getenv("LLM_API_BASE", "https://llmapi.tongji.edu.cn/v1")
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("LLM_API_KEY")

    return ChatOpenAI(
        model=model,
        openai_api_base=api_base,
        openai_api_key=api_key,
        temperature=0,
    )


def outline_build(outline_prompt: OutlinePromptSchema) -> OutlineBuildSchema:
    prompt_path = Path(__file__).resolve().parents[1] / "prompt" / "outline_build.md"
    system_prompt = prompt_path.read_text(encoding="utf-8")

    parser = OutlineBuildParser()
    llm = _make_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{outline_prompt_json}"),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    outline_prompt_json = outline_prompt.model_dump_json(
        ensure_ascii=False,
        indent=2,
    )

    chain = prompt | llm | parser
    return chain.invoke({"outline_prompt_json": outline_prompt_json})


def build_outline_bundle(topic: str) -> dict:
    outline_prompt = outline_prompt_build(topic)
    outline = outline_build(outline_prompt)
    return {
        "outline_prompt": outline_prompt,
        "outline": outline,
    }


if __name__ == "__main__":
    topic = input("输入主题： ").strip()
    bundle = build_outline_bundle(topic)
    print(bundle["outline"].model_dump_json(ensure_ascii=False, indent=2))
