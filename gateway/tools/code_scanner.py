import os
import re
import logging
from typing import Dict, Any, List, Optional
from tools.git_ops import _resolve_repo_path

logger = logging.getLogger("cyberwar.tools.scanner")

EXCLUDED_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", 
    "__pycache__", ".venv", "venv", "coverage", ".cache"
}

# Regex patterns for SAST code smells
SAST_RULES = [
    {
        "id": "SAST-SQLI-001",
        "severity": "CRITICAL",
        "name": "Raw SQL String Concatenation",
        "pattern": r"(?:db|sequelize|knex|connection|pool|cursor|client)\.(?:query|execute|raw)\s*\(\s*(?:[`'\"][^`'\"]*SELECT[^`'\"]*[`'\"]\s*\+|\s*f[\"'].*SELECT|\`.*SELECT.*\$\{)",
        "recommendation": "Use parameterized prepared statements with bind parameters instead of string interpolation."
    },
    {
        "id": "SAST-AUTH-001",
        "severity": "HIGH",
        "name": "Disabled SSL/TLS Verification",
        "pattern": r"(?:rejectUnauthorized\s*:\s*false|verify\s*=\s*False|NODE_TLS_REJECT_UNAUTHORIZED\s*=\s*['\"]0['\"])",
        "recommendation": "Never disable SSL/TLS certificate verification in production environments."
    },
    {
        "id": "SAST-CORS-001",
        "severity": "HIGH",
        "name": "Permissive Wildcard CORS with Credentials",
        "pattern": r"(?:cors\s*\(\s*\{[^}]*origin\s*:\s*['\"\*]+[^}]*credentials\s*:\s*true)",
        "recommendation": "Explicitly whitelist trusted origins when supporting credentialed requests."
    },
    {
        "id": "SAST-EXEC-001",
        "severity": "CRITICAL",
        "name": "Dynamic Code Execution (eval / exec)",
        "pattern": r"\b(?:eval|exec)\s*\([^)]+\)",
        "recommendation": "Avoid dynamic code execution of unvalidated user input."
    }
]

# Regex patterns for High-Entropy Secret Detection
SECRET_RULES = [
    {
        "id": "SECRET-AWS-001",
        "severity": "CRITICAL",
        "name": "AWS Access Key ID",
        "pattern": r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])",
        "prefix_match": r"AKIA[0-9A-Z]{16}",
        "recommendation": "Revoke key in AWS IAM and load via environment variables or AWS Secrets Manager."
    },
    {
        "id": "SECRET-OPENAI-001",
        "severity": "CRITICAL",
        "name": "OpenAI API Key",
        "pattern": r"sk-(?:proj-)?[a-zA-Z0-9_-]{32,}",
        "recommendation": "Rotate OpenAI key immediately and load through secure environment secrets."
    },
    {
        "id": "SECRET-GOOGLE-001",
        "severity": "HIGH",
        "name": "Google API Key",
        "pattern": r"AIza[0-9A-Za-z-_]{35}",
        "recommendation": "Restrict key usage by HTTP referrer / IP in Google Cloud Console."
    },
    {
        "id": "SECRET-KEY-001",
        "severity": "CRITICAL",
        "name": "Private Cryptographic Key",
        "pattern": r"-----BEGIN (?:RSA|EC|DSA|OPENSSH)? ?PRIVATE KEY-----",
        "recommendation": "Never store unencrypted private keys in source control."
    },
    {
        "id": "SECRET-JWT-001",
        "severity": "MEDIUM",
        "name": "Hardcoded JWT Token",
        "pattern": r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b",
        "recommendation": "Tokens must be generated dynamically and never stored hardcoded in code."
    },
    {
        "id": "SECRET-HARDCODED-001",
        "severity": "HIGH",
        "name": "Hardcoded Secret / Password Assignment",
        "pattern": r"(?:api[_-]?key|secret|password|auth_token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.!@#$%^&*]{10,}['\"]",
        "recommendation": "Remove hardcoded credentials and read from environment variables."
    }
]

def _walk_files(base_path: str, extensions: List[str]) -> List[str]:
    """Recursively walks repository ignoring vendored and built directories."""
    matched_files = []
    for root, dirs, files in os.walk(base_path):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                matched_files.append(os.path.join(root, f))
    return matched_files

def scan_codebase_sast(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes Static Application Security Testing (SAST) on the target repository.
    Scans for raw SQL concatenation, disabled SSL, wildcard CORS, and dynamic eval.
    """
    target_path = _resolve_repo_path(repo_dir)
    if not os.path.exists(target_path):
        return {"status": "error", "error": f"Target repo path not found: {target_path}"}

    files = _walk_files(target_path, [".js", ".ts", ".jsx", ".tsx", ".py", ".go", ".json"])
    findings = []

    for file_path in files:
        rel_path = os.path.relpath(file_path, target_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            full_text = "".join(lines)
            for rule in SAST_RULES:
                # Check line by line or pattern
                for line_idx, line in enumerate(lines, 1):
                    if re.search(rule["pattern"], line, re.IGNORECASE):
                        findings.append({
                            "rule_id": rule["id"],
                            "severity": rule["severity"],
                            "title": rule["name"],
                            "file": rel_path,
                            "line": line_idx,
                            "snippet": line.strip()[:150],
                            "recommendation": rule["recommendation"]
                        })
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")

    return {
        "status": "success",
        "repo_path": target_path,
        "files_scanned": len(files),
        "total_findings": len(findings),
        "is_clean": len(findings) == 0,
        "findings": findings
    }

def scan_codebase_secrets(repo_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Scans repository files and configurations for hardcoded secrets, API tokens, and private keys.
    """
    target_path = _resolve_repo_path(repo_dir)
    if not os.path.exists(target_path):
        return {"status": "error", "error": f"Target repo path not found: {target_path}"}

    files = _walk_files(target_path, [".js", ".ts", ".py", ".json", ".env", ".yaml", ".yml", ".conf"])
    secrets_found = []

    for file_path in files:
        rel_path = os.path.relpath(file_path, target_path)
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_idx, line in enumerate(lines, 1):
                # Don't scan comment lines that mention dummy keys
                line_stripped = line.strip()
                if line_stripped.startswith("//") or line_stripped.startswith("#"):
                    if "example" in line_stripped.lower() or "your_" in line_stripped.lower():
                        continue

                for rule in SECRET_RULES:
                    pattern = rule.get("prefix_match") or rule["pattern"]
                    match = re.search(pattern, line)
                    if match:
                        matched_str = match.group(0)
                        # Mask secret in output for safety
                        masked = matched_str[:4] + "*" * (len(matched_str) - 8) + matched_str[-4:] if len(matched_str) > 8 else "***"
                        secrets_found.append({
                            "rule_id": rule["id"],
                            "severity": rule["severity"],
                            "name": rule["name"],
                            "file": rel_path,
                            "line": line_idx,
                            "masked_token": masked,
                            "recommendation": rule["recommendation"]
                        })
        except Exception as e:
            logger.warning(f"Could not read file {file_path}: {e}")

    return {
        "status": "success",
        "repo_path": target_path,
        "files_scanned": len(files),
        "secrets_count": len(secrets_found),
        "is_clean": len(secrets_found) == 0,
        "findings": secrets_found
    }
