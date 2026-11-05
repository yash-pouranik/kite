import json
import os
import subprocess
import logging
from typing import Dict, Any, Optional
from tools.git_ops import _resolve_repo_path

logger = logging.getLogger("cyberwar.tools.test_runner")

def run_local_test_suite(
    test_command: Optional[str] = None,
    repo_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes automated tests in the target repository before applying fixes or opening PRs.
    Detects package.json test scripts or pytest configurations automatically.
    """
    target_path = _resolve_repo_path(repo_dir)
    if not os.path.exists(target_path):
        return {"status": "error", "error": f"Repository path not found: {target_path}"}

    # Auto-detect test runner if not provided
    cmd = test_command
    if not cmd:
        pkg_json = os.path.join(target_path, "package.json")
        if os.path.exists(pkg_json):
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                scripts = data.get("scripts", {})
                if "test" in scripts:
                    cmd = "npm test"
            except Exception:
                pass

        if not cmd and (os.path.exists(os.path.join(target_path, "pytest.ini")) or
                        os.path.exists(os.path.join(target_path, "tests"))):
            cmd = "pytest"

    if not cmd:
        return {
            "status": "skipped",
            "message": "No test runner configured in repository (no package.json 'test' script or pytest.ini).",
            "repo_path": target_path
        }

    try:
        logger.info(f"Executing test command: '{cmd}' in {target_path}")
        # Run test command safely with timeout
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=45
        )

        passed = proc.returncode == 0
        output = (proc.stdout + "\n" + proc.stderr).strip()

        return {
            "status": "passed" if passed else "failed",
            "command": cmd,
            "exit_code": proc.returncode,
            "is_passing": passed,
            "output_snippet": output[-2000:] if output else "Tests completed with no output."
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": cmd,
            "error": "Test suite execution timed out after 45 seconds."
        }
    except Exception as e:
        return {
            "status": "error",
            "command": cmd,
            "error": str(e)
        }
