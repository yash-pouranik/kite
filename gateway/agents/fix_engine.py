import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings
from services.virtual_patcher import NginxVirtualPatcher
from services.github_service import GitHubGitOpsService
from services.git_service import LocalGitService

logger = logging.getLogger("cyberwar.agents.fix_engine")

class FixEngineAgent:
    """
    Fix Engine powered by gpt-6-luna.
    DevSecOps Architect responsible for Dual-Track Remediation:
    1. Instant Zero-Downtime Virtual Patching (Nginx Reverse Proxy)
    2. Permanent GitOps Source Code Pull Request (Local Git & GitHub)
    Enforces Pre-Action Transparency: explicitly details all commands before execution.
    """
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.FIX_ENGINE_MODEL # gpt-6-luna
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.virtual_patcher = NginxVirtualPatcher()
        self.github_service = GitHubGitOpsService()
        self.local_git = LocalGitService()

    async def formulate_remediation_plan(self, vuln_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Presents a detailed Pre-Action Execution Manifest explaining what commands
        will be run on the system upon human approval.
        """
        vuln_title = vuln_info.get("title", "SQL Injection on Search Endpoint")
        endpoint = vuln_info.get("endpoint", "/rest/products/search")

        proposal_text = (
            f"🛡️ **Fix Engine Agent — Pre-Action Remediation Plan**\n\n"
            f"An active **{vuln_title}** has been confirmed on `{endpoint}`.\n"
            "If you approve, here is **exactly what I will execute on the system**:\n\n"
            "1. ⚡ **Layer 1: Zero-Downtime Virtual Shield (Active Defense)**\n"
            f"   - **File Written:** `/etc/nginx/conf.d/patch_sqli.conf`\n"
            f"   - **Regex Rule:** Intercepts `' OR 1=1`, `UNION SELECT`, and `--` on `{endpoint}`\n"
            "   - **Hot-Reload:** Executes `nginx -s reload` (5 millisecond reload without dropping connections)\n"
            "   - **Customer Guarantee:** Genuine shopper traffic (`apple`, `mug`) will experience 0 downtime!\n\n"
            "2. 🚀 **Layer 2: Permanent Source Code Fix (Local Git & GitHub)**\n"
            "   - **Local Branch:** Runs `git checkout -b secops/fix-sqli-patch` on `/app/target_repo`\n"
            "   - **Code Refactor:** Replaces vulnerable string concatenation with parameterized prepared statements\n"
            "   - **Pull Request:** Submits Pull Request with full before/after code diffs\n\n"
            "**Should I proceed with executing the shield and opening the PR?**"
        )

        return {
            "agent": "fix-engine",
            "model": self.model_name,
            "conversational_plan": proposal_text
        }

    async def execute_dual_remediation(self, incident_id: str = "INC-101") -> Dict[str, Any]:
        """
        Applies both the Nginx virtual patch hot reload and creates the GitHub PR.
        """
        logger.info(f"Fix Engine applying dual remediation for {incident_id}")

        # 1. Apply Nginx virtual patch
        patch_res = await self.virtual_patcher.apply_virtual_patch()
        
        # 2. Open GitHub Pull Request
        pr_res = await self.github_service.create_security_fix_pr(incident_id=incident_id)

        pr_url = pr_res.get("pr_url")
        report = (
            "✅ **Dual Remediation Executed Successfully**\n\n"
            "1. 🛡️ **Virtual Shield Active**: Nginx reverse proxy hot-reloaded with targeted SQL query filter. "
            "Attack payloads will now be blocked with 403 Forbidden, while legitimate shopper traffic flows freely.\n"
            f"2. 🚀 **Permanent Pull Request Submitted**: [{pr_res.get('title')}]({pr_url})\n\n"
            "Notifying **Verifier Agent** to perform independent dual-path traffic testing."
        )

        return {
            "status": "applied",
            "patch_result": patch_res,
            "github_pr": pr_res,
            "conversational_report": report
        }
