import os;
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import MessagesPlaceholder
from parser import OutlineParser

load_dotenv()

def outline_prompt_build(topic : str) -> str :
    with open("backend/prompt/outline_prompt.md", "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    parser = OutlineParser()

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        # MessagesPlaceholder(variable_name="chat_history"),
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