import os
from dotenv import load_dotenv

# Ensure .env is discovered across container and host paths
for env_candidate in [".env", "../.env", "/app/.env"]:
    if os.path.exists(env_candidate):
        load_dotenv(dotenv_path=env_candidate, override=True)
        break
load_dotenv()

try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        from pydantic import BaseSettings
    except ImportError:
        class BaseSettings:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)

class Settings(BaseSettings):
    # API Keys & Tokens from .env
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO_OWNER: str = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME: str = os.getenv("GITHUB_REPO_NAME", "vynn")

    # Switch AI & Proxy Configuration
    SWITCH_TRUST_API_KEY: str = os.getenv("SWITCH_TRUST_API_KEY", "")
    SWITCH_TRUST_GATEWAY_URL: str = os.getenv("SWITCH_TRUST_GATEWAY_URL", "")
    SWITCH_SERVER_URL: str = os.getenv("SWITCH_SERVER_URL", "http://switch-server:3000")

    # Pinned Models
    RECON_MODEL: str = "gemini-3.1-flash-lite"
    ATTACKER_MODEL: str = "gpt-6-luna"
    FIX_ENGINE_MODEL: str = "gpt-6-luna"
    VERIFIER_MODEL: str = "gemini-3.1-flash-lite"

    # Infrastructure URLs
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://secops:secops_secure_pass@postgres:5432/cyberwar")
    
    # Target and Proxy URLs inside Docker Network
    TARGET_CONTAINER_NAME: str = "vynn"
    PROXY_CONTAINER_NAME: str = "nginx-proxy"
    TOOLS_CONTAINER_NAME: str = "kite-sec-tools"
    NGINX_PATCH_DIR: str = os.getenv("NGINX_PATCH_DIR", "/app/nginx_patches")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
