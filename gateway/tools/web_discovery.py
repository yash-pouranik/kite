import httpx
import re
import logging
from typing import Dict, Any, List
from urllib.parse import urljoin

logger = logging.getLogger("cyberwar.tools.web_discovery")

async def crawl_and_discover_target(target_url: str = "https://vynn.urbackend.in") -> Dict[str, Any]:
    """
    Crawls the target web application, inspects response headers,
    downloads referenced JavaScript bundles, and extracts API endpoints using regex.
    """
    if not target_url.startswith("http"):
        target_url = f"https://{target_url}"

    discovered_endpoints = set()
    tech_stack = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KiteSecOps/1.0"
    }

    async with httpx.AsyncClient(verify=False, timeout=12.0) as client:
        # 1. Fetch homepage
        try:
            res = await client.get(target_url, headers=headers)
            tech_stack["server"] = res.headers.get("server", "Nginx / Cloud")
            tech_stack["powered_by"] = res.headers.get("x-powered-by", "Unknown")
            html_text = res.text

            # 2. Extract script tags (JS bundles)
            script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            logger.info(f"Discovered {len(script_srcs)} script bundles on {target_url}")

            # 3. Download bundles and extract API routes (/api/..., /rest/..., /auth/...)
            for src in script_srcs[:5]: # top 5 bundles
                full_script_url = urljoin(target_url, src)
                try:
                    js_res = await client.get(full_script_url, headers=headers)
                    if js_res.status_code == 200:
                        # Extract quoted API paths like "/api/v1/login", "/auth/...", "/users"
                        routes = re.findall(r'["\'](/api/[a-zA-Z0-9_\-\/]+|/rest/[a-zA-Z0-9_\-\/]+|/auth/[a-zA-Z0-9_\-\/]+)["\']', js_res.text)
                        for r in routes:
                            discovered_endpoints.add(r)
                except Exception as e:
                    logger.warning(f"Failed to fetch bundle {full_script_url}: {e}")

        except Exception as e:
            logger.error(f"Failed to connect to target {target_url}: {e}")

        # 4. Probe standard Swagger / OpenAPI endpoints
        common_probes = ["/api-docs", "/swagger.json", "/openapi.json", "/api/v1/health", "/health"]
        for probe in common_probes:
            probe_url = urljoin(target_url, probe)
            try:
                probe_res = await client.get(probe_url, headers=headers)
                if probe_res.status_code in [200, 301, 302]:
                    discovered_endpoints.add(probe)
                    if "json" in probe_res.headers.get("content-type", ""):
                        tech_stack["api_spec"] = probe
            except Exception:
                pass

    endpoints_list = sorted(list(discovered_endpoints))
    if not endpoints_list:
        # Fallback common REST targets for the domain
        endpoints_list = ["/api/v1/auth/login", "/api/v1/users", "/health"]

    return {
        "target": target_url,
        "technology_stack": tech_stack,
        "total_discovered": len(endpoints_list),
        "endpoints": endpoints_list
    }
