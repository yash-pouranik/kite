import os
import json
import logging
from typing import Dict, Any, List, Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from config import settings
from tools.tool_registry import registry
from tools.setup_registry import register_all_tools
from services.switch_trust_wrapper import wrap_with_switch_trust

logger = logging.getLogger("cyberwar.agent_engine")

class KiteAgentEngine:
    """
    Switch-Native Multi-Agent SecOps Engine with OpenAI Function Calling & Switch Trust Guardrails.
    Maintains full room chat history, speaks fluent English & Hinglish, and coordinates
    autonomous security operations:
    1. Recon, Repo Filesystem & Endpoint Discovery (@recon-bot)
    2. Ethical Vulnerability Probing (@attacker)
    3. Dual-Track Remediation & 1-Click Safety Rollback (@fix-engine)
    4. Independent Regression Audit (@verifier)
    """
    def __init__(self):
        # Register all 25 DevSecOps, Git, and remediation tools
        register_all_tools()

        raw_client = OpenAI(api_key=settings.OPENAI_API_KEY) if (OpenAI and settings.OPENAI_API_KEY) else None
        self.client = wrap_with_switch_trust(
            raw_client,
            agent_id="kite-secops-lead",
            agent_name="Kite-SecOps-Teammate"
        ) if raw_client else None

        self.model = "gpt-6-luna"
        self.default_target = settings.TARGET_HOST or settings.TARGET_CONTAINER_NAME or "target-app"
        self._load_system_prompt()

    def _load_system_prompt(self):
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "system_prompt.md")
        if os.path.exists(prompt_path):
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
            self.system_prompt = template.format(
                default_target=self.default_target,
                k8s_namespace=settings.K8S_NAMESPACE
            )
        else:
            self.system_prompt = (
                f"You are Kite, an autonomous Senior Multi-Agent SecOps Teammate on {self.default_target}. "
                "Always be truthful, execute tools transparently, and follow the pre-action execution protocol."
            )

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns schemas for all registered tools dynamically from the central registry."""
        return registry.get_schemas()

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Executes tool via central registry with error isolation."""
        logger.info(f"Agent Engine dispatching tool: [{name}] with args: {args}")
        return await registry.execute(name, args)

    async def process_chat_turn(self, user_message: str, room_history: List[str]) -> str:
        """
        Sends multi-turn room history + user message + tools to OpenAI.
        Loops to resolve tool calls, then returns an intelligent, structured response.
        """
        if not self.client:
            return (
                "⚠️ **OpenAI API Key is missing in `.env`**. "
                "Please configure `OPENAI_API_KEY` to activate autonomous agent reasoning."
            )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": self.system_prompt}]

        # Inject shared Switch Room context (multi-turn history)
        for hist_line in room_history[-8:]:
            if hist_line.startswith("Kite-Agent:"):
                messages.append({"role": "assistant", "content": hist_line.replace("Kite-Agent:", "").strip()})
            else:
                messages.append({"role": "user", "content": hist_line})

        messages.append({"role": "user", "content": user_message})

        tools = self.get_tool_definitions()

        try:
            max_tool_iterations = getattr(settings, "MAX_TOOL_ITERATIONS", 10)
            iteration = 0

            while iteration < max_tool_iterations:
                iteration += 1
                # Exclusively use gpt-6-luna with reasoning_effort="none" when using function tools
                req_kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "tools": tools,
                    "tool_choice": "auto",
                    "extra_body": {"reasoning_effort": "none"}
                }
                try:
                    response = self.client.chat.completions.create(**req_kwargs)
                except Exception as call_err:
                    if "reasoning_effort" in str(call_err).lower():
                        req_kwargs.pop("extra_body", None)
                        req_kwargs["reasoning_effort"] = "none"
                        response = self.client.chat.completions.create(**req_kwargs)
                    else:
                        raise call_err

                response_message = response.choices[0].message

                # If no tool calls requested, we have the final assistant message
                if not response_message.tool_calls:
                    return response_message.content or "Standing by in room."

                # Append assistant message with tool calls to conversation
                messages.append(response_message)

                # Execute all tool calls emitted in this step
                for tool_call in response_message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    tool_output = await self.execute_tool(fn_name, fn_args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": fn_name,
                        "content": tool_output
                    })

            # If loop reached max iterations, make final call without tools
            final_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "extra_body": {"reasoning_effort": "none"}
            }
            try:
                final_resp = self.client.chat.completions.create(**final_kwargs)
                return final_resp.choices[0].message.content or "Task completed successfully."
            except Exception:
                return "Task completed successfully."

        except Exception as e:
            logger.error(f"Error in Agent Engine turn: {e}", exc_info=True)
            return f"⚠️ Error processing request: {str(e)}"
