import asyncio
import json
import logging
import httpx
from typing import Dict, Any, Callable, Optional
from config import settings

logger = logging.getLogger("cyberwar.switch.client")

class SwitchAgentProtocolClient:
    """
    Implements the official Switch Agent Protocol:
    1. Listens for live room events (mentions, human messages) over SSE or WebSocket stream.
    2. Sends tool operations and conversational replies via HTTP POST against the Switch Agent Bridge.
    """
    def __init__(self, switch_url: str = settings.SWITCH_SERVER_URL):
        self.switch_url = switch_url.rstrip("/")
        self.is_connected = False
        self._listener_task: Optional[asyncio.Task] = None

    async def send_room_message(self, room_name: str, agent_name: str, content: str) -> bool:
        """
        Sends an HTTP call to Switch Agent Bridge to post a message into the room/Discord channel.
        """
        url = f"{self.switch_url}/api/rooms/{room_name}/messages"
        payload = {
            "agent": agent_name,
            "content": content
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                res = await client.post(url, json=payload)
                if res.status_code in [200, 201]:
                    logger.info(f"Message delivered to Switch Room [{room_name}] by @{agent_name}")
                    return True
                else:
                    logger.warning(f"Switch Agent Bridge returned status {res.status_code}: {res.text}")
                    return False
            except Exception as e:
                logger.error(f"Failed to post message to Switch Bridge: {e}")
                return False

    async def start_event_stream_listener(self, on_event_callback: Callable[[Dict[str, Any]], Any]):
        """
        Connects to Switch Agent Bridge's SSE / Event stream (/api/events or /api/agent/stream)
        and forwards events to our multi-agent gateway handler.
        """
        stream_url = f"{self.switch_url}/api/agent/stream"
        logger.info(f"Connecting to Switch Agent Protocol stream at: {stream_url}")

        while True:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", stream_url) as response:
                        if response.status_code != 200:
                            logger.warning(f"Switch stream returned status {response.status_code}. Retrying in 5s...")
                            await asyncio.sleep(5)
                            continue

                        self.is_connected = True
                        logger.info("Connected to Switch Live Event Stream successfully.")
                        
                        async for line in response.aiter_lines():
                            if line.startswith("data:"):
                                raw_json = line[len("data:"):].strip()
                                if raw_json:
                                    try:
                                        event_data = json.loads(raw_json)
                                        await on_event_callback(event_data)
                                    except Exception as err:
                                        logger.error(f"Error handling event payload: {err}")
            except Exception as e:
                self.is_connected = False
                logger.warning(f"Switch stream disconnected ({e}). Reconnecting in 5s...")
                await asyncio.sleep(5)
