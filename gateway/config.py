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
    
    # Target Application & Infrastructure (100% Configurable from .env)
    TARGET_HOST: str = os.getenv("TARGET_HOST", "target-app")
    TARGET_CONTAINER_NAME: str = os.getenv("TARGET_CONTAINER_NAME", os.getenv("TARGET_HOST", "target-app"))
    HOST_REPO_PATH: str = os.getenv("HOST_REPO_PATH", "/app/target_repo")
    K8S_NAMESPACE: str = os.getenv("K8S_NAMESPACE", "default")

    # GitHub GitOps Integration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO_OWNER: str = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME: str = os.getenv("GITHUB_REPO_NAME", "")

    # Switch AI & Switch Rooms Configuration
    SWITCH_TRUST_API_KEY: str = os.getenv("SWITCH_TRUST_API_KEY", "")
    SWITCH_TRUST_GATEWAY_URL: str = os.getenv("SWITCH_TRUST_GATEWAY_URL", "")
    SWITCH_SERVER_URL: str = os.getenv("SWITCH_SERVER_URL", "http://switch-server:8000")
    SWITCH_AGENT_REGISTRATION_TOKEN: str = os.getenv("SWITCH_AGENT_REGISTRATION_TOKEN", "secops-switch-token-2026")
    SWITCH_AGENT_ID: str = os.getenv("SWITCH_AGENT_ID", "kite-secops")
    SWITCH_AGENT_API_KEY: str = os.getenv("SWITCH_AGENT_API_KEY", "")
    SWITCH_ROOM_ID: str = os.getenv("SWITCH_ROOM_ID", "cyberwar-ops")
    ENABLE_DIRECT_DISCORD_FALLBACK: bool = os.getenv("ENABLE_DIRECT_DISCORD_FALLBACK", "false").lower() in ("true", "1", "yes")

    # Pinned Models
    RECON_MODEL: str = os.getenv("RECON_MODEL", "gemini-3.1-flash-lite")
    ATTACKER_MODEL: str = os.getenv("ATTACKER_MODEL", "gpt-6-luna")
    FIX_ENGINE_MODEL: str = os.getenv("FIX_ENGINE_MODEL", "gpt-6-luna")
    VERIFIER_MODEL: str = os.getenv("VERIFIER_MODEL", "gemini-3.1-flash-lite")

    # Infrastructure URLs
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://secops:secops_secure_pass@postgres:5432/cyberwar")
    
    # Containers & Paths
    PROXY_CONTAINER_NAME: str = os.getenv("PROXY_CONTAINER_NAME", "nginx-proxy")
    TOOLS_CONTAINER_NAME: str = os.getenv("TOOLS_CONTAINER_NAME", "kite-sec-tools")
    NGINX_PATCH_DIR: str = os.getenv("NGINX_PATCH_DIR", "/app/nginx_patches")

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
