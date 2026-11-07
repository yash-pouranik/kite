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
from tools.terminal_runner import execute_terminal_command
from services.github_service import GitHubGitOpsService

class TestSecOpsTools(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        register_all_tools()

    def test_01_tool_registry_registration(self):
        """Verifies that all 25 tools are successfully registered in ToolRegistry."""
        schemas = registry.get_schemas()
        tool_names = [s["function"]["name"] for s in schemas]
        self.assertGreaterEqual(len(tool_names), 27, f"Expected >= 27 tools, found {len(tool_names)}")

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
            "get_k8s_pods",
            "tail_k8s_logs",
            "check_service_health",
            "run_local_test_suite",
            "check_github_ci_status",
            "sync_github_issue",
            "apply_virtual_shield",
            "rollback_virtual_shield",
            "execute_terminal_command"
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

    def test_07_governed_terminal_runner(self):
        """Verifies terminal command execution and strict SecOps guardrails."""
        # 1. Allowed safe command executes cleanly
        res = execute_terminal_command("git status")
        self.assertIn(res["status"], ["success", "failed"])
        self.assertIn("command", res)

        # 2. Destructive command is blocked by guardrail
        blocked_res = execute_terminal_command("rm -rf /")
        self.assertEqual(blocked_res["status"], "blocked")
        self.assertIn("destructive operation detected", blocked_res["error"])

        # 3. Secret file reading is blocked
        secret_res = execute_terminal_command("cat .env")
        self.assertEqual(secret_res["status"], "blocked")
        self.assertIn("environment secrets", secret_res["error"])

        # 4. Unknown / disallowed command prefix is blocked
        disallowed_res = execute_terminal_command("powershell.exe -c Get-Process")
        self.assertEqual(disallowed_res["status"], "blocked")
        self.assertIn("not in the allowed command whitelist", disallowed_res["error"])

    def test_08_switch_agent_protocol_client(self):
        """Test Switch Agent Protocol WebSocket client frame handling and heartbeat."""
        from services.switch_client import SwitchAgentProtocolClient
        import json

        client = SwitchAgentProtocolClient()
        self.assertEqual(client.room_id, "cyberwar-ops")
        self.assertEqual(client.agent_id, "kite-secops")
        self.assertTrue(client.ws_base_url.startswith("ws://") or client.ws_base_url.startswith("wss://"))

        # Mock WebSocket to test ping/pong frame handling
        class MockWS:
            def __init__(self):
                self.sent = []
            async def send(self, payload):
                self.sent.append(payload)

        mock_ws = MockWS()
        client.last_cursor = 42

        # 1. Ping receives pong with cursor
        asyncio.run(client._handle_incoming_frame(json.dumps({"type": "ping"}), mock_ws))
        self.assertEqual(len(mock_ws.sent), 1)
        pong = json.loads(mock_ws.sent[0])
        self.assertEqual(pong.get("type"), "pong")
        self.assertEqual(pong.get("cursor"), 42)

        # 2. Connection state updates generation & cursor
        asyncio.run(client._handle_incoming_frame(json.dumps({
            "type": "connection_state",
            "generation": 105,
            "cursor": 88
        }), mock_ws))
        self.assertEqual(client.generation, 105)
        self.assertEqual(client.last_cursor, 88)

    def test_09_tool_layer_four_eyes_approval_gate(self):
        """
        Adversarial Test Suite for Tool-Layer Four-Eyes Principle:
        1. Direct tool execution without approval must be blocked.
        2. Automated bots/agents cannot approve actions.
        3. Human approval enables single-use execution.
        4. Replay attacks and parameter tampering are blocked.
        """
        from services.approval_guard import approval_guard
        from services.virtual_patcher import NginxVirtualPatcher

        patcher = NginxVirtualPatcher()
        endpoint = "/api/v1/secure/resource"

        # 1. Direct tool call without approval MUST be blocked
        blocked_res = asyncio.run(patcher.apply_virtual_patch(endpoint=endpoint))
        self.assertEqual(blocked_res["status"], "blocked")
        self.assertTrue(blocked_res.get("requires_approval"))
        self.assertIn("Tool-layer Four-Eyes Principle enforced", blocked_res["error"])

        # Extract the auto-registered pending plan hash
        plan_hash = approval_guard.compute_plan_hash("apply_virtual_shield", endpoint, {"patch_filename": "patch_kite_shield.conf"})

        # 2. Automated Agent / Bot approval MUST be rejected
        bot_approved, bot_msg = approval_guard.approve_plan(plan_hash, approver_id="switch-agent-fixer", is_bot=True)
        self.assertFalse(bot_approved)
        self.assertIn("automated agent/bot", bot_msg.lower())

        bot_prefix_approved, bot_prefix_msg = approval_guard.approve_plan(plan_hash, approver_id="bot-attacker")
        self.assertFalse(bot_prefix_approved)
        self.assertIn("automated agent/bot", bot_prefix_msg.lower())

        # 3. Genuine Human Approval MUST succeed
        human_approved, human_msg = approval_guard.approve_plan(plan_hash, approver_id="yash-lead", is_bot=False)
        self.assertTrue(human_approved)
        self.assertIn("successfully approved by human lead", human_msg)

        # 4. Tampering test: trying to use approved hash for a different endpoint MUST fail
        tampered_res = asyncio.run(patcher.apply_virtual_patch(endpoint="/api/v1/different/admin", plan_hash=plan_hash))
        self.assertEqual(tampered_res["status"], "blocked")
        self.assertIn("mismatch", tampered_res["error"])

        # 5. Executing with valid human-approved hash succeeds
        success_res = asyncio.run(patcher.apply_virtual_patch(endpoint=endpoint, plan_hash=plan_hash))
        self.assertEqual(success_res["status"], "success")

        # 6. Replay attack: calling again with the same token MUST fail (single-use consumed)
        replay_res = asyncio.run(patcher.apply_virtual_patch(endpoint=endpoint, plan_hash=plan_hash))
        self.assertEqual(replay_res["status"], "blocked")
        self.assertIn("already been consumed", replay_res["error"])

    def test_10_adversarial_dialogue_refusals(self):
        """
        Adversarial Test Suite for Dialogue Intent Parser:
        Confirms negative qualifiers ('don't deploy', 'approve nahi hai', 'why deploy?')
        are NEVER falsely interpreted as CONFIRM_ACTION.
        """
        from nlu.dialogue_manager import ConversationalDialogueManager

        dm = ConversationalDialogueManager()

        # 1. Negative qualifiers with action verbs -> Must be REFUSE_ACTION
        refusal_cases = [
            "don't deploy",
            "dont apply the shield",
            "approve nahi hai",
            "why deploy?",
            "do not deploy this patch",
            "stop and wait",
            "cancel execution"
        ]
        for phrase in refusal_cases:
            res = asyncio.run(dm.analyze_human_turn(phrase))
            self.assertEqual(res["intent"], "REFUSE_ACTION", f"Failed for phrase: '{phrase}'")

        # 2. Genuine positive confirmations -> Must be CONFIRM_ACTION
        confirm_cases = [
            "approve",
            "approved",
            "proceed",
            "go ahead",
            "haan karo"
        ]
        for phrase in confirm_cases:
            res = asyncio.run(dm.analyze_human_turn(phrase))
            self.assertEqual(res["intent"], "CONFIRM_ACTION", f"Failed for phrase: '{phrase}'")

    def test_11_pr_review_and_branch_manager_tools(self):
        """
        Verifies PR / MR Diff Fetcher, Comment & Review Writer, and Branch/Commit Manager tools.
        """
        from tools.pr_review_ops import (
            fetch_pr_diff_and_files,
            post_pr_review_and_comment,
            manage_branch_and_commit
        )

        schemas = registry.get_schemas()
        tool_names = [s["function"]["name"] for s in schemas]

        # 1. Verify tools are registered in schema catalog
        self.assertIn("fetch_pr_diff_and_files", tool_names)
        self.assertIn("post_pr_review_and_comment", tool_names)
        self.assertIn("manage_branch_and_commit", tool_names)
        self.assertGreaterEqual(len(tool_names), 30)

        # 2. Test PR Diff Fetcher error handling when unconfigured
        fetch_res = asyncio.run(fetch_pr_diff_and_files(pr_number=999, target_repo="nonexistent/repo"))
        self.assertIn(fetch_res["status"], ["error", "failed"])

        # 3. Test Comment & Review Writer validation
        review_res = asyncio.run(post_pr_review_and_comment(
            pr_number=999,
            body="LGTM. Parameterized queries verified.",
            event="APPROVE",
            target_repo="nonexistent/repo"
        ))
        self.assertIn(review_res["status"], ["error", "failed"])

        # 4. Test Branch & Commit Manager local git execution
        current_status = get_git_status()
        base_branch = current_status.get("branch", "main")

        # Test branch creation
        test_branch = "kite/test-pr-review-branch"
        branch_res = asyncio.run(manage_branch_and_commit(
            action="create_branch",
            branch_name=test_branch,
            push_remote=False
        ))
        self.assertEqual(branch_res["status"], "success")
        self.assertEqual(branch_res["branch"], test_branch)

        # Return to original branch
        from tools.git_ops import _run_git_cmd
        _run_git_cmd(["checkout", base_branch])
        _run_git_cmd(["branch", "-D", test_branch])

if __name__ == "__main__":
    unittest.main()
