import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

load_dotenv()

model = ChatOpenAI(
    model="deepseek/deepseek-chat-v3-0324",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)

router_agent = create_react_agent(
    model=model,
    tools=[],
    # this is just an example, we can look into prompt engineering + customing it for each agent
    prompt="""You are a runtime monitor for AI agent workflows.
When given a task, evaluate it on four dimensions (score 0-10):
1. Privacy Sensitivity: Does it involve local files, passwords, or personal data?
2. Security Risk: Is it irreversible? (delete files, send emails, run scripts)
3. Task Complexity: Does it require heavy reasoning or multi-step execution?
4. Latency Sensitivity: Does it need a fast response?

Routing rules:
- BLOCKED: security >= 9, refuse execution
- CONFIRM: security >= 7 OR privacy >= 7, ask user first
- CLOUD: complexity >= 7, needs strong cloud model
- LOCAL: latency >= 7 (needs fast response) OR everything else, run on edge device
- If task is ambiguous or context is insufficient: default to CONFIRM
- If task involves running any script or executable: security >= 8, route to CONFIRM minimum
You MUST respond in this exact JSON format, nothing else:
{
  "privacy": <0-10>,
  "security": <0-10>,
  "complexity": <0-10>,
  "latency": <0-10>,
  "routing": "<LOCAL|CLOUD|CONFIRM|BLOCKED>",
  "reason": "<one sentence explanation>"
}"""
)
