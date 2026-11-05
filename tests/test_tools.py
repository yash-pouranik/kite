import asyncio
import os
import sys
import unittest

# Add gateway to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "gateway")))

from tools.tool_registry import registry
from tools.setup_registry import register_all_tools
from tools.git_ops import get_git_remote_info, get_git_status, get_git_log, get_git_branches
from tools.code_scanner import scan_codebase_sast, scan_codebase_secrets
from tools.dependency_scanner import scan_dependencies
from tools.test_runner import run_local_test_suite
from services.github_service import GitHubGitOpsService

class TestSecOpsTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all_tools()

    def test_01_tool_registry_registration(self):
        """Verifies that all 25 tools are successfully registered in ToolRegistry."""
        schemas = registry.get_schemas()
        tool_names = [s["function"]["name"] for s in schemas]
        self.assertGreaterEqual(len(tool_names), 25, f"Expected >= 25 tools, found {len(tool_names)}")

        # Check key tools exist
        required = [
            "discover_target_endpoints",
            "read_project_file",
            "list_project_files",
            "parse_openapi_schema",
            "get_git_remote_info",
            "get_git_status",
            "get_git_diff",
            "get_git_log",
            "get_git_branches",
            "create_github_pr",
            "scan_codebase_sast",
            "scan_codebase_secrets",
            "scan_dependencies",
            "tail_container_logs",
            "check_service_health",
            "run_local_test_suite",
            "check_github_ci_status",
            "sync_github_issue",
            "apply_virtual_shield",
            "rollback_virtual_shield"
        ]
        for req in required:
            self.assertIn(req, tool_names, f"Missing required tool: {req}")

    def test_02_git_operations(self):
        """Verifies Git status, log, branches, and remote parsing."""
        status = get_git_status()
        self.assertEqual(status["status"], "success")
        self.assertIn("branch", status)

        log = get_git_log(max_count=2)
        self.assertEqual(log["status"], "success")
        self.assertGreater(log["commit_count"], 0)

        remotes = get_git_remote_info()
        self.assertEqual(remotes["status"], "success")

        branches = get_git_branches()
        self.assertEqual(branches["status"], "success")

    def test_03_code_sast_and_secrets(self):
        """Verifies SAST and Secret scanners run cleanly across files."""
        sast = scan_codebase_sast()
        self.assertEqual(sast["status"], "success")
        self.assertGreater(sast["files_scanned"], 0)

        secrets = scan_codebase_secrets()
        self.assertEqual(secrets["status"], "success")
        self.assertGreater(secrets["files_scanned"], 0)

    def test_04_dependency_scanner(self):
        """Verifies OSV dependency scanner parses requirements.txt."""
        req_path = os.path.join(os.path.dirname(__file__), "..", "gateway", "requirements.txt")
        res = asyncio.run(scan_dependencies(manifest_file=req_path))
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["scanned_dependencies_count"], 0)

    def test_05_local_test_runner(self):
        """Verifies test runner detects runner or gracefully reports skipped."""
        res = run_local_test_suite()
        self.assertIn(res["status"], ["passed", "failed", "skipped"])

    def test_06_real_pr_engine_no_mocks(self):
        """Verifies GitHub PR engine never returns fake mock URLs when token is missing."""
        gh = GitHubGitOpsService()
        # Override token to empty
        gh._get_credentials = lambda target_repo=None: ("", "test-owner", "test-repo")
        res = asyncio.run(gh.create_pull_request(title="Test PR", body="Test Body"))
        self.assertEqual(res["status"], "error")
        self.assertIn("GITHUB_TOKEN is not configured", res["error"])
        # Ensure no fake pull/42 url
        self.assertNotIn("pull/42", str(res))

if __name__ == "__main__":
    unittest.main()
