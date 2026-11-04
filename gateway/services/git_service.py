import os
import asyncio
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("cyberwar.services.git")

class LocalGitService:
    """
    Executes native git commands on the locally mounted target repository
    (/app/target_repo). Provides instant file inspection, branch creation,
    diffing, and committing without cloud API latency or rate limits.
    """
    def __init__(self, repo_path: str = "/app/target_repo"):
        self.repo_path = repo_path

    async def _run_git_cmd(self, args: List[str]) -> Dict[str, Any]:
        """
        Executes a git command inside the repository directory.
        """
        if not os.path.exists(self.repo_path):
            logger.warning(f"Target repository path {self.repo_path} does not exist. Using simulation mode.")
            return {"exit_code": 0, "stdout": "Simulated Git output", "stderr": ""}

        try:
            proc = await asyncio.create_subprocess_exec(
                "git", *args,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="ignore").strip(),
                "stderr": stderr.decode("utf-8", errors="ignore").strip()
            }
        except Exception as e:
            logger.error(f"Git execution error: {e}")
            return {"exit_code": 1, "stdout": "", "stderr": str(e)}

    async def find_file_for_endpoint(self, endpoint_keyword: str = "login") -> Optional[str]:
        """
        Searches the repository tree for files matching the endpoint name.
        """
        res = await self._run_git_cmd(["ls-files"])
        if res["exit_code"] != 0 or not res["stdout"]:
            # Fallback path
            return f"routes/{endpoint_keyword}.js"

        files = res["stdout"].splitlines()
        for f in files:
            if endpoint_keyword.lower() in f.lower():
                return f
        return files[0] if files else "routes/index.js"

    async def create_fix_branch(self, branch_name: str) -> Dict[str, Any]:
        """
        Creates and checks out a new security patch branch: git checkout -b <branch_name>
        """
        logger.info(f"Creating local Git branch: {branch_name}")
        return await self._run_git_cmd(["checkout", "-b", branch_name])

    async def get_diff(self) -> str:
        """
        Returns the uncommitted git diff of the repository.
        """
        res = await self._run_git_cmd(["diff"])
        return res.get("stdout", "")

    async def commit_fix(self, commit_message: str) -> Dict[str, Any]:
        """
        Stages and commits changes: git add -A && git commit -m <message>
        """
        await self._run_git_cmd(["add", "-A"])
        return await self._run_git_cmd(["commit", "-m", commit_message])
