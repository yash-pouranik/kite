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
from tools.repo_inspector import TargetRepoInspector
from tools.openapi_parser import OpenAPISchemaParser

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
        self.repo_inspector = TargetRepoInspector()
        self.openapi_parser = OpenAPISchemaParser()
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
                    "name": "read_project_file",
                    "description": "Reads source code or project documentation files from the mounted target application repository (e.g. package.json, README.md, Dockerfile, server configs). Use this to understand the project purpose, dependencies, and architecture.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Relative path to file in repo, e.g. 'package.json', 'README.md', 'src/index.ts'"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_project_files",
                    "description": "Lists the files and folder structure in the target repository to see what files are available to inspect.",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "parse_openapi_schema",
                    "description": "Ingests and parses OpenAPI/Swagger specifications from public endpoints or local repo files. Returns exact endpoint routes, HTTP methods, and body parameter schemas.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_url": {
                                "type": "string",
                                "description": "Target base URL, e.g. https://vynn.urbackend.in"
                            }
                        }
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
                    "name": "update_knowledge_base",
                    "description": "Updates or appends verified project details (such as confirmed project purpose, architecture notes, or tech stack) into persistent memory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["target_overview", "auth_mechanisms", "api_inventory"],
                                "description": "Knowledge category to update."
                            },
                            "key": {
                                "type": "string",
                                "description": "Field or section name to update (e.g. 'project_purpose', 'technology_stack', 'repository_path')."
                            },
                            "value": {
                                "type": "string",
                                "description": "Information or summary content to store."
                            }
                        },
                        "required": ["category", "key", "value"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_security_scan",
                    "description": "Executes sandboxed security scans and active HTTP security header / auth hardening checks against an asset or endpoint.",
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
                                "description": "The target endpoint path, e.g. /api/auth/login"
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
                                "description": "The endpoint to protect, e.g. /api/auth/login"
                            }
                        },
                        "required": ["endpoint"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "rollback_virtual_shield",
                    "description": "1-Click Safety Rollback: Instantly deactivates the virtual patch, deletes the WAF rule, and hot-reloads Nginx. Restores traffic to original pre-incident state.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "endpoint": {
                                "type": "string",
                                "description": "Endpoint to rollback, e.g. /api/auth/login"
                            }
                        }
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

            elif name == "read_project_file":
                file_path = args.get("file_path", "package.json")
                res = self.repo_inspector.read_file(file_path=file_path)
                return json.dumps(res, indent=2)

            elif name == "list_project_files":
                res = self.repo_inspector.list_files()
                return json.dumps(res, indent=2)

            elif name == "parse_openapi_schema":
                target = args.get("target_url") or f"https://{self.default_target}"
                res = await self.openapi_parser.fetch_and_parse_schema(base_url=target)
                return json.dumps(res, indent=2)

            elif name == "read_knowledge_base":
                cat = args.get("category", "api_inventory")
                kb_data = self.kb.get_knowledge(cat)
                return json.dumps(kb_data or {"status": "empty", "completeness": 0, "message": "No data discovered yet."}, indent=2)

            elif name == "update_knowledge_base":
                cat = args.get("category", "target_overview")
                key = args.get("key", "project_info")
                val = args.get("value", "")
                existing = self.kb.get_knowledge(cat) or {}
                existing[key] = val
                res = self.kb.save_or_update_knowledge(
                    category=cat,
                    data=existing,
                    agent_name="human_collaborator",
                    discovery_method="engineer_input"
                )
                return json.dumps({"status": "updated", "category": cat, "key": key}, indent=2)

            elif name == "run_security_scan":
                target = args.get("target") or self.default_target
                target_url = target if target.startswith("http") else f"https://{target}"
                res = await self.scanner.run_nuclei_scan(target_url)
                return json.dumps(res, indent=2)

            elif name == "verify_safe_exploit_probe":
                endpoint = args.get("endpoint", "/api/auth/login")
                payload = args.get("payload", "' OR 1=1 --")
                res = await self.exploit.verify_sqli_probe(endpoint=endpoint, payload=payload)
                return json.dumps(res, indent=2)

            elif name == "apply_virtual_shield":
                endpoint = args.get("endpoint", "/api/auth/login")
                res = await self.patcher.apply_virtual_patch(endpoint=endpoint)
                return json.dumps(res, indent=2)

            elif name == "rollback_virtual_shield":
                res = await self.patcher.rollback_virtual_patch()
                return json.dumps(res, indent=2)

            elif name == "create_github_pr":
                vuln = args.get("vulnerability", "Authentication Input Vulnerability")
                target_file = args.get("target_file", "src/auth/login.ts")
                res = await self.github.create_security_fix_pr(
                    vulnerability=vuln,
                    target_file=target_file
                )
                return json.dumps(res, indent=2)

            elif name == "verify_dual_track_remediation":
                endpoint = args.get("endpoint", "/api/auth/login")
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
            "You are Kite, an autonomous, highly capable Senior Multi-Agent SecOps Teammate built for the Flip the Switch Hackathon. "
            "You live in this Switch Room (Discord channel) alongside human security leads and engineers.\n\n"
            f"TARGET ENVIRONMENT:\n"
            f"- Target Host: {self.default_target} (AWS EC2 Production/Staging)\n"
            f"- Target Repository: Mounted at /app/target_repo (/home/ubuntu/mcp-gateway-k8s on EC2)\n"
            f"- Architecture: Switch-Native Multi-Agent System with Switch Trust Guardrails\n\n"
            "YOUR SQUAD PERSONAS:\n"
            "1. @recon-bot: Asset discovery, web bundle spidering, API route extraction, repository source code inspection (reading package.json, README.md), OpenAPI schema ingestion, Nmap/Nuclei scanning.\n"
            "2. @attacker: Ethical penetration testing, safe read-only PoC probes (' OR 1=1 --) to eliminate false positives.\n"
            "3. @fix-engine: Dual-Track Remediation — Zero-downtime Nginx virtual shield (`nginx -s reload`), Git Pull Request automation, and 1-Click Instant Safety Rollback.\n"
            "4. @verifier: Independent QA auditor — Confirms normal traffic (200 OK) while attack vectors are blocked (403 Forbidden).\n\n"
            "NEW SENIOR DEVSECOPS CAPABILITIES:\n"
            "- If asked about project purpose, code, or to read files, use `read_project_file` (e.g. package.json, README.md) or `list_project_files` to inspect the actual repository code!\n"
            "- If the user provides confirmed details (such as project purpose or corrected repository path), use `update_knowledge_base` to save them into persistent memory.\n"
            "- If asked to map exact schemas or endpoints, use `parse_openapi_schema`.\n"
            "- If the human asks to rollback, undo a patch, or take down the shield, invoke `rollback_virtual_shield`.\n\n"
            "RULES:\n"
            "- Always communicate naturally, professionally, and warmly in the user's language (English, Hindi, or Hinglish).\n"
            "- Never provide canned repetitive responses. Respect the multi-turn context provided in the room history.\n"
            "- Before firing active exploit probes or modifying Nginx virtual patch files, always outline your Pre-Action Execution Plan."
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
