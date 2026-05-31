import os
from dataclasses import dataclass

from src.edge_coding_agent import agent as edge_coding_agent
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
    """
    work = clone_repo(remote_url)
    repo_dir = str(work.path)

    branch = f"{branch_prefix}/{slugify(task)}"
    create_branch(repo_dir, branch)

    # Ask agent for concrete file changes
    content = (
        f"repo_root: {repo_root_hint or '.'}\n"
        f"task: {task}\n"
        f"language: {language}\n"
    )
    resp = edge_coding_agent.invoke({"messages": [{"role": "user", "content": content}]})
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
