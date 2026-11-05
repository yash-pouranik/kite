import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from routes.webhooks import router as switch_router
from services.discord_runner import start_discord_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberwar.gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Kite SecOps Gateway & Autonomous Agents...")
    openai_masked = f"{settings.OPENAI_API_KEY[:7]}...{settings.OPENAI_API_KEY[-4:]}" if len(settings.OPENAI_API_KEY) > 12 else "NOT_SET"
    gemini_masked = f"{settings.GOOGLE_AI_API_KEY[:6]}...{settings.GOOGLE_AI_API_KEY[-4:]}" if len(settings.GOOGLE_AI_API_KEY) > 10 else "NOT_SET"
    logger.info(f"Credentials Verified: OpenAI=[{openai_masked}], Gemini=[{gemini_masked}], Discord=[{'SET' if settings.DISCORD_BOT_TOKEN else 'NOT_SET'}]")
    logger.info(f"Active Models: Recon={settings.RECON_MODEL}, Attacker={settings.ATTACKER_MODEL}, Fix={settings.FIX_ENGINE_MODEL}, Verifier={settings.VERIFIER_MODEL}")
    
    # Launch Discord Bot listener in background asyncio task
    asyncio.create_task(start_discord_bot())
    
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
        "models": {
            "recon_bot": settings.RECON_MODEL,
            "attacker": settings.ATTACKER_MODEL,
            "fix_engine": settings.FIX_ENGINE_MODEL,
            "verifier": settings.VERIFIER_MODEL
        }
    }
