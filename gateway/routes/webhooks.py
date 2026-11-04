import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from nlu.dialogue_manager import ConversationalDialogueManager
from agents.recon_bot import ReconBotAgent
from agents.attacker import AttackerAgent
from agents.fix_engine import FixEngineAgent
from agents.verifier import VerifierAgent

logger = logging.getLogger("cyberwar.routes.webhook")
router = APIRouter(prefix="/switch", tags=["Switch Protocol Webhook"])

dialogue_manager = ConversationalDialogueManager()
recon_agent = ReconBotAgent()
attacker_agent = AttackerAgent()
fix_engine_agent = FixEngineAgent()
verifier_agent = VerifierAgent()

# Ephemeral state store for active incident turns
active_incident_context = {
    "stage": "IDLE", # IDLE, RECON_DONE, AWAITING_ATTACK_APPROVAL, ATTACK_DONE, AWAITING_FIX_APPROVAL, FIXED
    "target": "juice-shop-staging",
    "endpoint": "/rest/products/search",
    "vuln_title": "SQL Injection"
}

class SwitchIncomingMessage(BaseModel):
    room: str
    sender: str
    message: str
    conversation_id: str

class SwitchOutgoingMessage(BaseModel):
    room: str
    agent_name: str
    content: str

@router.post("/message")
async def handle_switch_incoming_event(payload: SwitchIncomingMessage, background_tasks: BackgroundTasks):
    """
    Primary ingress point for messages coming from Switch / Discord.
    """
    logger.info(f"Incoming message from {payload.sender} in room {payload.room}: '{payload.message}'")
    
    # 1. Parse conversation intent and check for ambiguity
    analysis = await dialogue_manager.analyze_human_turn(payload.message)
    intent = analysis.get("intent")
    is_ambiguous = analysis.get("is_ambiguous", False)

    # 2. If prompt is ambiguous, ask clarification directly
    if is_ambiguous:
        clarification_text = analysis.get("clarification_prompt")
        return {
            "status": "clarification_needed",
            "reply": {
                "agent_name": "recon-bot",
                "content": clarification_text
            }
        }

    # 3. If user requested a scan
    if intent == "REQUEST_SCAN":
        target = analysis.get("extracted_target") or "juice-shop-staging"
        recon_data = await recon_agent.execute_reconnaissance(target)
        summary = recon_data.get("findings", {}).get("executive_summary", "")
        
        # Attacker prepares safe proposal
        proposal = await attacker_agent.formulate_verification_proposal({
            "title": "Unsanitized SQL Injection on Search Endpoint",
            "endpoint": "/rest/products/search"
        })
        
        active_incident_context["stage"] = "AWAITING_ATTACK_APPROVAL"
        active_incident_context["target"] = target
        active_incident_context["endpoint"] = "/rest/products/search"

        combined_reply = (
            f"🔍 **Recon-Bot Scan Report (`{target}`)**\n"
            f"{summary}\n\n"
            f"⚔️ **Attacker Agent (`{attacker_agent.model_name}`):**\n"
            f"{proposal.get('conversational_proposal')}"
        )
        return {
            "status": "awaiting_attack_approval",
            "reply": {
                "agent_name": "attacker",
                "content": combined_reply
            },
            "data": recon_data
        }

    # 4. If human naturally approves attack probe
    if intent == "CONFIRM_ACTION" and active_incident_context["stage"] == "AWAITING_ATTACK_APPROVAL":
        active_incident_context["stage"] = "ATTACKING"
        exploit_data = await attacker_agent.execute_verified_exploit(active_incident_context["endpoint"])
        
        # Immediately formulate dual-track remediation plan
        fix_proposal = await fix_engine_agent.formulate_remediation_plan({
            "title": active_incident_context["vuln_title"],
            "endpoint": active_incident_context["endpoint"]
        })
        active_incident_context["stage"] = "AWAITING_FIX_APPROVAL"

        combined_reply = (
            f"{exploit_data.get('conversational_report')}\n\n"
            f"🛡️ **Fix Engine (`{fix_engine_agent.model_name}`):**\n"
            f"{fix_proposal.get('conversational_plan')}"
        )
        return {
            "status": "awaiting_fix_approval",
            "reply": {
                "agent_name": "fix-engine",
                "content": combined_reply
            },
            "data": exploit_data
        }

    # 5. If human approves fix (e.g. "apply the shield", "deploy the fix", "sounds good")
    if intent == "CONFIRM_ACTION" and active_incident_context["stage"] == "AWAITING_FIX_APPROVAL":
        active_incident_context["stage"] = "FIXING"
        remediation_res = await fix_engine_agent.execute_dual_remediation()
        
        # Trigger autonomous Verifier agent audit
        audit_res = await verifier_agent.execute_verification_audit(active_incident_context["endpoint"])
        active_incident_context["stage"] = "RESOLVED"

        combined_reply = (
            f"{remediation_res.get('conversational_report')}\n\n"
            f"{audit_res.get('conversational_scorecard')}"
        )

        return {
            "status": "incident_resolved",
            "reply": {
                "agent_name": "verifier",
                "content": combined_reply
            },
            "data": {
                "remediation": remediation_res,
                "verification": audit_res
            }
        }

    return {
        "status": "acknowledged",
        "reply": {
            "agent_name": "recon-bot",
            "content": "Acknowledged. CyberWar-Room agents are standing by."
        }
    }
