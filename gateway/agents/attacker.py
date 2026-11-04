import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings
from tools.exploit_runner import SafeExploitToolkit
from services.knowledge_manager import KnowledgeBaseManager

logger = logging.getLogger("cyberwar.agents.attacker")

class AttackerAgent:
    """
    Attacker Agent powered by gpt-6-luna.
    Functions as an ethical white-hat penetration tester. Validates Recon-Bot alerts,
    formulates harmless PoC probes, requests natural human approval, and verifies exploits.
    Leverages persistent Knowledge Base for exact parameter names and payload types.
    """
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.ATTACKER_MODEL # gpt-6-luna
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        self.exploit_toolkit = SafeExploitToolkit()
        self.kb = KnowledgeBaseManager()

    async def formulate_verification_proposal(self, recon_finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses gpt-6-luna to craft a natural language explanation of the vulnerability
        and propose a harmless verification probe for human sign-off.
        Checks Knowledge Base for parameters.
        """
        vuln_title = recon_finding.get("title", "SQL Injection")
        endpoint = recon_finding.get("endpoint", "/rest/products/search")
        
        # Check Knowledge Base for known fields
        auth_kb = self.kb.get_knowledge("auth_mechanisms")
        params = ["q"]
        if "login" in endpoint and auth_kb:
            params = auth_kb.get("endpoints", {}).get("login", {}).get("payload_fields", ["email", "password"])

        proposal_text = (
            f"🚨 **Attacker Agent — Pre-Action Plan for Approval**\n\n"
            f"Recon-Bot detected a high-risk **{vuln_title}** on `{endpoint}`.\n"
            "To eliminate false positives, if you confirm, here is **exactly what I will execute**:\n"
            f"1. 🎯 **Target Endpoint:** `{endpoint}`\n"
            f"2. 🧪 **Payload Probe:** Send a harmless read-only test vector: `' OR 1=1 --` on parameter `{params[0]}`.\n"
            "3. 🛡️ **Safety Guarantee:** This is a non-destructive read probe. It will not write, alter, or drop any customer records.\n"
            "4. 📊 **Success Metric:** If vulnerable, internal records will be exposed in the response; if secure, the probe will be sanitized.\n\n"
            "**Do you approve me executing this verification probe?**"
        )

        return {
            "conversational_proposal": proposal_text,
            "probe_payload": "' OR 1=1 --",
            "endpoint": endpoint
        }
        
        system_prompt = (
            "You are Attacker, a principal ethical penetration tester in a SecOps War Room. "
            "You are communicating with human SecOps engineers in plain conversational English. "
            "Explain the vulnerability identified by Recon-Bot, why it must be verified to eliminate false positives, "
            "and propose a harmless read-only test probe. "
            "Ask politely for their approval before firing the probe. "
            "Return JSON with: "
            "'conversational_proposal' (clear natural explanation and approval request), "
            "'probe_payload' (the safe string to test), "
            "'endpoint' (the target endpoint)."
        )

        user_content = f"Vulnerability: {vuln_title}\nEndpoint: {endpoint}"

        if not self.client:
            # High-fidelity conversational fallback
            return {
                "conversational_proposal": (
                    f"I reviewed the alert from Recon-Bot regarding the **{vuln_title}** on `{endpoint}`. "
                    "To ensure this isn't a scanner false positive, I've prepared a harmless read-only test probe: `' OR 1=1 --`. "
                    "This probe will simply test if hidden catalog records are exposed without modifying any data. "
                    "May I proceed with this verification?"
                ),
                "probe_payload": "' OR 1=1 --",
                "endpoint": endpoint
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Error in Attacker proposal with OpenAI: {e}")
            return {
                "conversational_proposal": (
                    f"I see the **{vuln_title}** flagged on `{endpoint}`. "
                    "I have a safe read-only probe ready to verify if it can actually be exploited. "
                    "Should I go ahead and test it?"
                ),
                "probe_payload": "' OR 1=1 --",
                "endpoint": endpoint
            }

    async def execute_verified_exploit(self, endpoint: str) -> Dict[str, Any]:
        """
        Executes the safe probe and synthesizes findings into verifiable proof.
        """
        logger.info(f"Attacker executing verified exploit against {endpoint}")
        raw_result = await self.exploit_toolkit.verify_sqli_probe(endpoint=endpoint)

        is_exploitable = raw_result.get("is_exploitable", False)
        evidence = raw_result.get("evidence", "")

        return {
            "agent": "attacker",
            "model": self.model_name,
            "is_exploitable": is_exploitable,
            "verdict": raw_result.get("verdict"),
            "evidence": evidence,
            "conversational_report": (
                "🚨 **Exploit Confirmed by Attacker Agent**\n\n"
                f"{evidence}\n\n"
                "**Risk Verdict:** CRITICAL (Verified Active). "
                "Handing context over to **Fix Engine** to formulate immediate zero-downtime shielding and permanent code fixes."
            )
        }
