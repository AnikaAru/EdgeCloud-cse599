import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

model = ChatOpenAI(
    model="openai/gpt-4o-mini",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)

agent = create_react_agent(
    model=model,
    tools=[],
    # this is just an example, we can look into prompt engineering + customing it for each agent
    prompt="You are an agent that helps classify programming tasks for edge vs cloud execution."
)