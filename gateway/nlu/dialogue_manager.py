import json
import logging
from typing import Dict, Any, Optional
from google import genai
from config import settings

logger = logging.getLogger("cyberwar.nlu.dialogue")

class ConversationalDialogueManager:
    """
    Evaluates human messages in natural language:
    - Maintains conversational memory across turns.
    - Determines intent (request scan, confirm action, override, inquire).
    - Extracts specific targets and focus areas (e.g. auth, nginx, endpoints).
    - Checks for ambiguity and generates open clarifying questions if needed.
    """
    def __init__(self):
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.model_name = settings.RECON_MODEL # gemini-3.1-flash-lite
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.session_memory: Dict[str, Any] = {
            "last_target": "vynn.urbackend.in",
            "last_focus": None
        }

    async def analyze_human_turn(self, human_message: str, session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses human conversational input into structured intent, target, and focus area.
        """
        msg_lower = human_message.lower()

        # Heuristic focus extraction
        focus_area = None
        if "auth" in msg_lower or "login" in msg_lower or "jwt" in msg_lower:
            focus_area = "auth"
            self.session_memory["last_focus"] = "auth"
        elif "nginx" in msg_lower or "waf" in msg_lower or "proxy" in msg_lower:
            focus_area = "nginx"
            self.session_memory["last_focus"] = "nginx"
        elif self.session_memory.get("last_focus"):
            focus_area = self.session_memory["last_focus"]

        # Target extraction
        target = None
        if "vynn" in msg_lower:
            target = "vynn.urbackend.in"
            self.session_memory["last_target"] = target
        elif "http" in msg_lower:
            for part in human_message.split():
                if "http" in part:
                    target = part.strip("<>").rstrip("/")
                    self.session_memory["last_target"] = target
                    break
        elif self.session_memory.get("last_target"):
            target = self.session_memory["last_target"]

        # Confirmations
        if any(w in msg_lower for w in ["yes", "proceed", "go ahead", "approve", "sounds solid", "apply", "haan", "karo", "verify"]):
            return {
                "intent": "CONFIRM_ACTION",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": target,
                "focus_area": focus_area
            }

        # Scan requests
        if any(word in msg_lower for word in ["scan", "audit", "check", "vulnerability", "profile", "issue", "security"]):
            return {
                "intent": "REQUEST_SCAN",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": target or "vynn.urbackend.in",
                "focus_area": focus_area
            }

        if not self.client:
            return {
                "intent": "GENERAL_CHAT",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": target,
                "focus_area": focus_area
            }

        # Gemini LLM Parser
        system_instruction = (
            "You are an NLU engine for Kite SecOps. Analyze user message and maintain context. "
            "Return JSON with: "
            "'intent' (REQUEST_SCAN, CONFIRM_ACTION, OVERRIDE_ACTION, GENERAL_INQUIRY), "
            "'is_ambiguous' (true only if zero context or target exists), "
            "'clarification_prompt' (clarifying question if ambiguous, or null), "
            "'extracted_target' (target URL/domain, e.g. vynn.urbackend.in), "
            "'focus_area' (auth, nginx, endpoints, or null)."
        )

        try:
            prompt = f"User Message: {human_message}\nSession Memory: {json.dumps(self.session_memory)}"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json"
                }
            )
            parsed = json.loads(response.text)
            if not parsed.get("extracted_target"):
                parsed["extracted_target"] = self.session_memory.get("last_target", "vynn.urbackend.in")
            if not parsed.get("focus_area"):
                parsed["focus_area"] = focus_area
            return parsed
        except Exception as e:
            logger.error(f"Error in Gemini NLU analysis: {e}")
            return {
                "intent": "REQUEST_SCAN",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": target or "vynn.urbackend.in",
                "focus_area": focus_area
            }
