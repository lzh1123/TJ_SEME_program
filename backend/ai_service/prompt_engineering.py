import os;
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

with open("../prompt/prompt_engineering_prompt.md", "r", encoding="utf-8") as f:
    prompt = f.read()

model = ChatOpenAI(
    model="deepseek-reasoner",
    openai_api_base="https://llmapi.tongji.edu.cn/v1",
    openai_api_key=os.getenv["DEEPSEEK_API_KEY"],
)