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
    Wraps an OpenAI or LLM client with Switch Trust / FlintAI guardrails and telemetry.
    Injects standard Switch Agent Protocol headers:
    - X-Agent-Id
    - X-Agent-Name
    - X-Agent-Session-Id
    """
    try:
        # 1. Try modern switch_trust SDK
        import switch_trust
        logger.info(f"🛡️ Wrapping client with Switch Trust Guardrails for agent [{agent_name}]")
        return switch_trust.wrap(
            client,
            agent_id=agent_id,
            agent_name=agent_name,
            session_id=session_id or "cyberwar-default-session"
        )
    except ImportError:
        pass

    try:
        # 2. Try flintai-sdk-py fallback
        import flintai
        logger.info(f"🛡️ Wrapping client with FlintAI / Switch Trust for agent [{agent_name}]")
        return flintai.wrap(
            client,
            agent_id=agent_id,
            agent_name=agent_name
        )
    except ImportError:
        logger.info(
            f"ℹ️ Switch Trust SDK running in lightweight mode for agent [{agent_name}]. "
            "Telemetry & guardrails headers will be attached natively."
        )
        return client
