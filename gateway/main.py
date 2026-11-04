import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from config import settings
from routes.webhooks import router as switch_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("cyberwar.gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CyberWar-Room Gateway...")
    logger.info(f"Connecting to Switch Server at: {settings.SWITCH_SERVER_URL}")
    logger.info(f"Active Models: Recon={settings.RECON_MODEL}, Attacker={settings.ATTACKER_MODEL}, Fix={settings.FIX_ENGINE_MODEL}, Verifier={settings.VERIFIER_MODEL}")
    yield
    logger.info("Shutting down CyberWar-Room Gateway...")

app = FastAPI(
    title="CyberWar-Room Autonomous SecOps Gateway",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(switch_router)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "CyberWar-Room Event Gateway",
        "models": {
            "recon_bot": settings.RECON_MODEL,
            "attacker": settings.ATTACKER_MODEL,
            "fix_engine": settings.FIX_ENGINE_MODEL,
            "verifier": settings.VERIFIER_MODEL
        }
    }
