import httpx
import re
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin
from config import settings

logger = logging.getLogger("cyberwar.tools.web_discovery")

async def crawl_and_discover_target(target_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Crawls the live target web application, inspects HTTP response headers,
    extracts script/bundle tags, parses real API routes via regex from downloaded bundles,
    and conducts active live probes (GET/POST) to verify route existence and supported methods.

    NEVER returns fake or mocked fallback routes. If unreachable, returns an explicit connection error.
    """
    raw_url = target_url or settings.TARGET_HOST or "target-app"

    raw_url = raw_url.strip()
    if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
        target_url = f"https://{raw_url}"
    else:
        target_url = raw_url

    discovered_routes = set()
    tech_stack = {}
    detailed_endpoints = []
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KiteSecOps/2.0 (Live Attack Surface Discovery)"
    }

    async with httpx.AsyncClient(verify=False, timeout=12.0) as client:
        # 1. Fetch homepage
        try:
            res = await client.get(target_url, headers=headers)
            tech_stack["server"] = res.headers.get("server", "Nginx / Cloud")
            tech_stack["x_powered_by"] = res.headers.get("x-powered-by", "Unknown")
            tech_stack["strict_transport_security"] = "strict-transport-security" in res.headers
            html_text = res.text

            # 2. Extract script tags and modulepreloads (Vite / Webpack / Next)
            script_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            preload_srcs = re.findall(r'<link[^>]+rel=["\']modulepreload["\'][^>]+href=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
            all_bundles = list(set(script_srcs + preload_srcs))
            tech_stack["bundles_found"] = len(all_bundles)
            logger.info(f"Discovered {len(all_bundles)} script/module bundles on {target_url}")

            # 3. Download bundles and extract API routes (/api/..., /auth/..., /rest/...)
            for src in all_bundles[:10]:
                full_script_url = urljoin(target_url, src)
                try:
                    js_res = await client.get(full_script_url, headers=headers)
                    if js_res.status_code == 200:
                        matches = re.findall(r'["\'](/(?:api|auth|rest)/[a-zA-Z0-9_\-\/]+(?:\?[a-zA-Z0-9_\-=&]+)?)["\']', js_res.text)
                        for m in matches:
                            clean_route = m.split("?")[0].rstrip("/")
                            if clean_route:
                                discovered_routes.add(clean_route)
                except Exception as e:
                    logger.warning(f"Failed to fetch bundle {full_script_url}: {e}")

        except Exception as e:
            logger.error(f"Failed to connect to target {target_url}: {e}")
            return {
                "status": "error",
                "error": f"Failed to connect to target {target_url}: {e}",
                "total_discovered": 0,
                "endpoints": [],
                "verified_endpoints": []
            }

        # 4. Probe standard Swagger / OpenAPI / Health endpoints
        common_probes = ["/health", "/api/health", "/swagger.json", "/openapi.json", "/api-docs"]
        for probe in common_probes:
            probe_url = urljoin(target_url, probe)
            try:
                probe_res = await client.get(probe_url, headers=headers)
                if probe_res.status_code in [200, 204, 301, 302, 401, 403]:
                    discovered_routes.add(probe)
                    if "json" in probe_res.headers.get("content-type", ""):
                        tech_stack["api_spec"] = probe
            except Exception:
                pass

        # 5. Live Active Probing & Verification of Discovered Endpoints
        sorted_routes = sorted(list(discovered_routes))
        auth_endpoints = []
        health_endpoints = []

        for route in sorted_routes:
            ep_url = urljoin(target_url, route)
            methods_supported = []
            status_map = {}
            is_live = False

            # Probe GET
            try:
                g_res = await client.get(ep_url, headers=headers)
                status_map["GET"] = g_res.status_code
                if g_res.status_code not in [404, 502, 503]:
                    methods_supported.append("GET")
                    is_live = True
            except Exception:
                status_map["GET"] = None

            # Probe POST
            try:
                p_res = await client.post(ep_url, headers=headers, json={})
                status_map["POST"] = p_res.status_code
                if p_res.status_code not in [404, 405, 502, 503]:
                    methods_supported.append("POST")
                    is_live = True
            except Exception:
                status_map["POST"] = None

            category = "api"
            if any(k in route.lower() for k in ["login", "auth", "token", "oauth"]):
                category = "auth"
            elif "health" in route.lower():
                category = "health"

            ep_data = {
                "path": route,
                "url": ep_url,
                "category": category,
                "is_live": is_live,
                "methods": methods_supported if methods_supported else ["UNKNOWN"],
                "status_codes": status_map
            }

            if category == "auth":
                auth_endpoints.append(ep_data)
            elif category == "health":
                health_endpoints.append(ep_data)

            detailed_endpoints.append(ep_data)

    return {
        "status": "success",
        "target": target_url,
        "technology_stack": tech_stack,
        "total_discovered": len(sorted_routes),
        "endpoints": sorted_routes,
        "verified_endpoints": detailed_endpoints,
        "auth_endpoints": auth_endpoints,
        "health_endpoints": health_endpoints
    }
