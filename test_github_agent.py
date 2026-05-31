from src.github_agent import github_agent
from src.parser_agent import parser_agent

repo_url = "https://github.com/AnikaAru/EdgeCloud-cse599"

task_text = """
Update README.md by adding a short description of each agent (categorized by python files having _agent at the end file name).
"""

github_result = github_agent(repo_url)

print("repo_path:", github_result["repo_path"])
print("repo_context length:", len(github_result["repo_context"]))

parsed = parser_agent(
    task_text=task_text,
    repo_context=github_result["repo_context"]
)

print(parsed)