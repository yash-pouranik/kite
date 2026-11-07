import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("cyberwar.services.approval_guard")

class ApprovalGuard:
    """
    Tool-Layer Human-in-the-Loop Approval Gate.
    Enforces the Four-Eyes Principle for high-risk operations (e.g. Virtual Shields, GitHub PRs):
    1. Direct tool calls without explicit human approval are BLOCKED.
    2. Approval must come from a verified human user ID (bots/agents are rejected).
    3. Approval is cryptographically bound to the exact action parameters via plan hash.
    4. Approvals are single-use (consumed upon execution) and expire after TTL (300s).
    """

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        # hash -> {action_type, target, details, status: PENDING|APPROVED|CONSUMED|EXPIRED, created_at, approved_by, approved_at}
        self.plans: Dict[str, Dict[str, Any]] = {}

    def compute_plan_hash(self, action_type: str, target: str, details: Optional[Dict[str, Any]] = None) -> str:
        """Generates a deterministic 12-char SHA-256 hash for the given plan parameters."""
        details_str = json.dumps(details or {}, sort_keys=True)
        raw = f"{action_type}:{target}:{details_str}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:12]

    def register_pending_plan(self, action_type: str, target: str, details: Optional[Dict[str, Any]] = None) -> str:
        """Registers a proposed plan in PENDING state awaiting human lead sign-off."""
        plan_hash = self.compute_plan_hash(action_type, target, details)
        self.plans[plan_hash] = {
            "action_type": action_type,
            "target": target,
            "details": details or {},
            "status": "PENDING",
            "created_at": time.time(),
            "approved_by": None,
            "approved_at": None
        }
        logger.info(f"Registered pending plan '{action_type}' on '{target}' with hash [{plan_hash}]")
        return plan_hash

    def approve_plan(
        self,
        plan_hash: str,
        approver_id: str,
        approver_name: Optional[str] = None,
        is_bot: bool = False
    ) -> Tuple[bool, str]:
        """
        Approves a registered plan.
        Strictly rejects automated bots/agents and validates TTL.
        """
        approver_lower = approver_id.lower()
        # 1. Adversarial Guard: Reject bot / agent approvals
        if is_bot or any(approver_lower.startswith(prefix) for prefix in ["bot-", "switch-agent-", "agent-", "bot_"]) or "bot" in approver_lower:
            logger.warning(f"Rejected approval attempt from automated bot/agent: {approver_id}")
            return False, "Approval rejected: Approver is an automated agent/bot. Only verified human leads can approve high-risk operations."

        # 2. Check if plan exists
        plan = self.plans.get(plan_hash)
        if not plan:
            return False, f"Approval rejected: Plan hash '{plan_hash}' not found."

        # 3. Check TTL expiration
        if time.time() - plan["created_at"] > self.ttl_seconds:
            plan["status"] = "EXPIRED"
            return False, "Approval rejected: Plan has expired. Please formulate a fresh plan."

        # 4. Check if already consumed
        if plan["status"] == "CONSUMED":
            return False, "Approval rejected: Plan approval has already been consumed."

        plan["status"] = "APPROVED"
        plan["approved_by"] = approver_id
        plan["approved_at"] = time.time()
        logger.info(f"Plan [{plan_hash}] successfully approved by human lead '{approver_id}'")
        return True, f"Plan '{plan_hash}' successfully approved by human lead '{approver_id}'."

    def verify_and_consume(
        self,
        action_type: str,
        target: str,
        details: Optional[Dict[str, Any]] = None,
        plan_hash: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Tool-layer gate: Verifies that the action has a valid, unexpired, matching human approval.
        Consumes the token immediately upon success to prevent replay attacks.
        """
        expected_hash = self.compute_plan_hash(action_type, target, details)

        # 1. Direct tool call without plan_hash -> Block & auto-register
        if not plan_hash:
            registered_hash = self.register_pending_plan(action_type, target, details)
            msg = (
                f"BLOCKED: Tool-layer Four-Eyes Principle enforced. Action '{action_type}' requires "
                f"human sign-off. Registered pending plan hash: '{registered_hash}'. "
                f"A human security lead must approve this hash before execution."
            )
            logger.warning(msg)
            return False, msg

        # 2. Plan hash mismatch (e.g. parameters tampered)
        if plan_hash != expected_hash:
            msg = f"BLOCKED: Plan hash mismatch. Expected [{expected_hash}], got [{plan_hash}]. Parameter tampering detected."
            logger.warning(msg)
            return False, msg

        plan = self.plans.get(plan_hash)
        if not plan:
            return False, f"BLOCKED: No plan found for hash '{plan_hash}'."

        # 3. Status check
        if plan["status"] == "PENDING":
            return False, f"BLOCKED: Plan '{plan_hash}' is pending approval from a human lead."
        if plan["status"] == "CONSUMED":
            return False, f"BLOCKED: Plan '{plan_hash}' approval has already been consumed (single-use token)."
        if plan["status"] == "EXPIRED" or (time.time() - plan.get("approved_at", 0) > self.ttl_seconds):
            plan["status"] = "EXPIRED"
            return False, f"BLOCKED: Plan '{plan_hash}' approval has expired."

        # 4. Successful authorization -> Consume token
        plan["status"] = "CONSUMED"
        logger.info(f"Authorized action '{action_type}' for target '{target}' by human lead '{plan['approved_by']}'")
        return True, f"Authorized by human lead '{plan['approved_by']}'."

# Global singleton
approval_guard = ApprovalGuard()
