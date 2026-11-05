import asyncio
import logging
import discord
from discord.ext import commands
from config import settings
from nlu.dialogue_manager import ConversationalDialogueManager
from agents.recon_bot import ReconBotAgent
from agents.attacker import AttackerAgent
from agents.fix_engine import FixEngineAgent
from agents.verifier import VerifierAgent

logger = logging.getLogger("cyberwar.discord_runner")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

dialogue_mgr = ConversationalDialogueManager()
recon_agent = ReconBotAgent()
attacker_agent = AttackerAgent()
fix_agent = FixEngineAgent()
verifier_agent = VerifierAgent()

# Stateful incident memory
incident_state = {
    "stage": "IDLE", # IDLE, AWAITING_ATTACK_APPROVAL, ATTACK_DONE, AWAITING_FIX_APPROVAL, RESOLVED
    "target": "vynn.urbackend.in",
    "endpoint": "/api/v1/auth/login",
    "vuln": "SQL Injection / Auth Bypass"
}

@bot.event
async def on_ready():
    logger.info(f"🪁 Kite Bot is online in Discord as @{bot.user.name} (ID: {bot.user.id})")
    print(f"\n[Kite Bot Connected] Logged in as {bot.user.name}\n")

@bot.event
async def on_message(message: discord.Message):
    # Ignore own messages
    if message.author.bot:
        return

    content = message.content.strip()
    logger.info(f"Received message from {message.author.name} in #{message.channel.name}: {content}")

    # Analyze intent
    analysis = await dialogue_mgr.analyze_human_turn(content)
    intent = analysis.get("intent")
    is_ambiguous = analysis.get("is_ambiguous", False)

    # 1. Ambiguity handling
    if is_ambiguous:
        clarification = analysis.get("clarification_prompt")
        await message.channel.send(f"🤖 **Recon-Bot:** {clarification}")
        return

    # 2. Request Scan
    if intent == "REQUEST_SCAN":
        target = analysis.get("extracted_target") or incident_state["target"]
        focus_area = analysis.get("focus_area")
        async with message.channel.typing():
            focus_str = f" (Focus: {focus_area.upper()})" if focus_area else ""
            await message.channel.send(f"🔍 **Recon-Bot:** Starting target profiling and knowledge inspection on `{target}`{focus_str}...")
            recon_data = await recon_agent.execute_reconnaissance(target, focus_area=focus_area)
            summary = recon_data.get("findings", {}).get("executive_summary", "")

            # Attacker proposes safe PoC probe
            proposal = await attacker_agent.formulate_verification_proposal({
                "title": "SQL Injection on Auth Endpoint",
                "endpoint": incident_state["endpoint"]
            })
            incident_state["stage"] = "AWAITING_ATTACK_APPROVAL"

            await message.channel.send(f"🤖 **Recon-Bot Findings:**\n{summary}")
            await message.channel.send(f"{proposal.get('conversational_proposal')}")
        return

    # 3. Confirm Attack Probe
    if intent == "CONFIRM_ACTION" and incident_state["stage"] == "AWAITING_ATTACK_APPROVAL":
        async with message.channel.typing():
            await message.channel.send("⚡ **Attacker Agent:** Executing non-destructive read probe on live target...")
            exploit_res = await attacker_agent.execute_verified_exploit(incident_state["endpoint"])
            await message.channel.send(f"{exploit_res.get('conversational_report')}")

            # Fix Engine prepares Pre-Action Plan
            fix_plan = await fix_agent.formulate_remediation_plan({
                "title": incident_state["vuln"],
                "endpoint": incident_state["endpoint"]
            })
            incident_state["stage"] = "AWAITING_FIX_APPROVAL"
            await message.channel.send(f"{fix_plan.get('conversational_plan')}")
        return

    # 4. Confirm Fix & Remediation
    if intent == "CONFIRM_ACTION" and incident_state["stage"] == "AWAITING_FIX_APPROVAL":
        async with message.channel.typing():
            await message.channel.send("🛡️ **Fix Engine:** Deploying zero-downtime virtual shield and branching Git repository...")
            remediation_res = await fix_agent.execute_dual_remediation()
            await message.channel.send(f"{remediation_res.get('conversational_report')}")

            # Verifier conducts dual-path audit
            await message.channel.send("⚖️ **Verifier Agent:** Running independent dual-path traffic testing (Legitimate vs Exploit)...")
            audit_res = await verifier_agent.execute_verification_audit(incident_state["endpoint"])
            incident_state["stage"] = "RESOLVED"
            await message.channel.send(f"{audit_res.get('conversational_scorecard')}")
        return

    # General chat acknowledgment
    await message.channel.send("👋 **Kite SecOps:** I am standing by. You can ask me to audit any endpoint or check security posture!")

async def start_discord_bot():
    token = settings.DISCORD_BOT_TOKEN
    if not token or token == "your_discord_bot_token_here":
        logger.warning("DISCORD_BOT_TOKEN not provided in .env. Discord listener standing by.")
        return
    try:
        await bot.start(token)
    except Exception as e:
        logger.error(f"Error starting Discord Bot: {e}")
