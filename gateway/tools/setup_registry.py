import json
import logging
from typing import Dict, Any, Optional, List
from config import settings
from tools.tool_registry import registry
from tools.web_discovery import crawl_and_discover_target
from services.knowledge_manager import KnowledgeBaseManager
from tools.scanner_runner import SandboxedScannerRunner
from tools.exploit_runner import SafeExploitToolkit
from services.virtual_patcher import NginxVirtualPatcher
from services.github_service import GitHubGitOpsService
from tools.verifier_suite import DualPathAuditSuite
from tools.repo_inspector import TargetRepoInspector
from tools.openapi_parser import OpenAPISchemaParser
from tools.git_ops import (
    get_git_remote_info,
    get_git_status,
    get_git_diff,
    get_git_log,
    get_git_branches
)
from tools.code_scanner import scan_codebase_sast, scan_codebase_secrets
from tools.dependency_scanner import scan_dependencies
from tools.log_inspector import tail_container_logs, check_service_health
from tools.test_runner import run_local_test_suite
from tools.ci_and_issues import check_github_ci_status, sync_github_issue
from tools.k8s_ops import get_k8s_pods, tail_k8s_logs
from tools.terminal_runner import execute_terminal_command

logger = logging.getLogger("cyberwar.tools.setup")

# Initialize underlying service instances
kb_manager = KnowledgeBaseManager()
scanner_runner = SandboxedScannerRunner()
exploit_toolkit = SafeExploitToolkit()
virtual_patcher = NginxVirtualPatcher()
github_service = GitHubGitOpsService()
verifier_suite = DualPathAuditSuite(target_host=settings.TARGET_HOST or settings.TARGET_CONTAINER_NAME or "target-app")
repo_inspector = TargetRepoInspector()
openapi_parser = OpenAPISchemaParser()
default_target = settings.TARGET_HOST or settings.TARGET_CONTAINER_NAME or "target-app"

def register_all_tools():
    """Binds all 28 DevSecOps, Git, Kubernetes, and Terminal tools into the centralized registry."""

    # 1. Endpoint Web Discovery
    @registry.register(
        name="discover_target_endpoints",
        description="Crawls the target application web bundles, inspects HTTP response headers, and extracts live API routes and authentication endpoints.",
        parameters={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "The base URL or domain to crawl (defaults to configured TARGET_HOST)"}
            }
        }
    )
    async def handle_discover(target_url: Optional[str] = None):
        url = target_url or f"https://{default_target}"
        result = await crawl_and_discover_target(url)
        kb_manager.save_or_update_knowledge(
            category="api_inventory",
            data=result,
            agent_name="recon-bot",
            discovery_method="web_bundle_crawler"
        )
        return result

    # 2. Read Project File
    @registry.register(
        name="read_project_file",
        description="Reads source code or project documentation files from the mounted target application repository (e.g. package.json, README.md, Dockerfile, server configs).",
        parameters={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Relative path to file in repo, e.g. 'package.json', 'README.md', 'src/index.ts'"}
            },
            "required": ["file_path"]
        }
    )
    def handle_read_file(file_path: str = "package.json"):
        return repo_inspector.read_file(file_path=file_path)

    # 3. List Project Files
    @registry.register(
        name="list_project_files",
        description="Lists the files and folder structure in the target repository to see what files are available to inspect."
    )
    def handle_list_files():
        return repo_inspector.list_files()

    # 4. Parse OpenAPI / Swagger
    @registry.register(
        name="parse_openapi_schema",
        description="Ingests and parses OpenAPI/Swagger specifications from public endpoints or local repo files. Returns exact endpoint routes, HTTP methods, and body parameter schemas.",
        parameters={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "Target base URL (defaults to configured target)"}
            }
        }
    )
    async def handle_openapi(target_url: Optional[str] = None):
        target = target_url or f"https://{default_target}"
        return await openapi_parser.fetch_and_parse_schema(base_url=target)

    # 5. Read Knowledge Base
    @registry.register(
        name="read_knowledge_base",
        description="Reads persistent knowledge files (target_overview, auth_mechanisms, api_inventory) to check discovered intelligence and completeness score.",
        parameters={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["target_overview", "auth_mechanisms", "api_inventory"],
                    "description": "Category of knowledge to retrieve."
                }
            },
            "required": ["category"]
        }
    )
    def handle_read_kb(category: str):
        kb_data = kb_manager.get_knowledge(category)
        return kb_data or {"status": "empty", "completeness": 0, "message": "No data discovered yet."}

    # 6. Update Knowledge Base
    @registry.register(
        name="update_knowledge_base",
        description="Updates or appends verified project details (such as confirmed project purpose, architecture notes, or tech stack) into persistent memory.",
        parameters={
            "type": "object",
            "properties": {
                "category": {"type": "string", "enum": ["target_overview", "auth_mechanisms", "api_inventory"], "description": "Knowledge category to update."},
                "key": {"type": "string", "description": "Field or section name to update."},
                "value": {"type": "string", "description": "Information or summary content to store."}
            },
            "required": ["category", "key", "value"]
        }
    )
    def handle_update_kb(category: str, key: str, value: str):
        existing = kb_manager.get_knowledge(category) or {}
        existing[key] = value
        kb_manager.save_or_update_knowledge(
            category=category,
            data=existing,
            agent_name="human_collaborator",
            discovery_method="engineer_input"
        )
        return {"status": "updated", "category": category, "key": key}

    # 7. Run Security Scan
    @registry.register(
        name="run_security_scan",
        description="Executes sandboxed security scans and active HTTP security header / auth hardening checks against an asset or endpoint.",
        parameters={
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target hostname, IP, or full URL (defaults to configured target)"}
            }
        }
    )
    async def handle_security_scan(target: Optional[str] = None):
        tgt = target or default_target
        target_url = tgt if tgt.startswith("http") else f"https://{tgt}"
        return await scanner_runner.run_nuclei_scan(target_url)

    # 8. Verify Safe Exploit Probe
    @registry.register(
        name="verify_safe_exploit_probe",
        description="Fires a non-destructive, read-only proof-of-concept verification probe to confirm if an endpoint or parameter has active security flaws (e.g. SQLi / auth bypass).",
        parameters={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "The target endpoint path, e.g. /api/auth/login"},
                "payload": {"type": "string", "description": "The harmless test payload string, e.g. ' OR 1=1 --"}
            },
            "required": ["endpoint", "payload"]
        }
    )
    async def handle_exploit(endpoint: str = "/api/auth/login", payload: str = "' OR 1=1 --"):
        return await exploit_toolkit.verify_sqli_probe(endpoint=endpoint, payload=payload)

    # 9. Apply Virtual Shield
    @registry.register(
        name="apply_virtual_shield",
        description="Deploys a zero-downtime Nginx reverse proxy virtual patch (regex inspection rule) and reloads Nginx dynamically in 5ms.",
        parameters={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "The endpoint to protect, e.g. /api/auth/login"}
            },
            "required": ["endpoint"]
        }
    )
    async def handle_apply_patch(endpoint: str = "/api/auth/login"):
        return await virtual_patcher.apply_virtual_patch(endpoint=endpoint)

    # 10. Rollback Virtual Shield
    @registry.register(
        name="rollback_virtual_shield",
        description="1-Click Safety Rollback: Instantly deactivates the virtual patch, deletes the WAF rule, and hot-reloads Nginx. Restores traffic to original pre-incident state.",
        parameters={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Endpoint to rollback, e.g. /api/auth/login"}
            }
        }
    )
    async def handle_rollback_patch(endpoint: Optional[str] = None):
        return await virtual_patcher.rollback_virtual_patch()

    # 11. Dual-Track Remediation Regression Verifier
    @registry.register(
        name="verify_dual_track_remediation",
        description="Performs independent regression audit: tests that legitimate customer traffic returns 200 OK while exploit payloads are blocked with 403 Forbidden.",
        parameters={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Endpoint to audit, e.g. /api/auth/login"}
            },
            "required": ["endpoint"]
        }
    )
    async def handle_verify_dual(endpoint: str = "/api/auth/login"):
        return await verifier_suite.execute_dual_path_audit(endpoint=endpoint)

    # 12. Git Remote Info
    @registry.register(
        name="get_git_remote_info",
        description="Executes 'git remote -v' on the mounted target repository to extract origin URLs, GitHub owner, and repo name.",
        parameters={
            "type": "object",
            "properties": {
                "repo_dir": {"type": "string", "description": "Optional repository path (defaults to /app/target_repo)"}
            }
        }
    )
    def handle_git_remote(repo_dir: Optional[str] = None):
        return get_git_remote_info(repo_dir=repo_dir)

    # 13. Git Status
    @registry.register(
        name="get_git_status",
        description="Executes 'git status --porcelain -b' to inspect active branch, untracked files, modified files, and staged changes in the target repo.",
        parameters={
            "type": "object",
            "properties": {
                "repo_dir": {"type": "string", "description": "Optional repository path"}
            }
        }
    )
    def handle_git_status(repo_dir: Optional[str] = None):
        return get_git_status(repo_dir=repo_dir)

    # 14. Git Diff
    @registry.register(
        name="get_git_diff",
        description="Executes 'git diff' to review exact pending code changes or staged modifications in the target repository.",
        parameters={
            "type": "object",
            "properties": {
                "staged": {"type": "boolean", "description": "Whether to check staged changes (--staged)"},
                "file_path": {"type": "string", "description": "Optional specific file path to diff"}
            }
        }
    )
    def handle_git_diff(staged: bool = False, file_path: Optional[str] = None):
        return get_git_diff(staged=staged, file_path=file_path)

    # 15. Git Log
    @registry.register(
        name="get_git_log",
        description="Executes 'git log' to inspect the recent commit history, SHAs, authors, dates, and commit messages.",
        parameters={
            "type": "object",
            "properties": {
                "max_count": {"type": "integer", "description": "Number of recent commits to return (default 5)"}
            }
        }
    )
    def handle_git_log(max_count: int = 5):
        return get_git_log(max_count=max_count)

    # 16. Git Branches
    @registry.register(
        name="get_git_branches",
        description="Lists all local and remote branches in the target repository and highlights the currently active branch.",
        parameters={
            "type": "object",
            "properties": {}
        }
    )
    def handle_git_branches():
        return get_git_branches()

    # 17. Real GitHub PR Creator
    @registry.register(
        name="create_github_pr",
        description="Opens a REAL GitHub Pull Request with custom title, body, and branch. Never returns mock or simulated URLs.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "The title of the Pull Request"},
                "description": {"type": "string", "description": "The markdown body / description of the Pull Request"},
                "branch_name": {"type": "string", "description": "Optional branch name (e.g. 'kite/test-pr' or 'secops/fix-sqli')"},
                "target_repo": {"type": "string", "description": "Optional target repository in 'owner/repo' or URL format"},
                "base_branch": {"type": "string", "description": "Base branch to merge into (defaults to 'main')"}
            },
            "required": ["title"]
        }
    )
    async def handle_create_pr(
        title: str,
        description: Optional[str] = "",
        branch_name: Optional[str] = None,
        target_repo: Optional[str] = None,
        base_branch: Optional[str] = None
    ):
        return await github_service.create_pull_request(
            title=title,
            body=description or f"Created by Kite SecOps Teammate for {title}",
            branch_name=branch_name,
            target_repo=target_repo,
            base_branch=base_branch
        )

    # 18. Code SAST Scanner
    @registry.register(
        name="scan_codebase_sast",
        description="Executes Static Application Security Testing (SAST) on the codebase. Detects raw SQL concatenation, disabled SSL verification, wildcard CORS, and dynamic eval.",
        parameters={
            "type": "object",
            "properties": {
                "repo_dir": {"type": "string", "description": "Optional repository path to scan"}
            }
        }
    )
    def handle_sast(repo_dir: Optional[str] = None):
        return scan_codebase_sast(repo_dir=repo_dir)

    # 19. Code Secret Scanner
    @registry.register(
        name="scan_codebase_secrets",
        description="Scans source code and configs for accidentally exposed credentials: AWS keys, OpenAI tokens, Google API keys, JWT secrets, and private keys.",
        parameters={
            "type": "object",
            "properties": {
                "repo_dir": {"type": "string", "description": "Optional repository path to scan"}
            }
        }
    )
    def handle_secrets(repo_dir: Optional[str] = None):
        return scan_codebase_secrets(repo_dir=repo_dir)

    # 20. Dependency Vulnerability Scanner (SCA)
    @registry.register(
        name="scan_dependencies",
        description="Executes Software Composition Analysis (SCA) on package.json or requirements.txt using the open OSV.dev database to detect vulnerable dependencies and safe upgrade versions.",
        parameters={
            "type": "object",
            "properties": {
                "manifest_file": {"type": "string", "description": "Manifest filename, e.g. 'package.json' or 'requirements.txt'"}
            }
        }
    )
    async def handle_sca(manifest_file: str = "package.json"):
        return await scan_dependencies(manifest_file=manifest_file)

    # 21. Tail Container Logs
    @registry.register(
        name="tail_container_logs",
        description="Tails live runtime logs from target Docker containers. Extracts recent error traces, unhandled exceptions, and 500 status codes.",
        parameters={
            "type": "object",
            "properties": {
                "container_name": {"type": "string", "description": "Container name to tail (defaults to TARGET_CONTAINER_NAME)"},
                "lines": {"type": "integer", "description": "Number of log lines to tail (default 50)"}
            }
        }
    )
    def handle_logs(container_name: Optional[str] = None, lines: int = 50):
        c_name = container_name or settings.TARGET_CONTAINER_NAME or "target-app"
        return tail_container_logs(container_name=c_name, lines=lines)

    # 22. Check Service Health & Latency
    @registry.register(
        name="check_service_health",
        description="Probes endpoint response latency, HTTP status code, server header, and service health.",
        parameters={
            "type": "object",
            "properties": {
                "target_url": {"type": "string", "description": "URL to probe (defaults to configured TARGET_HOST)"}
            }
        }
    )
    async def handle_health(target_url: Optional[str] = None):
        tgt = target_url or (default_target if default_target.startswith("http") else f"https://{default_target}")
        return await check_service_health(target_url=tgt)

    # 23. Local Test Suite Runner
    @registry.register(
        name="run_local_test_suite",
        description="Executes automated tests in the target repository before applying fixes or opening PRs. Detects package.json test scripts or pytest configurations automatically.",
        parameters={
            "type": "object",
            "properties": {
                "test_command": {"type": "string", "description": "Optional custom test command, e.g. 'npm test' or 'pytest'"}
            }
        }
    )
    def handle_test_suite(test_command: Optional[str] = None):
        return run_local_test_suite(test_command=test_command)

    # 24. GitHub Actions CI Status
    @registry.register(
        name="check_github_ci_status",
        description="Checks the GitHub Actions CI / test workflow status for a branch or commit SHA.",
        parameters={
            "type": "object",
            "properties": {
                "branch_or_commit": {"type": "string", "description": "Branch name or commit SHA to inspect (defaults to 'main')"},
                "target_repo": {"type": "string", "description": "Optional target repository in 'owner/repo' format"}
            }
        }
    )
    async def handle_ci_status(branch_or_commit: Optional[str] = None, target_repo: Optional[str] = None):
        return await check_github_ci_status(branch_or_commit=branch_or_commit, target_repo=target_repo)

    # 25. Sync GitHub Issue
    @registry.register(
        name="sync_github_issue",
        description="Opens a security tracking issue on GitHub linking the incident, CVE, and PR status.",
        parameters={
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Issue title"},
                "body": {"type": "string", "description": "Markdown body detailing incident, reproduction PoC, and patch status"},
                "labels": {"type": "array", "items": {"type": "string"}, "description": "Labels e.g. ['security', 'bug']"},
                "target_repo": {"type": "string", "description": "Optional repository in 'owner/repo' format"}
            },
            "required": ["title", "body"]
        }
    )
    async def handle_issue_sync(
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        target_repo: Optional[str] = None
    ):
        return await sync_github_issue(title=title, body=body, labels=labels, target_repo=target_repo)

    # 26. Kubernetes Pods Inspector
    @registry.register(
        name="get_k8s_pods",
        description="Lists active Kubernetes pods in the target cluster namespace. Shows pod names, phases, readiness, restart counts, and age.",
        parameters={
            "type": "object",
            "properties": {
                "namespace": {"type": "string", "description": "Target Kubernetes namespace (defaults to K8S_NAMESPACE in settings)"}
            }
        }
    )
    def handle_k8s_pods(namespace: Optional[str] = None):
        ns = namespace or settings.K8S_NAMESPACE or "default"
        return get_k8s_pods(namespace=ns)

    # 27. Kubernetes Live Pod Log Tailer
    @registry.register(
        name="tail_k8s_logs",
        description="Tails live runtime logs, stack traces, and 500 error outputs directly from a Kubernetes pod in the target namespace.",
        parameters={
            "type": "object",
            "properties": {
                "pod_name": {"type": "string", "description": "Pod name or prefix (e.g. 'gateway', 'dashboard')"},
                "namespace": {"type": "string", "description": "Kubernetes namespace (defaults to K8S_NAMESPACE in settings)"},
                "lines": {"type": "integer", "description": "Number of log lines to tail (default 50)"}
            }
        }
    )
    def handle_k8s_logs(pod_name: Optional[str] = None, namespace: Optional[str] = None, lines: int = 50):
        ns = namespace or settings.K8S_NAMESPACE or "default"
        p_name = pod_name or "gateway"
        return tail_k8s_logs(pod_name=p_name, namespace=ns, lines=lines)

    # 28. Governed Terminal Execution Tool
    @registry.register(
        name="execute_terminal_command",
        description="Executes arbitrary CLI commands (e.g. kubectl, git, docker, curl, npm, grep) under strict SecOps safety guardrails. Destructive commands (rm -rf, shutdown) and secret leakage (.env access) are blocked.",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The CLI command string to execute, e.g. 'kubectl get pods -n=gateway' or 'git status'"},
                "working_dir": {"type": "string", "description": "Optional working directory (defaults to mounted repository /app/target_repo)"}
            },
            "required": ["command"]
        }
    )
    def handle_terminal_exec(command: str, working_dir: Optional[str] = None):
        return execute_terminal_command(command=command, working_dir=working_dir)

    logger.info("Successfully registered all 28 DevSecOps, Git, Kubernetes, and Terminal tools in ToolRegistry.")
