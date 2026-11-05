import os
import json
import logging
from typing import Dict, Any, List, Optional
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from config import settings
from tools.web_discovery import crawl_and_discover_target
from services.knowledge_manager import KnowledgeBaseManager
from tools.scanner_runner import SandboxedScannerRunner
from tools.exploit_runner import SafeExploitToolkit
from services.virtual_patcher import NginxVirtualPatcher
from services.github_service import GitHubGitOpsService
from tools.verifier_suite import DualPathAuditSuite
from services.switch_trust_wrapper import wrap_with_switch_trust

logger = logging.getLogger("cyberwar.agent_engine")

class KiteAgentEngine:
    """
    Switch-Native Multi-Agent SecOps Engine with OpenAI Function Calling & Switch Trust Guardrails.
    Maintains full room chat history, speaks fluent English & Hinglish, and coordinates
    autonomous security operations:
    1. Recon & Endpoint Discovery (@recon-bot)
    2. Ethical Vulnerability Probing (@attacker)
    3. Dual-Track Remediation: Nginx WAF + Git PR (@fix-engine)
    4. Independent Regression Audit (@verifier)
    """
    def __init__(self):
        raw_client = OpenAI(api_key=settings.OPENAI_API_KEY) if (OpenAI and settings.OPENAI_API_KEY) else None
        self.client = wrap_with_switch_trust(
            raw_client,
            agent_id="kite-secops-lead",
            agent_name="Kite-SecOps-Teammate"
        ) if raw_client else None

        self.model = "gpt-6-luna"
        self.kb = KnowledgeBaseManager()
        self.scanner = SandboxedScannerRunner()
        self.exploit = SafeExploitToolkit()
        self.patcher = NginxVirtualPatcher()
        self.github = GitHubGitOpsService()
        self.verifier = DualPathAuditSuite(target_host=settings.TARGET_CONTAINER_NAME or "vynn.urbackend.in")
        self.default_target = settings.TARGET_CONTAINER_NAME or "vynn.urbackend.in"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "discover_target_endpoints",
                    "description": "Crawls the target application web bundles, inspects HTTP response headers, and extracts live API routes and authentication endpoints.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_url": {
                                "type": "string",
                                "description": "The base URL or domain to crawl, e.g. https://vynn.urbackend.in"
                            }
                        },
                        "required": ["target_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_knowledge_base",
                    "description": "Reads persistent knowledge files (target_overview, auth_mechanisms, api_inventory) to check discovered intelligence and completeness score.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["target_overview", "auth_mechanisms", "api_inventory"],
                                "description": "Category of knowledge to retrieve."
                            }
                        },
                        "required": ["category"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_security_scan",
                    "description": "Executes sandboxed Nmap port detection and Nuclei security template scans against an asset or endpoint.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target hostname, IP, or full URL, e.g. vynn.urbackend.in"
                            }
                        },
                        "required": ["target"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_safe_exploit_probe",
                    "description": "Fires a non-destructive, read-only proof-of-concept verification probe to confirm if an endpoint or parameter has active security flaws (e.g. SQLi / auth bypass).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "The target endpoint path, e.g. /api/v1/auth/login"
                            },
                            "payload": {
                                "type": "string",
                                "description": "The harmless test payload string, e.g. ' OR 1=1 --"
                            }
                        },
                        "required": ["endpoint", "payload"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "apply_virtual_shield",
                    "description": "Deploys a zero-downtime Nginx reverse proxy virtual patch (regex inspection rule) and reloads Nginx dynamically in 5ms.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "The endpoint to protect, e.g. /api/v1/auth/login"
                            }
                        },
                        "required": ["endpoint"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_github_pr",
                    "description": "Opens a real GitHub Pull Request with a permanent source code fix (e.g. prepared parameterized statements) on the repository.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "vulnerability": {
                                "type": "string",
                                "description": "Name or type of vulnerability being patched."
                            },
                            "target_file": {
                                "type": "string",
                                "description": "Path to file being fixed, e.g. src/auth/login.ts"
                            }
                        },
                        "required": ["vulnerability", "target_file"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "verify_dual_track_remediation",
                    "description": "Performs independent regression audit: tests that legitimate customer traffic returns 200 OK while exploit payloads are blocked with 403 Forbidden.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "Endpoint to audit."
                            }
                        },
                        "required": ["endpoint"]
                    }
                }
            }
        ]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        logger.info(f"Agent Engine executing tool: [{name}] with args: {args}")
        try:
            if name == "discover_target_endpoints":
                url = args.get("target_url") or f"https://{self.default_target}"
                result = await crawl_and_discover_target(url)
                self.kb.save_or_update_knowledge(
                    category="api_inventory",
                    data=result,
                    agent_name="recon-bot",
                    discovery_method="web_bundle_crawler"
                )
                return json.dumps(result, indent=2)

            elif name == "read_knowledge_base":
                cat = args.get("category", "api_inventory")
                kb_data = self.kb.get_knowledge(cat)
                return json.dumps(kb_data or {"status": "empty", "completeness": 0, "message": "No data discovered yet."}, indent=2)

            elif name == "run_security_scan":
                target = args.get("target") or self.default_target
                target_url = target if target.startswith("http") else f"https://{target}"
                res = await self.scanner.run_nuclei_scan(target_url)
                return json.dumps(res, indent=2)

            elif name == "verify_safe_exploit_probe":
                endpoint = args.get("endpoint", "/api/v1/auth/login")
                payload = args.get("payload", "' OR 1=1 --")
                res = await self.exploit.verify_sqli_probe(endpoint=endpoint, payload=payload)
                return json.dumps(res, indent=2)

            elif name == "apply_virtual_shield":
                endpoint = args.get("endpoint", "/api/v1/auth/login")
                res = await self.patcher.apply_virtual_patch()
                return json.dumps(res, indent=2)

            elif name == "create_github_pr":
                vuln = args.get("vulnerability", "Authentication Vulnerability")
                target_file = args.get("target_file", "src/auth/login.ts")
                res = await self.github.create_security_fix_pr(
                    vulnerability=vuln,
                    target_file=target_file
                )
                return json.dumps(res, indent=2)

            elif name == "verify_dual_track_remediation":
                endpoint = args.get("endpoint", "/api/v1/auth/login")
                res = await self.verifier.execute_dual_path_audit(endpoint=endpoint)
                return json.dumps(res, indent=2)

            return json.dumps({"error": f"Unknown tool {name}"})
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return json.dumps({"error": str(e), "status": "failed"})

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

        system_prompt = (
            "You are Kite, an autonomous, highly capable Multi-Agent SecOps Teammate built for the Flip the Switch Hackathon. "
            "You live in this Switch Room (Discord channel) alongside human security leads and engineers.\n\n"
            f"TARGET ENVIRONMENT:\n"
            f"- Default Target Host: {self.default_target} (AWS EC2 Production/Staging)\n"
            f"- Local Repository: /home/ubuntu/vynn on EC2\n"
            f"- Architecture: Switch-Native Multi-Agent System with Switch Trust Guardrails\n\n"
            "YOUR SQUAD PERSONAS:\n"
            "1. @recon-bot: Asset discovery, web bundle spidering, API route extraction, Nmap/Nuclei scanning.\n"
            "2. @attacker: Ethical penetration testing, safe read-only PoC probes (' OR 1=1 --) to eliminate false positives.\n"
            "3. @fix-engine: Dual-Track Remediation — Zero-downtime Nginx virtual shield (`nginx -s reload`) + Git Pull Request automation.\n"
            "4. @verifier: Independent QA auditor — Confirms normal traffic (200 OK) while attack vectors are blocked (403 Forbidden).\n\n"
            "CRITICAL GUIDELINES:\n"
            "- Always communicate conversationally, professionally, and warmly in the user's language (English, Hindi, or Hinglish).\n"
            "- If the user asks 'what can you do' / 'detail desc do' / 'list what u can do', provide a clean, beautifully formatted summary of your 4 agent personas and all 6 capabilities.\n"
            "- When the user requests a security check or audit on a target (e.g. 'check vynn.urbackend.in for auth issues'), DO NOT ask them to repeat the URL if it is already provided. Immediately call the appropriate tools (`discover_target_endpoints` or `run_security_scan`) to inspect the target!\n"
            "- Before firing active exploit probes or modifying Nginx virtual patch files, always outline your Pre-Action Execution Plan and confirm with the human lead.\n"
            "- Never provide canned repetitive responses. Respect the multi-turn conversation context provided in the room history."
        )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": system_prompt}]

        # Inject shared Switch Room context (multi-turn history)
        for hist_line in room_history[-8:]:
            if hist_line.startswith("Kite-Agent:"):
                messages.append({"role": "assistant", "content": hist_line.replace("Kite-Agent:", "").strip()})
            else:
                messages.append({"role": "user", "content": hist_line})

        messages.append({"role": "user", "content": user_message})

        tools = self.get_tool_definitions()

        try:
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

            # Process tool calls if emitted
            if response_message.tool_calls:
                messages.append(response_message)
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

                second_kwargs: Dict[str, Any] = {
                    "model": self.model,
                    "messages": messages,
                    "extra_body": {"reasoning_effort": "none"}
                }
                try:
                    second_response = self.client.chat.completions.create(**second_kwargs)
                except Exception:
                    second_kwargs.pop("extra_body", None)
                    second_kwargs["reasoning_effort"] = "none"
                    second_response = self.client.chat.completions.create(**second_kwargs)

                return second_response.choices[0].message.content or "Task completed successfully."

            return response_message.content or "Standing by in room."

        except Exception as e:
            logger.error(f"Error in Agent Engine turn: {e}", exc_info=True)
            return f"⚠️ Error processing request: {str(e)}"
