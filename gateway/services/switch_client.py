import asyncio
import json
import logging
import uuid
import httpx
from typing import Dict, Any, List, Optional
try:
    import websockets
except ImportError:
    websockets = None

from config import settings
from agents.agent_engine import KiteAgentEngine

logger = logging.getLogger("cyberwar.switch.client")

class SwitchAgentProtocolClient:
    """
    Official Switch Agent Protocol Client:
    - Registers agent with Switch Server (/agents)
    - Updates addressing policy (/agents/{agent_id}/ops/update_agent_detail)
    - Connects over WebSocket (/agents/{agent_id}/connection/ws)
    - Listens for Room events, multi-turn history, and mentions
    - Dispatches turns to KiteAgentEngine (28 DevSecOps & K8s tools)
    - Posts replies back into Switch Rooms (/agents/{agent_id}/message)
    """

    def __init__(self, agent_engine: Optional[KiteAgentEngine] = None):
        self.switch_url = settings.SWITCH_SERVER_URL.rstrip("/")
        # Convert http(s) to ws(s)
        if self.switch_url.startswith("https://"):
            self.ws_base_url = "wss://" + self.switch_url[len("https://"):]
        elif self.switch_url.startswith("http://"):
            self.ws_base_url = "ws://" + self.switch_url[len("http://"):]
        else:
            self.ws_base_url = f"ws://{self.switch_url}"

        self.agent_id = settings.SWITCH_AGENT_ID or "kite-secops"
        self.agent_api_key = settings.SWITCH_AGENT_API_KEY
        self.registration_token = settings.SWITCH_AGENT_REGISTRATION_TOKEN
        self.room_id = settings.SWITCH_ROOM_ID or "cyberwar-ops"
        self.connection_id = str(uuid.uuid4())
        
        self.agent_engine = agent_engine or KiteAgentEngine()
        self.is_connected = False
        self.room_history: List[str] = []
        self._task: Optional[asyncio.Task] = None
        self.last_cursor: Optional[int] = None
        self.generation: Optional[int] = None

    async def check_health(self) -> bool:
        """Probes Switch Bridge /health endpoint."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(f"{self.switch_url}/health")
                return res.status_code == 200
        except Exception:
            return False

    async def register_agent(self) -> bool:
        """
        Registers Kite with the Switch Server if no agent API key is configured.
        Uses the AGENT_REGISTRATION_TOKEN bootstrap key.
        """
        if self.agent_api_key:
            return True

        if not self.registration_token:
            logger.info("No SWITCH_AGENT_API_KEY or REGISTRATION_TOKEN provided; using agent_id as token.")
            self.agent_api_key = self.agent_id
            return True

        url = f"{self.switch_url}/agents"
        headers = {"Authorization": f"Bearer {self.registration_token}"}
        payload = {
            "name": self.agent_id,
            "description": "Autonomous Multi-Agent SecOps Teammate for Kubernetes and Cloud Infrastructure",
            "connector_type": "websocket",
            "integration_profile": {
                "connection_model": "always_on",
                "message_exchange": True
            },
            "overwrite": True
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    data = res.json()
                    self.agent_api_key = data.get("api_key", self.agent_api_key)
                    self.agent_id = data.get("agent_id", self.agent_id)
                    logger.info(f"Registered agent with Switch Server: ID={self.agent_id}")
                    return True
                else:
                    logger.warning(f"Switch registration returned {res.status_code}: {res.text}")
                    return False
        except Exception as e:
            logger.warning(f"Could not register with Switch Server: {e}")
            return False

    async def configure_addressing(self) -> bool:
        """
        Configures the agent so anyone in the Switch Room can instruct it:
        POST /agents/{agent_id}/ops/update_agent_detail -> addressing: 'anyone'
        """
        url = f"{self.switch_url}/agents/{self.agent_id}/ops/update_agent_detail"
        headers = {
            "Authorization": f"Bearer {self.agent_api_key}",
            "X-Connection-Id": self.connection_id
        }
        payload = {
            "agent_id": self.agent_id,
            "addressing": "anyone"
        }
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                return res.status_code in [200, 204]
        except Exception as e:
            logger.debug(f"Could not set addressing (normal if standalone mock): {e}")
            return False

    async def send_room_message(self, room_id: str, content: str) -> bool:
        """
        Posts an agent reply into the Switch Room:
        POST /agents/{agent_id}/message
        """
        url = f"{self.switch_url}/agents/{self.agent_id}/message"
        headers = {"Authorization": f"Bearer {self.agent_api_key}"}
        payload = {
            "room_id": room_id,
            "content": content
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code in [200, 201]:
                    logger.info(f"Reply posted to Switch Room [{room_id}]")
                    return True
                else:
                    logger.warning(f"Failed to post to Switch Room ({res.status_code}): {res.text}")
                    return False
        except Exception as e:
            logger.error(f"Error posting message to Switch Room: {e}")
            return False

    async def _handle_incoming_frame(self, raw_data: str, ws):
        """Processes frames arriving from the Switch Room WebSocket connection."""
        try:
            data = json.loads(raw_data)
        except Exception:
            return

        msg_type = data.get("type", "")

        # 1. Answer heartbeat pings with cursor acknowledgment
        if msg_type == "ping":
            pong_payload = {"type": "pong", "cursor": self.last_cursor}
            await ws.send(json.dumps(pong_payload))
            return

        # 2. Connection state updates
        if msg_type == "connection_state":
            self.generation = data.get("generation")
            self.last_cursor = data.get("cursor")
            logger.info(f"Switch Room connected: generation={self.generation}, cursor={self.last_cursor}")
            return

        # 3. Handle live room message events
        if msg_type == "message":
            self.last_cursor = data.get("cursor", self.last_cursor)
            payload = data.get("payload", {})
            room_id = data.get("room_id", self.room_id)
            sender_name = payload.get("sender_name", "User")
            body = payload.get("body", "").strip()
            addressed = payload.get("addressed", False)

            # Auto-detect address if Kite or bot name is mentioned
            if not addressed and any(tag in body.lower() for tag in ["@kite", "kite", "@secops", "kite-secops"]):
                addressed = True

            # Track shared room context
            self.room_history.append(f"{sender_name}: {body}")
            if len(self.room_history) > 20:
                self.room_history = self.room_history[-20:]

            logger.info(f"Switch Room [{room_id}] Message from {sender_name}: '{body}' (addressed={addressed})")

            # If message is addressed to the agent, process with full DevSecOps engine
            if addressed and body:
                logger.info(f"Kite executing turn for Switch Room: '{body}'")
                response_text = await self.agent_engine.process_chat_turn(
                    user_message=body,
                    room_history=self.room_history
                )
                self.room_history.append(f"Kite-Agent: {response_text}")
                await self.send_room_message(room_id, response_text)

    async def run(self):
        """
        Persistent background loop maintaining connection to Switch Server.
        Automatically handles retries, reconnects, and socket keep-alive.
        """
        logger.info(f"Initializing Switch Agent Protocol Client (Server: {self.switch_url})")

        while True:
            try:
                # 1. Check if Switch Server is online
                healthy = await self.check_health()
                if not healthy:
                    self.is_connected = False
                    logger.debug(f"Switch Server at {self.switch_url} unreachable. Retrying in 10s...")
                    await asyncio.sleep(10)
                    continue

                # 2. Register agent and configure addressing
                await self.register_agent()
                await self.configure_addressing()

                # 3. Connect to WebSocket
                ws_url = (
                    f"{self.ws_base_url}/agents/{self.agent_id}/connection/ws"
                    f"?connection_id={self.connection_id}&rooms={self.room_id}&filter=all"
                )
                headers = {"Authorization": f"Bearer {self.agent_api_key}"}

                if websockets is None:
                    logger.warning("websockets package not installed. Skipping live socket.")
                    await asyncio.sleep(15)
                    continue

                logger.info(f"Connecting to Switch Room WebSocket: {ws_url}")
                async with websockets.connect(ws_url, extra_headers=headers) as ws:
                    self.is_connected = True
                    logger.info(f"Successfully joined Switch Room [{self.room_id}] as @{self.agent_id}!")

                    async for raw_message in ws:
                        await self._handle_incoming_frame(raw_message, ws)

            except asyncio.CancelledError:
                logger.info("Switch Agent Client loop cancelled.")
                break
            except Exception as e:
                self.is_connected = False
                logger.warning(f"Switch Room connection dropped ({e}). Reconnecting in 8s...")
                await asyncio.sleep(8)

    def start_background_task(self):
        """Spawns client in background asyncio task."""
        if not self._task or self._task.done():
            self._task = asyncio.create_task(self.run())
        return self._task
