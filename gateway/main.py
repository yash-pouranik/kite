import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from routes.webhooks import router as switch_router
from services.discord_runner import start_discord_bot
from services.switch_client import SwitchAgentProtocolClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberwar.gateway")

switch_client = SwitchAgentProtocolClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Kite SecOps Gateway & Autonomous Agents...")
    openai_masked = f"{settings.OPENAI_API_KEY[:7]}...{settings.OPENAI_API_KEY[-4:]}" if len(settings.OPENAI_API_KEY) > 12 else "NOT_SET"
    gemini_masked = f"{settings.GOOGLE_AI_API_KEY[:6]}...{settings.GOOGLE_AI_API_KEY[-4:]}" if len(settings.GOOGLE_AI_API_KEY) > 10 else "NOT_SET"
    logger.info(f"Credentials Verified: OpenAI=[{openai_masked}], Gemini=[{gemini_masked}], Discord=[{'SET' if settings.DISCORD_BOT_TOKEN else 'NOT_SET'}]")
    logger.info(f"Active Models: Recon={settings.RECON_MODEL}, Attacker={settings.ATTACKER_MODEL}, Fix={settings.FIX_ENGINE_MODEL}, Verifier={settings.VERIFIER_MODEL}")
    
    # 1. Launch Switch Agent Protocol client (WebSocket to Switch Rooms)
    switch_client.start_background_task()

    # 2. Launch Discord Bot listener in background asyncio task if direct fallback is enabled
    if settings.ENABLE_DIRECT_DISCORD_FALLBACK:
        logger.info("Direct Discord bot fallback is ENABLED. Starting direct discord runner...")
        asyncio.create_task(start_discord_bot())
    else:
        logger.info("Direct Discord bot is in STANDBY (Official Switch Rooms Bridge is primary).")
    
    yield
    logger.info("Shutting down Kite SecOps Gateway...")

app = FastAPI(
    title="Kite Autonomous SecOps Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(switch_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Kite Autonomous SecOps Gateway",
        "switch_bridge": {
            "connected": switch_client.is_connected,
            "room": settings.SWITCH_ROOM_ID,
            "agent_id": settings.SWITCH_AGENT_ID
        },
        "models": {
            "recon_bot": settings.RECON_MODEL,
            "attacker": settings.ATTACKER_MODEL,
            "fix_engine": settings.FIX_ENGINE_MODEL,
            "verifier": settings.VERIFIER_MODEL
        }
    }

@app.get("/switch/status")
async def switch_status():
    return {
        "status": "online",
        "switch_server_url": settings.SWITCH_SERVER_URL,
        "room_id": settings.SWITCH_ROOM_ID,
        "agent_id": settings.SWITCH_AGENT_ID,
        "is_connected": switch_client.is_connected,
        "recent_history_count": len(switch_client.room_history),
        "protocol": "Official Switch Agent Protocol (WebSocket + HTTP)"
    }
