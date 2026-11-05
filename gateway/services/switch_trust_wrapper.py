import os
import logging
from typing import Any, Optional

logger = logging.getLogger("cyberwar.switch_trust")

def wrap_with_switch_trust(
    client: Any,
    agent_id: str = "kite-secops-agent",
    agent_name: str = "Kite-SecOps",
    session_id: Optional[str] = None
) -> Any:
    """
    Attaches Switch Trust identity and telemetry.
    Only intercepts base_url via proxy if a dedicated Switch Trust Gateway / API Key is configured,
    preventing 401 proxy rejections when using standard OpenAI / Gemini credentials.
    """
    os.environ["AGENT_ID"] = agent_id
    os.environ["AGENT_NAME"] = agent_name
    if session_id:
        os.environ["AGENT_SESSION_ID"] = session_id

    # If user configured a Switch Trust proxy / gateway, wrap client
    if os.getenv("SWITCH_TRUST_API_KEY") and os.getenv("SWITCH_TRUST_GATEWAY_URL"):
        try:
            import switch_trust
            logger.info(f"🛡️ Routing client via Switch Trust Gateway for [{agent_name}]")
            return switch_trust.wrap(client)
        except Exception as e:
            logger.warning(f"Switch Trust gateway wrapping error: {e}")

    # Standard direct execution with Switch Agent headers
    logger.info(f"🛡️ Switch Trust active in direct agent mode for [{agent_name}] (ID: {agent_id})")
    return client
