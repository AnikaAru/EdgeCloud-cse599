import os
import shutil
import subprocess
from pathlib import Path


REPOS_DIR = Path("repos")


def clone_or_update_repo(repo_url: str) -> str:
    REPOS_DIR.mkdir(exist_ok=True)

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = REPOS_DIR / repo_name

    if repo_path.exists():
        subprocess.run(["git", "-C", str(repo_path), "pull"], check=False)
    else:
        subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)

    return str(repo_path)


def read_repo_summary(repo_path: str, max_files: int = 20) -> str:
    repo = Path(repo_path)
    allowed = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".md", ".json"}

    chunks = []
    count = 0

    for path in repo.rglob("*"):
        if count >= max_files:
            break
        if ".git" in path.parts or path.is_dir():
            continue
        if path.suffix not in allowed:
            continue

        try:
            text = path.read_text(errors="ignore")[:3000]
            chunks.append(f"\n--- FILE: {path.relative_to(repo)} ---\n{text}")
            count += 1
        except Exception:
            pass

    return "\n".join(chunks)


def github_agent(repo_url: str) -> dict:
    repo_path = clone_or_update_repo(repo_url)
    repo_context = read_repo_summary(repo_path)

    return {
        "repo_path": repo_path,
        "repo_context": repo_context,
    }