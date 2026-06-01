import os
from dataclasses import dataclass
from pathlib import Path

from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from src.edge_coding_agent import EDGE_CODING_PROMPT
from src.repo_ops import (
    RepoOpError,
    apply_files,
    clone_repo,
    commit_all,
    create_branch,
    load_edge_coding_json,
    slugify,
    push_branch,
)


@dataclass
class EdgeCodingResult:
    branch: str
    repo_dir: str
    summary: str
    written_files: list[str]


def run_edge_coding_task(
    *,
    remote_url: str,
    task: str,
    repo_root_hint: str | None = None,
    language: str = "python",
    branch_prefix: str = "edge-task",
    commit_message_prefix: str = "Edge task:",
    keep_workdir: bool = True,
) -> EdgeCodingResult:
    """Clone repo, create branch, ask agent for file contents, apply, commit, push.

    Notes:
    - Requires git credentials configured on this machine for pushing.
    - The agent generates full file contents for the paths it touches.
    - Tools are scoped to the cloned repo path so the agent can read files directly.
    """
    work = clone_repo(remote_url)
    repo_dir = str(work.path)
    repo_path = Path(repo_dir)

    branch = f"{branch_prefix}/{slugify(task)}"
    create_branch(repo_dir, branch)

    # Build tools scoped to THIS cloned repo so the agent can read actual files
    @tool
    def read_file(relative_path: str) -> str:
        """Read a file from the repo. Pass a relative path like 'README.md' or 'src/utils.py'."""
        full = repo_path / relative_path
        if not full.exists():
            return f"File not found: {relative_path}"
        return full.read_text(errors="ignore")[:5000]

    @tool
    def list_files(subdirectory: str = ".") -> str:
        """List all files in the repo or a subdirectory. Pass '.' for the root."""
        base = repo_path / subdirectory
        if not base.exists():
            return f"Directory not found: {subdirectory}"
        files = [
            str(p.relative_to(repo_path))
            for p in base.rglob("*")
            if p.is_file() and ".git" not in p.parts
        ]
        return "\n".join(files[:50])

    # Build a fresh agent with tools scoped to this repo
    model = ChatOpenAI(
        model=os.getenv("EDGE_CODING_MODEL", "openai/gpt-4o-mini"),
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL"),
    )
    agent = create_react_agent(
        model=model,
        tools=[read_file, list_files],
        prompt=EDGE_CODING_PROMPT,
    )

    # Ask agent for concrete file changes
    content = (
        f"repo_root: {repo_root_hint or '.'}\n"
        f"task: {task}\n"
        f"language: {language}\n"
        f"Use the list_files tool to explore the repo and read_file to read any files you need before making changes.\n"
    )

    resp = agent.invoke({"messages": [{"role": "user", "content": content}]})
    raw = resp["messages"][-1].content
    payload = load_edge_coding_json(raw)

    if "files" not in payload or not isinstance(payload["files"], list):
        raise RepoOpError(f"Agent output missing files[]. Output was:\n{raw}")

    written = apply_files(repo_dir, payload["files"])
    summary = payload.get("summary", "")

    commit_msg = f"{commit_message_prefix} {task}".strip()
    commit_all(repo_dir, commit_msg)
    push_branch(repo_dir, branch)

    if not keep_workdir:
        work.cleanup()

    return EdgeCodingResult(branch=branch, repo_dir=repo_dir, summary=summary, written_files=written)