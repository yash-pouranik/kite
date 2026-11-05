import os
import json
import logging
import httpx
import re
from typing import Dict, Any, List, Optional
from services.knowledge_manager import KnowledgeBaseManager
from config import settings

logger = logging.getLogger("cyberwar.tools.openapi_parser")

class OpenAPISchemaParser:
    """
    Ingests and parses OpenAPI/Swagger specifications from either:
    1. Public HTTP endpoints (e.g. /openapi.json, /api/docs).
    2. Local repository files (e.g. swagger.json, openapi.yaml, routes/).
    Eliminates manual endpoint guessing and maps exact request body schemas.
    """
    def __init__(self, repo_dir: str = "/app/target_repo"):
        self.repo_dir = repo_dir
        self.kb = KnowledgeBaseManager()

    async def fetch_and_parse_schema(self, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Attempts to fetch OpenAPI/Swagger JSON or YAML from target or local repo.
        """
        raw_target = base_url or settings.TARGET_HOST
        target_url = raw_target if raw_target.startswith("http") else f"https://{raw_target}"
        clean_base = target_url.rstrip("/")
        endpoints_catalog: Dict[str, Any] = {}
        auth_mechanisms: Dict[str, Any] = {}

        # 1. Probe HTTP endpoints
        common_candidates = [
            "/api/openapi.json",
            "/api/swagger.json",
            "/api-docs/swagger.json",
            "/openapi.json",
            "/swagger.json"
        ]

        async with httpx.AsyncClient(verify=False, timeout=8.0) as client:
            for cand in common_candidates:
                try:
                    res = await client.get(f"{clean_base}{cand}")
                    if res.status_code == 200 and "json" in res.headers.get("content-type", "").lower():
                        data = res.json()
                        if "paths" in data:
                            logger.info(f"Successfully loaded OpenAPI schema from: {cand}")
                            return self._process_openapi_data(data, source=cand)
                except Exception:
                    continue

        # 2. Check local repository for specification files
        base = self.repo_dir if os.path.exists(self.repo_dir) else os.getcwd()
        for root, _, files in os.walk(base):
            for f in files:
                if f.lower() in ["swagger.json", "openapi.json", "swagger.yaml", "openapi.yaml"]:
                    filepath = os.path.join(root, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as sf:
                            spec_data = json.load(sf)
                            if "paths" in spec_data:
                                logger.info(f"Successfully loaded OpenAPI schema from local repo file: {f}")
                                return self._process_openapi_data(spec_data, source=f)
                    except Exception:
                        pass

        # 3. Fallback: Parse express routes from source code files in repository
        scanned_routes = self._scan_source_code_routes(base)
        if scanned_routes:
            return {
                "source": "source_code_route_extraction",
                "total_routes_mapped": len(scanned_routes),
                "endpoints": scanned_routes
            }

        return {
            "status": "not_found",
            "message": "OpenAPI/Swagger schema not found on HTTP or repo root. Falling back to active web discovery.",
            "endpoints": [
                {"path": "/api/auth/login", "method": "POST", "body_params": ["email", "password"]},
                {"path": "/api/auth/me", "method": "GET", "auth_required": True},
                {"path": "/api/auth/api-keys", "method": "GET", "auth_required": True},
                {"path": "/api/oauth/clients", "method": "GET", "auth_required": True}
            ]
        }

    def _process_openapi_data(self, data: Dict[str, Any], source: str) -> Dict[str, Any]:
        paths = data.get("paths", {})
        routes_list = []
        auth_routes = []

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue

                route_info = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "parameters": [p.get("name") for p in details.get("parameters", []) if "name" in p]
                }
                routes_list.append(route_info)

                if "auth" in path.lower() or "login" in path.lower():
                    auth_routes.append(route_info)

        # Save to knowledge base
        self.kb.save_or_update_knowledge(
            category="api_inventory",
            data={"endpoints": routes_list, "total": len(routes_list)},
            agent_name="recon-bot",
            discovery_method=f"openapi_parser_{source}"
        )

        return {
            "source": source,
            "total_routes_mapped": len(routes_list),
            "auth_routes": auth_routes,
            "endpoints": routes_list[:25]
        }

    def _scan_source_code_routes(self, base_dir: str) -> List[Dict[str, Any]]:
        """
        Regex extracts app.get('/...', ...), router.post('/...', ...) from Express/Node.js files.
        """
        found = []
        for root, dirs, files in os.walk(base_dir):
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", ".venv"]]
            for f in files:
                if f.endswith((".js", ".ts")):
                    try:
                        filepath = os.path.join(root, f)
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as src:
                            text = src.read()
                            matches = re.findall(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
                            for method, path in matches:
                                found.append({"path": path, "method": method.upper(), "file": f})
                    except Exception:
                        pass
        return found
