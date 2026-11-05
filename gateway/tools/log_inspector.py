import time
import httpx
import logging
from typing import Dict, Any, Optional
from config import settings

logger = logging.getLogger("cyberwar.tools.logs")

def tail_container_logs(
    container_name: Optional[str] = None,
    lines: int = 50,
    filter_errors: bool = True
) -> Dict[str, Any]:
    """
    Tails runtime logs from Docker containers using the Docker daemon socket.
    Pinpoints 500 Internal Server Errors, uncaught exceptions, and stack traces.
    """
    target_name = container_name or settings.TARGET_CONTAINER_NAME or "target-app"
    try:
        import docker
        client = docker.from_env()
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to connect to Docker daemon: {e}. Ensure /var/run/docker.sock is mounted."
        }

    try:
        # Check if container exists (try exact name or fuzzy match)
        target = None
        all_containers = client.containers.list(all=True)
        for c in all_containers:
            if target_name.lower() in c.name.lower():
                target = c
                break

        if not target:
            running_names = [c.name for c in all_containers]
            return {
                "status": "not_found",
                "searched_for": target_name,
                "available_containers": running_names,
                "message": f"Container matching '{target_name}' not found."
            }

        raw_logs = target.logs(tail=lines, stdout=True, stderr=True)
        log_text = raw_logs.decode("utf-8", errors="replace")

        # Extract error traces
        error_lines = []
        for line in log_text.splitlines():
            line_lower = line.lower()
            if any(err in line_lower for err in ["error", "exception", "traceback", "500 internal", "failed", "fatal"]):
                error_lines.append(line.strip())

        return {
            "status": "success",
            "container": target.name,
            "container_state": target.status,
            "total_lines_read": len(log_text.splitlines()),
            "errors_detected": len(error_lines),
            "recent_error_traces": error_lines[-15:] if error_lines else [],
            "tail_output": log_text[-2000:]
        }

    except Exception as e:
        logger.error(f"Error reading container logs: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}

async def check_service_health(target_url: Optional[str] = None) -> Dict[str, Any]:
    """
    Probes endpoint response latency, HTTP status code, server header, and service health.
    """
    raw_target = target_url or settings.TARGET_HOST
    url = raw_target if raw_target.startswith("http") else f"https://{raw_target}"

    start_time = time.time()
    try:
        async with httpx.AsyncClient(verify=False, timeout=8.0) as client:
            resp = await client.get(url)
            latency_ms = round((time.time() - start_time) * 1000, 2)

            return {
                "status": "success",
                "target_url": url,
                "http_status": resp.status_code,
                "is_healthy": resp.status_code < 500,
                "latency_ms": latency_ms,
                "server": resp.headers.get("server", "unknown"),
                "content_type": resp.headers.get("content-type", "unknown")
            }
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "target_url": url,
            "error": "Connection timed out after 8 seconds."
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "target_url": url,
            "error": str(e)
        }
