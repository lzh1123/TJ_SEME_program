import os
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from parser import OutlinePromptParser

load_dotenv()

def outline_prompt_build(topic: str):
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
        model="DeepSeek-R1",
        openai_api_base="https://llmapi.tongji.edu.cn/v1",
        openai_api_key=os.getenv("DEEPSEEK_API_KEY"),
        temperature=0
    )

    chain = prompt | llm | parser

    result = chain.invoke({
        "topic" : topic,
    })
    
    return result

# 测试
if __name__ == "__main__":
    i = input("输入主题： ")
    result = outline_prompt_build(i)
    print(result)
