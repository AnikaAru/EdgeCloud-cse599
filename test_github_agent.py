# test_openrouter.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model_name="deepseek/deepseek-chat-v3-0324",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0,
    timeout=30,
)

resp = llm.invoke("Say hi in JSON: {\"message\": \"hi\"}")
print(resp.content)