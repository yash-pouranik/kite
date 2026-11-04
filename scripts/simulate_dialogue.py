"""
CyberWar-Room End-to-End Conversational Simulator
Simulates the entire multi-turn natural dialogue flow between Human and Agents
across Recon, Attack, Fix, and Verify stages.
"""

import asyncio
import json
import sys
import os

# Add gateway to python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "gateway"))

from nlu.dialogue_manager import ConversationalDialogueManager
from agents.recon_bot import ReconBotAgent
from agents.attacker import AttackerAgent
from agents.fix_engine import FixEngineAgent
from agents.verifier import VerifierAgent

async def run_conversational_simulation():
    print("=" * 75)
    print("🛡️  CYBERWAR-ROOM END-TO-END CONVERSATIONAL SIMULATION")
    print("=" * 75)

    dialogue = ConversationalDialogueManager()
    recon = ReconBotAgent()
    attacker = AttackerAgent()
    fix_engine = FixEngineAgent()
    verifier = VerifierAgent()

    # --------------------------------------------------------------------------
    # Turn 1: Human sends an ambiguous audit request
    # --------------------------------------------------------------------------
    human_msg_1 = "Hey team, could someone check our store app for any security holes?"
    print(f"\n👤 HUMAN (Alex, SecOps Lead): \"{human_msg_1}\"")
    
    analysis_1 = await dialogue.analyze_human_turn(human_msg_1)
    if analysis_1.get("is_ambiguous"):
        print(f"\n🤖 RECON-BOT ({recon.model_name}):")
        print(f"\"{analysis_1.get('clarification_prompt')}\"")

    # --------------------------------------------------------------------------
    # Turn 2: Human clarifies scope
    # --------------------------------------------------------------------------
    human_msg_2 = "Let's do a comprehensive audit on our staging environment, please."
    print(f"\n👤 HUMAN: \"{human_msg_2}\"")

    analysis_2 = await dialogue.analyze_human_turn(human_msg_2)
    target = analysis_2.get("extracted_target") or "juice-shop-staging"
    
    print("\n⚙️  [System: Executing sandboxed Nmap & Nuclei scans in Docker...]")
    recon_res = await recon.execute_reconnaissance(target)
    summary = recon_res.get("findings", {}).get("executive_summary", "")

    print(f"\n🤖 RECON-BOT ({recon.model_name}):")
    print(f"\"{summary}\"")

    # --------------------------------------------------------------------------
    # Turn 3: Attacker proposes non-destructive verification probe
    # --------------------------------------------------------------------------
    attack_prop = await attacker.formulate_verification_proposal({
        "title": "Unsanitized SQL Injection on Search Endpoint",
        "endpoint": "/rest/products/search"
    })
    print(f"\n⚔️  ATTACKER ({attacker.model_name}):")
    print(f"\"{attack_prop.get('conversational_proposal')}\"")

    # --------------------------------------------------------------------------
    # Turn 4: Human confirms verification probe
    # --------------------------------------------------------------------------
    human_msg_3 = "Yes, please go ahead and verify it."
    print(f"\n👤 HUMAN: \"{human_msg_3}\"")

    print("\n⚙️  [System: Attacker firing safe read probe (' OR 1=1 --)...]")
    exploit_res = await attacker.execute_verified_exploit("/rest/products/search")
    print(f"\n⚔️  ATTACKER ({attacker.model_name}):")
    print(exploit_res.get("conversational_report"))

    # --------------------------------------------------------------------------
    # Turn 5: Fix Engine proposes Dual-Track Remediation
    # --------------------------------------------------------------------------
    fix_prop = await fix_engine.formulate_remediation_plan({
        "title": "SQL Injection",
        "endpoint": "/rest/products/search"
    })
    print(f"\n🛡️  FIX ENGINE ({fix_engine.model_name}):")
    print(fix_prop.get("conversational_plan"))

    # --------------------------------------------------------------------------
    # Turn 6: Human confirms dual remediation
    # --------------------------------------------------------------------------
    human_msg_4 = "That sounds great, please apply the virtual shield and raise the PR."
    print(f"\n👤 HUMAN: \"{human_msg_4}\"")

    print("\n⚙️  [System: Hot-reloading Nginx virtual patch & opening Git Pull Request...]")
    remediation_res = await fix_engine.execute_dual_remediation()
    print(f"\n🛡️  FIX ENGINE ({fix_engine.model_name}):")
    print(remediation_res.get("conversational_report"))

    # --------------------------------------------------------------------------
    # Turn 7: Verifier conducts dual-path audit (Legitimate vs Exploit traffic)
    # --------------------------------------------------------------------------
    print("\n⚙️  [System: Verifier testing customer traffic (200 OK) vs attack vector (403 Forbidden)...]")
    audit_res = await verifier.execute_verification_audit("/rest/products/search")
    print(f"\n⚖️  VERIFIER ({verifier.model_name}):")
    print(audit_res.get("conversational_scorecard"))

    print("\n" + "=" * 75)
    print("✅  ALL 4 AGENTS COMPLETED THE COLLABORATIVE CYCLE SUCCESSFULLY!")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_conversational_simulation())
