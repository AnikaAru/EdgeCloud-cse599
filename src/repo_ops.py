import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


class RepoOpError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: str | None = None) -> str:
    p = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if p.returncode != 0:
        raise RepoOpError(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p.stdout


def slugify(s: str, max_len: int = 48) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:max_len] or "task"


@dataclass
class RepoWorkdir:
    path: Path

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


def clone_repo(remote_url: str, parent_dir: str | None = None) -> RepoWorkdir:
    base = Path(parent_dir) if parent_dir else Path(tempfile.gettempdir())
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    workdir = base / f"edgecloud-work-{ts}"
    _run(["git", "clone", remote_url, str(workdir)])
    return RepoWorkdir(path=workdir)


def create_branch(repo_dir: str, branch_name: str) -> None:
    _run(["git", "checkout", "-b", branch_name], cwd=repo_dir)


def apply_files(repo_dir: str, files: Iterable[dict]) -> list[str]:
    written: list[str] = []
    for f in files:
        rel = f.get("path")
        content = f.get("content")
        if not rel or content is None:
            raise RepoOpError(f"Invalid file entry (need path+content): {f}")
        rel_path = Path(rel)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise RepoOpError(f"Refusing unsafe path: {rel}")
        abs_path = Path(repo_dir) / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content, encoding="utf-8")
        written.append(str(rel_path))
    return written


def commit_all(repo_dir: str, message: str) -> None:
    _run(["git", "add", "-A"], cwd=repo_dir)
    # If nothing to commit, git commit exits non-zero. Detect and skip.
    status = _run(["git", "status", "--porcelain"], cwd=repo_dir)
    if status.strip() == "":
        return
    _run(["git", "commit", "-m", message], cwd=repo_dir)


def push_branch(repo_dir: str, branch_name: str, remote: str = "origin") -> None:
    _run(["git", "push", "-u", remote, branch_name], cwd=repo_dir)


def load_edge_coding_json(text: str) -> dict:
    """Parses the edge_coding_agent output.

    The agent is instructed to return strict JSON, but models sometimes wrap it.
    This function extracts the first top-level JSON object.
    """
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best-effort extraction
        m = re.search(r"\{[\s\S]*\}\s*$", text)
        if not m:
            raise RepoOpError(f"Could not parse JSON from agent output. Output was:\n{text}")
        return json.loads(m.group(0))
