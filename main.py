"""
main.py — Programmatic entry point.

For interactive use, run LangGraph Studio instead:
  1. Install: pip install langgraph-cli
  2. Start:   langgraph dev
  3. Open:    http://localhost:8123 (Studio UI opens automatically)

In Studio you can chat with the graph, input repo_url + task_text,
watch nodes fire in real time, and inspect every state transition.
"""

import os
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

from src.supervisor import graph


def run(repo_url: str, task_text: str, confirm: bool | None = None) -> dict:
    initial_state = {
        "repo_url": repo_url,
        "task_text": task_text,
        "user_confirmation": confirm,
    }
    return graph.invoke(initial_state)


if __name__ == "__main__":
    result = run(
        repo_url="https://github.com/your-org/your-repo",
        task_text="Add docstrings to all public functions in utils.py",
    )
    print(result.get("final_answer"))