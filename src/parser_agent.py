import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

model = ChatOpenAI(
    model="deepseek/deepseek-chat-v3-0324",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
    temperature=0,
)

def parser_agent(task_text: str, repo_context: str) -> dict:
    response = model.invoke([
        SystemMessage(content="""
You are a parser agent.

Your job is ONLY to convert the user's coding task into structured JSON.
Do NOT decide whether the task should run locally/edge or cloud.

Return ONLY valid JSON in this exact format:
{
  "task_summary": "<one sentence summary>",
  "requested_change": "<specific change the user wants>",
  "files_likely_needed": ["<file paths or file types likely needed>"],
  "required_capabilities": ["<skills/tools needed>"],
  "data_or_inputs_involved": ["<local files, user data, APIs, datasets, etc.>"],
  "will_modify_repo": <true or false>,
  "will_run_code": <true or false>,
  "repo_observations": ["<relevant observations from repo context>"],
  "ambiguities": ["<anything unclear or missing>"]
}
"""),
        HumanMessage(content=f"""
TASK:
{task_text}

REPO CONTEXT:
{repo_context[:12000]}
""")
    ])

    return json.loads(response.content)