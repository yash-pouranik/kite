import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from config import settings
from tools.web_discovery import crawl_and_discover_target
from services.knowledge_manager import KnowledgeBaseManager
from tools.scanner_runner import SandboxedScannerRunner
from tools.exploit_runner import SafeExploitToolkit
from services.virtual_patcher import NginxVirtualPatcher

logger = logging.getLogger("cyberwar.agent_engine")

class KiteAgentEngine:
    """
    Stateful OpenAI Agent Engine with Native Function Calling (Tools).
    Handles natural conversation, answers capability inquiries, autonomously
    discovers APIs, tests vulnerabilities, and proposes zero-downtime fixes.
    """
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.model = settings.ATTACKER_MODEL # gpt-6-luna (or fallback to gpt-4o / gpt-4o-mini)
        self.kb = KnowledgeBaseManager()
        self.scanner = SandboxedScannerRunner()
        self.exploit = SafeExploitToolkit()
        self.patcher = NginxVirtualPatcher()
        self.default_target = settings.TARGET_CONTAINER_NAME or "vynn.urbackend.in"

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "discover_target_endpoints",
                    "description": "Crawls the target application web bundles, inspects HTTP headers, and extracts all live API routes and authentication endpoints.",
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
                    "description": "Reads persistent knowledge files (target_overview, auth_mechanisms, api_inventory) to check what has already been discovered.",
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
                    "description": "Runs sandboxed Nmap port scan and Nuclei vulnerability scans against an endpoint.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target": {
                                "type": "string",
                                "description": "Target hostname or IP, e.g. vynn.urbackend.in"
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
                    "description": "Fires a non-destructive read-only proof-of-concept probe to verify if an endpoint is exploitable.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "The endpoint path to probe, e.g. /api/v1/auth/login"
                            },
                            "payload": {
                                "type": "string",
                                "description": "The safe test payload, e.g. ' OR 1=1 --"
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
                    "description": "Injects a targeted regex filter into Nginx reverse proxy and triggers a zero-downtime hot reload.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "The endpoint to protect"
                            }
                        },
                        "required": ["endpoint"]
                    }
                }
            }
        ]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> str:
        logger.info(f"Agent Engine executing tool: {name} with args: {args}")
        try:
            if name == "discover_target_endpoints":
                url = args.get("target_url") or f"https://{self.default_target}"
                result = await crawl_and_discover_target(url)
                # Save to knowledge base
                self.kb.save_or_update_knowledge(
                    category="api_inventory",
                    data=result,
                    agent_name="kite-agent",
                    discovery_method="web_bundle_crawler"
                )
                return json.dumps(result, indent=2)

            elif name == "read_knowledge_base":
                cat = args.get("category", "api_inventory")
                kb_data = self.kb.get_knowledge(cat)
                return json.dumps(kb_data or {"status": "empty", "message": "No data discovered yet."}, indent=2)

            elif name == "run_security_scan":
                target = args.get("target") or self.default_target
                res = await self.scanner.run_nuclei_scan(f"https://{target}")
                return json.dumps(res, indent=2)

            elif name == "verify_safe_exploit_probe":
                endpoint = args.get("endpoint", "/api/v1/auth/login")
                res = await self.exploit.verify_sqli_probe(endpoint=endpoint)
                return json.dumps(res, indent=2)

            elif name == "apply_virtual_shield":
                endpoint = args.get("endpoint", "/api/v1/auth/login")
                res = await self.patcher.apply_virtual_patch()
                return json.dumps(res, indent=2)

            return json.dumps({"error": f"Unknown tool {name}"})
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return json.dumps({"error": str(e)})

    async def process_chat_turn(self, user_message: str, room_history: List[str]) -> str:
        """
        Sends conversation history + user message + tools to OpenAI.
        Loops to resolve tool calls, then returns final intelligent response.
        """
        if not self.client:
            return (
                "⚠️ **OpenAI API Key is missing in `.env`**. "
                "Please configure `OPENAI_API_KEY` to activate autonomous agent reasoning."
            )

        system_prompt = (
            "You are Kite, an autonomous, highly skilled SecOps Teammate built for the Flip the Switch Hackathon. "
            "You live in this Discord War Room and collaborate with engineers to defend cloud infrastructure.\n\n"
            f"TARGET CONTEXT:\n"
            f"- Default Target Host: {self.default_target} (AWS EC2 Staging/Prod)\n"
            f"- Deployment Mode: On-Host Autonomous SecOps Sidecar\n\n"
            "YOUR CAPABILITIES:\n"
            "1. Asset & Endpoint Discovery: You can crawl web bundles, inspect headers, and extract live API endpoints.\n"
            "2. Vulnerability Profiling: Run Nmap port detection and Nuclei security scanning.\n"
            "3. Safe Exploit Verification: Fire harmless read-only probes (' OR 1=1 --) to eliminate false positives.\n"
            "4. Dual-Track Remediation: Deploy zero-downtime Nginx virtual shields (`nginx -s reload`) + generate Git PRs.\n"
            "5. Quality Audit: Verify that legitimate customer traffic (200 OK) works while exploits are blocked (403).\n\n"
            "RULES:\n"
            "- Speak naturally, professionally, and directly in Hinglish or English as the user speaks.\n"
            "- When asked what you can do, give a clear, comprehensive overview of your 5 capabilities.\n"
            "- When asked to audit/check a target or endpoint, use your tools (`discover_target_endpoints`, `run_security_scan`) autonomously!\n"
            "- Before firing active exploit probes or modifying Nginx configs, always outline your Pre-Action Execution Plan and ask for confirmation."
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Append recent room history for true Switch Room Context
        for hist_line in room_history[-6:]:
            if hist_line.startswith("Kite-Agent:"):
                messages.append({"role": "assistant", "content": hist_line.replace("Kite-Agent:", "").strip()})
            else:
                messages.append({"role": "user", "content": hist_line})

        messages.append({"role": "user", "content": user_message})

        tools = self.get_tool_definitions()

        try:
            # Model selection fallback: try configured model, fallback to gpt-4o if gpt-6-luna not on account
            model_to_use = self.model
            
            # Initial LLM turn
            try:
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )
            except Exception as model_err:
                logger.warning(f"Model {model_to_use} unavailable ({model_err}), falling back to gpt-4o")
                model_to_use = "gpt-4o"
                response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto"
                )

            response_message = response.choices[0].message

            # Check if model wants to call tools
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

                # Follow-up turn with tool outputs
                second_response = self.client.chat.completions.create(
                    model=model_to_use,
                    messages=messages
                )
                return second_response.choices[0].message.content or "Task completed."

            return response_message.content or "Standing by."

        except Exception as e:
            logger.error(f"Error in Agent Engine: {e}")
            return f"⚠️ Error processing request: {str(e)}"
