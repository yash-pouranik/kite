import httpx
import logging
from typing import Dict, Any, Optional, List
from services.github_service import GitHubGitOpsService

logger = logging.getLogger("cyberwar.tools.ci_issues")

git_service = GitHubGitOpsService()

async def check_github_ci_status(
    branch_or_commit: Optional[str] = None,
    target_repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Checks the GitHub Actions CI / test workflow status for a branch or commit SHA.
    """
    token, owner, repo = git_service._get_credentials(target_repo)
    if not token or not owner or not repo:
        return {
            "status": "error",
            "error": "GITHUB_TOKEN and target repo (owner/repo) must be configured to check CI status."
        }

    ref = branch_or_commit or "main"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kite-SecOps-Agent/1.0"
    }

    url = f"{git_service.base_url}/repos/{owner}/{repo}/commits/{ref}/check-runs"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                total = data.get("total_count", 0)
                runs = data.get("check_runs", [])
                
                check_summaries = []
                all_passing = True
                for r in runs:
                    conclusion = r.get("conclusion")
                    status = r.get("status")
                    if conclusion != "success":
                        all_passing = False
                    check_summaries.append({
                        "name": r.get("name"),
                        "status": status,
                        "conclusion": conclusion,
                        "html_url": r.get("html_url")
                    })

                return {
                    "status": "success",
                    "repo": f"{owner}/{repo}",
                    "ref": ref,
                    "total_checks": total,
                    "all_passing": all_passing if total > 0 else True,
                    "checks": check_summaries
                }
            else:
                return {
                    "status": "error",
                    "error": f"GitHub API ({resp.status_code}): {resp.text}"
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}

async def sync_github_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    target_repo: Optional[str] = None
) -> Dict[str, Any]:
    """
    Opens a security tracking issue on GitHub linking the incident, CVE, and PR status.
    """
    token, owner, repo = git_service._get_credentials(target_repo)
    if not token or not owner or not repo:
        return {
            "status": "error",
            "error": "GITHUB_TOKEN and target repo (owner/repo) must be configured to create GitHub issues."
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Kite-SecOps-Agent/1.0"
    }

    url = f"{git_service.base_url}/repos/{owner}/{repo}/issues"
    payload = {
        "title": title,
        "body": body,
        "labels": labels or ["security", "kite-secops"]
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code == 201:
                data = resp.json()
                return {
                    "status": "success",
                    "issue_number": data.get("number"),
                    "issue_url": data.get("html_url"),
                    "title": data.get("title")
                }
            else:
                return {
                    "status": "error",
                    "error": f"Failed to create GitHub issue ({resp.status_code}): {resp.text}"
                }
        except Exception as e:
            return {"status": "error", "error": str(e)}
