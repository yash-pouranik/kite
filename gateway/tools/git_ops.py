import os
import re
import subprocess
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("cyberwar.tools.git")

DEFAULT_TARGET_REPO = os.getenv("TARGET_REPO_PATH", "/app/target_repo")

# Auto-configure safe directory globally on module load
try:
    subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=False)
except Exception:
    pass

def _resolve_repo_path(repo_dir: Optional[str] = None) -> str:
    """Resolves target repository path across container and local environments."""
    if repo_dir and os.path.exists(repo_dir):
        return repo_dir
    if os.path.exists(DEFAULT_TARGET_REPO):
        return DEFAULT_TARGET_REPO
    host_path = os.getenv("HOST_REPO_PATH")
    if host_path and os.path.exists(host_path):
        return host_path
    # Fallback to current repository directory if running locally
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _run_git_cmd(args: List[str], repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """Safely executes a git CLI command in the target repo directory."""
    target_path = _resolve_repo_path(repo_dir)
    if not os.path.exists(target_path):
        return {
            "status": "error",
            "error": f"Repository directory not found at: {target_path}"
        }

    try:
        # -c safe.directory=* prevents dubious ownership errors when host directory
        # is mounted into Docker with a different user UID (e.g. root vs ubuntu)
        cmd = ["git", "-c", "safe.directory=*"] + args
        proc = subprocess.run(
            cmd,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=15
        )
        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "repo_path": target_path
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Git command timed out after 15s"}
    except FileNotFoundError:
        return {"status": "error", "error": "Git binary not found in environment."}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_git_remote_info(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes 'git remote -v' to detect remote origin URLs, GitHub owner, and repo name.
    """
    res = _run_git_cmd(["remote", "-v"], repo_dir)
    if res.get("status") != "success":
        return res

    output = res.get("stdout", "")
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    remotes = {}
    owner, repo_name = None, None

    for line in lines:
        parts = line.split()
        if len(parts) >= 2:
            name, url = parts[0], parts[1]
            remotes[name] = url
            # Extract owner and repo from URL (handles https://, git@, ssh host aliases)
            # e.g. https://github.com/yash-pouranik/mcp-gateway-k8s.git
            # e.g. git@github-personal:yash-pouranik/kite.git
            match = re.search(r"[:/]([a-zA-Z0-9_-]+)/([a-zA-Z0-9_\-\.]+?)(?:\.git)?$", url)
            if match and not owner:
                owner = match.group(1)
                repo_name = match.group(2)

    return {
        "status": "success",
        "repo_path": res.get("repo_path"),
        "remotes": remotes,
        "detected_owner": owner,
        "detected_repo": repo_name,
        "github_url": f"https://github.com/{owner}/{repo_name}" if (owner and repo_name) else None
    }

def get_git_status(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes 'git status --porcelain -b' to inspect active branch and pending changes.
    """
    res = _run_git_cmd(["status", "--porcelain", "-b"], repo_dir)
    if res.get("status") != "success":
        return res

    output = res.get("stdout", "")
    lines = output.splitlines()
    branch = "unknown"
    modified = []
    untracked = []
    staged = []

    if lines and lines[0].startswith("##"):
        branch_line = lines[0][3:].strip()
        branch = branch_line.split("...")[0].strip()
        lines = lines[1:]

    for line in lines:
        if len(line) < 3:
            continue
        index_status = line[0]
        worktree_status = line[1]
        file_path = line[3:].strip()

        if index_status in ["M", "A", "D", "R"]:
            staged.append({"path": file_path, "status": index_status})
        if worktree_status == "M":
            modified.append(file_path)
        elif index_status == "?" and worktree_status == "?":
            untracked.append(file_path)

    return {
        "status": "success",
        "repo_path": res.get("repo_path"),
        "branch": branch,
        "is_clean": len(modified) == 0 and len(untracked) == 0 and len(staged) == 0,
        "staged_changes": staged,
        "modified_files": modified,
        "untracked_files": untracked
    }

def get_git_diff(staged: bool = False, file_path: Optional[str] = None, repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes 'git diff' to review pending uncommitted or staged changes.
    """
    args = ["diff"]
    if staged:
        args.append("--staged")
    if file_path:
        args.extend(["--", file_path])

    res = _run_git_cmd(args, repo_dir)
    if res.get("status") != "success":
        return res

    diff_text = res.get("stdout", "")
    return {
        "status": "success",
        "has_changes": bool(diff_text),
        "diff": diff_text if diff_text else "No diff found (working tree is clean)."
    }

def get_git_log(max_count: int = 5, repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes 'git log' to inspect the recent commit history with SHAs, authors, and messages.
    """
    res = _run_git_cmd(["log", f"-n{max_count}", "--pretty=format:%h|%an|%ad|%s", "--date=short"], repo_dir)
    if res.get("status") != "success":
        return res

    commits = []
    for line in res.get("stdout", "").splitlines():
        parts = line.split("|")
        if len(parts) >= 4:
            commits.append({
                "commit": parts[0],
                "author": parts[1],
                "date": parts[2],
                "message": parts[3]
            })

    return {
        "status": "success",
        "commit_count": len(commits),
        "recent_commits": commits
    }

def get_git_branches(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Lists local and remote branches and highlights the currently active branch.
    """
    res = _run_git_cmd(["branch", "-a"], repo_dir)
    if res.get("status") != "success":
        return res

    branches = []
    current_branch = None
    for line in res.get("stdout", "").splitlines():
        line_clean = line.strip()
        is_current = line.startswith("*")
        b_name = line_clean.lstrip("* ").strip()
        branches.append(b_name)
        if is_current:
            current_branch = b_name

    return {
        "status": "success",
        "current_branch": current_branch,
        "all_branches": branches
    }
