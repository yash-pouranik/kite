import json
import logging
from typing import Dict, Any, Optional
from google import genai
from config import settings

logger = logging.getLogger("cyberwar.nlu.dialogue")

class ConversationalDialogueManager:
    """
    Evaluates human messages in natural language:
    - Determines intent (request scan, provide clarification, approve/reject fix, general inquiry).
    - Checks for ambiguity and generates open clarifying questions if needed.
    """
    def __init__(self):
        self.api_key = settings.GOOGLE_AI_API_KEY
        self.model_name = settings.RECON_MODEL # gemini-3.1-flash-lite
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    async def analyze_human_turn(self, human_message: str, session_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Parses human conversational input into structured intent and clarification requirement.
        """
        if not self.client:
            # Fallback heuristic parser if API key is not yet provided
            msg_lower = human_message.lower()
            if any(word in msg_lower for word in ["scan", "audit", "check", "vulnerability", "profile"]):
                if not any(t in msg_lower for t in ["staging", "production", "juice-shop", "internal"]):
                    return {
                        "intent": "REQUEST_SCAN",
                        "is_ambiguous": True,
                        "clarification_prompt": "I noticed you'd like a security audit. Which environment should I profile (our internal staging store or public QA instance), and would you prefer a quick port audit or comprehensive vulnerability scan?",
                        "extracted_target": None
                    }
                return {
                    "intent": "REQUEST_SCAN",
                    "is_ambiguous": False,
                    "clarification_prompt": None,
                    "extracted_target": "juice-shop-staging"
                }
            elif any(w in msg_lower for w in ["yes", "proceed", "go ahead", "approve", "sounds solid", "apply"]):
                return {
                    "intent": "CONFIRM_ACTION",
                    "is_ambiguous": False,
                    "clarification_prompt": None,
                    "extracted_target": None
                }
            elif any(w in msg_lower for w in ["wait", "no", "don't", "stop", "reject"]):
                return {
                    "intent": "OVERRIDE_ACTION",
                    "is_ambiguous": False,
                    "clarification_prompt": None,
                    "feedback": human_message
                }
            return {
                "intent": "GENERAL_CHAT",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": None
            }

        system_instruction = (
            "You are an NLU engine for CyberWar-Room SecOps. "
            "Analyze the user's natural language message and session context. "
            "Return JSON with: "
            "'intent' (REQUEST_SCAN, CONFIRM_ACTION, OVERRIDE_ACTION, GENERAL_INQUIRY), "
            "'is_ambiguous' (true if target or scope is unclear, requiring clarification), "
            "'clarification_prompt' (a polite, professional clarifying question to ask the user, or null), "
            "'extracted_target' (target name/URL or null)."
        )

        try:
            prompt = f"User Message: {human_message}\nSession Context: {json.dumps(session_context or {})}"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "system_instruction": system_instruction,
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error in Gemini NLU analysis: {e}")
            return {
                "intent": "REQUEST_SCAN",
                "is_ambiguous": False,
                "clarification_prompt": None,
                "extracted_target": "juice-shop-staging"
            }
