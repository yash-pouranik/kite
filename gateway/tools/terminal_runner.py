import os
import re
import subprocess
import logging
from typing import Dict, Any, Optional
from tools.git_ops import _resolve_repo_path

logger = logging.getLogger("cyberwar.tools.terminal")

# Commands permitted under governed terminal execution
ALLOWED_COMMAND_PREFIXES = [
    "kubectl", "git", "docker", "curl", "cat", "ls", "grep",
    "find", "npm", "node", "python", "df", "ps", "pwd", "echo",
    "head", "tail", "whoami", "uname", "tar", "sh", "bash"
]

# Destructive operations strictly blocked
BLACKLISTED_PATTERNS = [
    r"\brm\s+-(?:r|f|rf|fr)\b",
    r"\bmkfs\b",
    r"\bdd\b",
    r"\bfdisk\b",
    r"\breboot\b",
    r"\bshutdown\b",
    r"\bpoweroff\b",
    r"\binit\s+0\b",
    r"\bkill\s+-9\s+1\b",
    r"\bchmod\s+777\b",
    r"\bchown\s+root\b",
    r":\(\)\s*\{\s*:\|:&\s*\};:", # Fork bomb
]

# Sensitive files / patterns that must never be read or printed
SECRET_LEAK_PATTERNS = [
    r"\.env(?:\b|$)",
    r"/app/\.env",
    r"id_rsa",
    r"\.ssh/",
    r"secrets\.json"
]

def _mask_tokens(text: str) -> str:
    """Masks API keys, tokens, and credentials in terminal output."""
    if not text:
        return ""
    # Mask OpenAI keys
    text = re.sub(r"sk-(?:proj-)?[a-zA-Z0-9_-]{20,}", "sk-***[MASKED]***", text)
    # Mask GitHub tokens
    text = re.sub(r"gh[pousr]_[a-zA-Z0-9]{20,}", "ghp_***[MASKED]***", text)
    # Mask AWS keys
    text = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA***[MASKED]***", text)
    # Mask JWT tokens
    text = re.sub(r"eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}", "eyJ***[JWT_MASKED]***", text)
    return text

def execute_terminal_command(
    command: str,
    working_dir: Optional[str] = None,
    timeout_seconds: int = 15
) -> Dict[str, Any]:
    """
    Executes an arbitrary CLI command in the target environment
    under strict SecOps safety guardrails.
    """
    if not command or not command.strip():
        return {"status": "error", "error": "Command string cannot be empty."}

    cmd_clean = command.strip()

    # 1. Guardrail Check: Blacklisted destructive commands
    for pattern in BLACKLISTED_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            logger.warning(f"Terminal Runner BLOCKED dangerous command: {cmd_clean}")
            return {
                "status": "blocked",
                "error": "Command execution blocked by Kite SecOps Security Policy (destructive operation detected).",
                "matched_rule": pattern
            }

    # 2. Guardrail Check: Secret file leakage
    for pattern in SECRET_LEAK_PATTERNS:
        if re.search(pattern, cmd_clean, re.IGNORECASE):
            logger.warning(f"Terminal Runner BLOCKED secret leak attempt: {cmd_clean}")
            return {
                "status": "blocked",
                "error": "Command execution blocked by Kite SecOps Security Policy (attempted access to protected environment secrets).",
                "matched_rule": pattern
            }

    # 3. Guardrail Check: Allowed command prefix
    first_token = cmd_clean.split()[0].lower()
    # Strip path prefixes like /usr/bin/kubectl -> kubectl
    first_token_name = os.path.basename(first_token)
    if first_token_name not in ALLOWED_COMMAND_PREFIXES:
        return {
            "status": "blocked",
            "error": f"Command '{first_token_name}' is not in the allowed command whitelist.",
            "allowed_commands": ALLOWED_COMMAND_PREFIXES
        }

    # 4. Resolve working directory
    target_path = _resolve_repo_path(working_dir)
    if not os.path.exists(target_path):
        target_path = os.getcwd()

    # 5. Execute Command
    try:
        logger.info(f"Terminal Runner executing: [{cmd_clean}] in [{target_path}]")
        proc = subprocess.run(
            cmd_clean,
            shell=True,
            cwd=target_path,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )

        stdout_sanitized = _mask_tokens(proc.stdout)
        stderr_sanitized = _mask_tokens(proc.stderr)

        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "command": cmd_clean,
            "exit_code": proc.returncode,
            "working_directory": target_path,
            "stdout": stdout_sanitized.strip()[-3000:] if stdout_sanitized else "",
            "stderr": stderr_sanitized.strip()[-1500:] if stderr_sanitized else "",
            "is_clean_exit": proc.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": cmd_clean,
            "error": f"Command timed out after {timeout_seconds} seconds."
        }
    except Exception as e:
        logger.error(f"Error executing terminal command: {e}", exc_info=True)
        return {"status": "error", "command": cmd_clean, "error": str(e)}
