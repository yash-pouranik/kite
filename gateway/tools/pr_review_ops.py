import os
import re
import base64
import time
import httpx
import logging
from typing import Dict, Any, Optional, List
from services.github_service import GitHubGitOpsService
from tools.git_ops import _run_git_cmd, _resolve_repo_path

logger = logging.getLogger("cyberwar.tools.pr_review")

git_service = GitHubGitOpsService()

async def fetch_pr_diff_and_files(
    pr_number: int,
    target_repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    PR / MR Diff & File Fetcher:
    Retrieves added, modified, or deleted files, line-by-line diffs,
    and commit histories for a Pull Request / Merge Request.
    """
    token, owner, repo = git_service._get_credentials(target_repo)
    if not token or not owner or not repo:
        return {
            "status": "error",
            "error": "GITHUB_TOKEN and target repo (owner/repo) must be configured to fetch PR diffs."
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kite-SecOps-Agent/1.0"
    }

    base_api = f"{git_service.base_url}/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # 1. Fetch PR details
            pr_res = await client.get(f"{base_api}/pulls/{pr_number}", headers=headers)
            if pr_res.status_code == 404:
                return {"status": "error", "error": f"Pull Request #{pr_number} not found in {owner}/{repo}."}
            elif pr_res.status_code != 200:
                return {"status": "error", "error": f"Failed to fetch PR #{pr_number}: {pr_res.text}"}
            
            pr_data = pr_res.json()

            # 2. Fetch changed files list with additions, deletions, status, and patch diffs
            files_res = await client.get(f"{base_api}/pulls/{pr_number}/files", headers=headers)
            changed_files = []
            if files_res.status_code == 200:
                for f in files_res.json():
                    changed_files.append({
                        "filename": f.get("filename"),
                        "status": f.get("status"), # added, modified, removed
                        "additions": f.get("additions", 0),
                        "deletions": f.get("deletions", 0),
                        "changes": f.get("changes", 0),
                        "patch": f.get("patch", "")
                    })

            # 3. Fetch commit history
            commits_res = await client.get(f"{base_api}/pulls/{pr_number}/commits", headers=headers)
            commit_history = []
            if commits_res.status_code == 200:
                for c in commits_res.json():
                    commit_history.append({
                        "sha": c.get("sha", "")[:8],
                        "author": c.get("commit", {}).get("author", {}).get("name", "Unknown"),
                        "message": c.get("commit", {}).get("message", "").strip(),
                        "date": c.get("commit", {}).get("author", {}).get("date", "")
                    })

            # 4. Fetch raw unified diff
            diff_headers = dict(headers)
            diff_headers["Accept"] = "application/vnd.github.v3.diff"
            diff_res = await client.get(f"{base_api}/pulls/{pr_number}", headers=diff_headers)
            unified_diff = diff_res.text if diff_res.status_code == 200 else ""

            return {
                "status": "success",
                "repo": f"{owner}/{repo}",
                "pr_number": pr_number,
                "title": pr_data.get("title"),
                "author": pr_data.get("user", {}).get("login"),
                "state": pr_data.get("state"),
                "head_branch": pr_data.get("head", {}).get("ref"),
                "base_branch": pr_data.get("base", {}).get("ref"),
                "changed_files_count": len(changed_files),
                "total_additions": pr_data.get("additions", 0),
                "total_deletions": pr_data.get("deletions", 0),
                "files": changed_files,
                "commit_count": len(commit_history),
                "commits": commit_history,
                "unified_diff": unified_diff[:50000] # Safe cap
            }

        except Exception as e:
            logger.error(f"Error fetching PR #{pr_number} diff: {e}")
            return {"status": "error", "error": str(e)}

async def post_pr_review_and_comment(
    pr_number: int,
    body: str,
    event: Optional[str] = "COMMENT", # COMMENT, APPROVE, REQUEST_CHANGES
    comments: Optional[List[Dict[str, Any]]] = None, # [{"path": "file.py", "line": 10, "body": "..."}]
    labels: Optional[List[str]] = None,
    target_repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Comment & Review Writer:
    Posts inline code comments, summary reviews, labels, or approval/request-changes status to a PR.
    """
    token, owner, repo = git_service._get_credentials(target_repo)
    if not token or not owner or not repo:
        return {
            "status": "error",
            "error": "GITHUB_TOKEN and target repo (owner/repo) must be configured to post PR reviews."
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kite-SecOps-Agent/1.0"
    }

    base_api = f"{git_service.base_url}/repos/{owner}/{repo}"

    event_upper = (event or "COMMENT").upper()
    if event_upper not in ["COMMENT", "APPROVE", "REQUEST_CHANGES"]:
        event_upper = "COMMENT"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            # 1. Post Pull Request Review (with optional inline comments)
            review_payload = {
                "body": body,
                "event": event_upper
            }
            if comments:
                formatted_comments = []
                for c in comments:
                    if isinstance(c, dict) and "path" in c and "body" in c:
                        fc = {
                            "path": c["path"],
                            "body": c["body"]
                        }
                        if "line" in c:
                            fc["line"] = int(c["line"])
                        if "side" in c:
                            fc["side"] = c["side"] # LEFT or RIGHT
                        formatted_comments.append(fc)
                if formatted_comments:
                    review_payload["comments"] = formatted_comments

            review_res = await client.post(
                f"{base_api}/pulls/{pr_number}/reviews",
                headers=headers,
                json=review_payload
            )

            review_id = None
            review_url = None
            if review_res.status_code in [200, 201]:
                r_json = review_res.json()
                review_id = r_json.get("id")
                review_url = r_json.get("html_url")
            else:
                # If reviews endpoint fails (e.g. self-approval restriction), fallback to issue comment
                comment_res = await client.post(
                    f"{base_api}/issues/{pr_number}/comments",
                    headers=headers,
                    json={"body": f"**[Review: {event_upper}]**\n\n{body}"}
                )
                if comment_res.status_code in [200, 201]:
                    review_url = comment_res.json().get("html_url")
                else:
                    return {"status": "error", "error": f"Failed to post review: {review_res.text}"}

            # 2. Attach labels if provided
            applied_labels = []
            if labels and isinstance(labels, list):
                label_res = await client.post(
                    f"{base_api}/issues/{pr_number}/labels",
                    headers=headers,
                    json={"labels": labels}
                )
                if label_res.status_code in [200, 201]:
                    applied_labels = [l.get("name") if isinstance(l, dict) else str(l) for l in label_res.json()]

            return {
                "status": "success",
                "repo": f"{owner}/{repo}",
                "pr_number": pr_number,
                "review_id": review_id,
                "event": event_upper,
                "review_url": review_url,
                "inline_comments_count": len(comments or []),
                "labels_applied": applied_labels
            }

        except Exception as e:
            logger.error(f"Error posting review on PR #{pr_number}: {e}")
            return {"status": "error", "error": str(e)}

async def manage_branch_and_commit(
    action: str, # create_branch, checkout_branch, commit_and_push, update_branch
    branch_name: str,
    commit_message: Optional[str] = None,
    files_to_commit: Optional[List[Dict[str, str]]] = None, # [{"path": "file.py", "content": "..."}]
    base_branch: Optional[str] = None,
    push_remote: bool = True,
    repo_dir: Optional[str] = None,
    target_repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Branch & Commit Manager:
    Creates, checks out, pushes, or updates branches and commits fixes directly to the PR.
    Seamlessly works via local git on mounted volume or remote GitHub GitOps API.
    """
    action_clean = action.lower().strip()
    target_path = _resolve_repo_path(repo_dir)

    # Mode A: Native local Git repository available
    if os.path.exists(os.path.join(target_path, ".git")):
        try:
            if action_clean in ["create_branch", "checkout_branch"]:
                # Check if branch exists
                b_check = _run_git_cmd(["branch", "--list", branch_name], target_path)
                if branch_name in b_check.get("stdout", ""):
                    res = _run_git_cmd(["checkout", branch_name], target_path)
                else:
                    base = base_branch or "main"
                    res = _run_git_cmd(["checkout", "-b", branch_name], target_path)
                return {
                    "status": "success" if res.get("status") == "success" else "failed",
                    "action": action_clean,
                    "branch": branch_name,
                    "mode": "local_git",
                    "details": res.get("stdout") or res.get("stderr")
                }

            elif action_clean in ["commit_and_push", "update_branch"]:
                # 1. Checkout target branch
                _run_git_cmd(["checkout", branch_name], target_path)

                # 2. Write files if provided
                written_files = []
                if files_to_commit and isinstance(files_to_commit, list):
                    for f in files_to_commit:
                        if isinstance(f, dict) and "path" in f and "content" in f:
                            full_file_path = os.path.join(target_path, f["path"])
                            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                            with open(full_file_path, "w", encoding="utf-8") as file_out:
                                file_out.write(f["content"])
                            written_files.append(f["path"])

                # 3. Stage changes
                _run_git_cmd(["add", "-A"], target_path)

                # 4. Commit
                msg = commit_message or f"kite: auto-commit fixes on {branch_name}"
                commit_res = _run_git_cmd(["commit", "-m", msg], target_path)

                # 5. Push if requested
                push_info = "skipped"
                if push_remote:
                    push_res = _run_git_cmd(["push", "origin", branch_name], target_path)
                    push_info = "pushed" if push_res.get("status") == "success" else f"push_failed: {push_res.get('stderr')}"

                # 6. Retrieve latest commit SHA
                head_sha_res = _run_git_cmd(["rev-parse", "--short", "HEAD"], target_path)
                head_sha = head_sha_res.get("stdout", "").strip()

                return {
                    "status": "success",
                    "action": action_clean,
                    "branch": branch_name,
                    "commit_sha": head_sha,
                    "commit_message": msg,
                    "files_committed": written_files,
                    "push_status": push_info,
                    "mode": "local_git"
                }

        except Exception as e:
            logger.error(f"Error in local git branch/commit manager: {e}")
            return {"status": "error", "error": str(e)}

    # Mode B: Remote GitHub API GitOps fallback
    token, owner, repo = git_service._get_credentials(target_repo)
    if not token or not owner or not repo:
        return {
            "status": "error",
            "error": "No local .git directory found and GITHUB_TOKEN is not configured for remote git operations."
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kite-SecOps-Agent/1.0"
    }
    base_api = f"{git_service.base_url}/repos/{owner}/{repo}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if action_clean in ["create_branch", "checkout_branch"]:
                # Get base SHA
                base = base_branch or "main"
                ref_res = await client.get(f"{base_api}/git/ref/heads/{base}", headers=headers)
                if ref_res.status_code != 200:
                    return {"status": "error", "error": f"Failed to resolve base branch '{base}': {ref_res.text}"}
                base_sha = ref_res.json()["object"]["sha"]

                create_ref = await client.post(
                    f"{base_api}/git/refs",
                    headers=headers,
                    json={"ref": f"refs/heads/{branch_name}", "sha": base_sha}
                )
                if create_ref.status_code in [200, 201]:
                    return {
                        "status": "success",
                        "action": action_clean,
                        "branch": branch_name,
                        "base_branch": base,
                        "mode": "github_api"
                    }
                elif create_ref.status_code == 422:
                    return {
                        "status": "success",
                        "action": action_clean,
                        "branch": branch_name,
                        "note": "Branch already exists on remote.",
                        "mode": "github_api"
                    }
                else:
                    return {"status": "error", "error": f"Failed to create branch: {create_ref.text}"}

            elif action_clean in ["commit_and_push", "update_branch"]:
                msg = commit_message or f"kite: auto-commit fixes on {branch_name}"
                committed = []
                if files_to_commit:
                    for f in files_to_commit:
                        f_path = f["path"]
                        f_content = f["content"]
                        # Check existing SHA
                        file_sha = None
                        get_f = await client.get(f"{base_api}/contents/{f_path}?ref={branch_name}", headers=headers)
                        if get_f.status_code == 200:
                            file_sha = get_f.json().get("sha")

                        b64 = base64.b64encode(f_content.encode("utf-8")).decode("utf-8")
                        payload = {"message": msg, "content": b64, "branch": branch_name}
                        if file_sha:
                            payload["sha"] = file_sha

                        put_res = await client.put(f"{base_api}/contents/{f_path}", headers=headers, json=payload)
                        if put_res.status_code in [200, 201]:
                            committed.append(f_path)

                return {
                    "status": "success",
                    "action": action_clean,
                    "branch": branch_name,
                    "files_committed": committed,
                    "commit_message": msg,
                    "mode": "github_api"
                }

            return {"status": "error", "error": f"Unsupported branch action: '{action}'"}

        except Exception as e:
            logger.error(f"Error managing remote branch/commit: {e}")
            return {"status": "error", "error": str(e)}
