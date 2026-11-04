import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_AI_API_KEY: str = os.getenv("GOOGLE_AI_API_KEY", "")
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO_OWNER: str = os.getenv("GITHUB_REPO_OWNER", "")
    GITHUB_REPO_NAME: str = os.getenv("GITHUB_REPO_NAME", "juice-shop")

    # Pinned Models
    RECON_MODEL: str = "gemini-3.1-flash-lite"
    ATTACKER_MODEL: str = "gpt-6-luna"
    FIX_ENGINE_MODEL: str = "gpt-6-luna"
    VERIFIER_MODEL: str = "gemini-3.1-flash-lite"

    # Infrastructure URLs
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://secops:secops_secure_pass@postgres:5432/cyberwar")
    SWITCH_SERVER_URL: str = os.getenv("SWITCH_SERVER_URL", "http://switch-server:3000")
    
    # Target and Proxy URLs inside Docker Network
    TARGET_CONTAINER_NAME: str = "juice-shop"
    PROXY_CONTAINER_NAME: str = "nginx-proxy"
    TOOLS_CONTAINER_NAME: str = "sec-tools"
    NGINX_PATCH_DIR: str = os.getenv("NGINX_PATCH_DIR", "/app/nginx_patches")

    class Config:
        env_file = ".env"

settings = Settings()
