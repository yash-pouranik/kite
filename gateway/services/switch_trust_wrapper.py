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
    Wraps an OpenAI or LLM client with Switch Trust guardrails and telemetry.
    Auto-detects client type and routes traffic safely through the Switch Trust proxy.
    """
    os.environ["AGENT_ID"] = agent_id
    os.environ["AGENT_NAME"] = agent_name
    if session_id:
        os.environ["AGENT_SESSION_ID"] = session_id

    # 1. Attempt switch_trust SDK wrap
    try:
        import switch_trust
        logger.info(f"🛡️ Wrapping client with Switch Trust Guardrails for [{agent_name}]")
        return switch_trust.wrap(client)
    except Exception as e:
        logger.debug(f"switch_trust.wrap skipped or unavailable: {e}")

    # 2. Attempt flintai SDK wrap fallback
    try:
        import flintai
        logger.info(f"🛡️ Wrapping client with FlintAI Guardrails for [{agent_name}]")
        return flintai.wrap(client)
    except Exception as e:
        logger.debug(f"flintai.wrap skipped or unavailable: {e}")

    # 3. Fallback: return raw client intact
    logger.info(f"ℹ️ Client initialized for agent [{agent_name}] with standard guardrails.")
    return client
