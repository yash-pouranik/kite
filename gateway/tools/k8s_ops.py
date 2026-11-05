import json
import os
import subprocess
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("cyberwar.tools.k8s")

KUBECONFIG_CANDIDATES = [
    os.path.expanduser("~/.kube/config"),
    "/root/.kube/config",
    "/etc/rancher/k3s/k3s.yaml",
    "/etc/kubernetes/admin.conf"
]

def _resolve_kubeconfig() -> Optional[str]:
    """Finds available kubeconfig file across mounted paths."""
    env_kc = os.getenv("KUBECONFIG")
    if env_kc and os.path.exists(env_kc):
        return env_kc
    for cand in KUBECONFIG_CANDIDATES:
        if os.path.exists(cand):
            return cand
    return None

def _run_kubectl(args: List[str]) -> Dict[str, Any]:
    """Safely executes kubectl CLI command with resolved kubeconfig."""
    kubeconfig = _resolve_kubeconfig()
    cmd = ["kubectl"]
    if kubeconfig:
        cmd.extend(["--kubeconfig", kubeconfig])
    cmd.extend(args)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15
        )
        return {
            "status": "success" if proc.returncode == 0 else "failed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Kubectl command timed out after 15s"}
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "kubectl binary not installed in container. Run 'curl -fsSL https://dl.k8s.io/release/v1.30.0/bin/linux/amd64/kubectl -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl'."
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_k8s_pods(namespace: str = "gateway") -> Dict[str, Any]:
    """
    Lists running Kubernetes pods in the target namespace (e.g. gateway, default).
    Returns pod names, status, readiness, restart counts, and age.
    """
    res = _run_kubectl(["get", "pods", f"-n={namespace}", "-o=json"])
    if res.get("status") != "success":
        # Fallback to plain kubectl get pods if json format fails
        plain_res = _run_kubectl(["get", "pods", f"-n={namespace}"])
        if plain_res.get("status") == "success":
            return {
                "status": "success",
                "namespace": namespace,
                "raw_output": plain_res.get("stdout")
            }
        return res

    try:
        data = json.loads(res.get("stdout", "{}"))
        items = data.get("items", [])
        pods = []
        for item in items:
            metadata = item.get("metadata", {})
            status = item.get("status", {})
            container_statuses = status.get("containerStatuses", [{}])

            ready_count = sum(1 for cs in container_statuses if cs.get("ready", False))
            restart_count = sum(cs.get("restartCount", 0) for cs in container_statuses)

            pods.append({
                "name": metadata.get("name"),
                "namespace": metadata.get("namespace"),
                "phase": status.get("phase"),
                "ready": f"{ready_count}/{len(container_statuses)}",
                "restarts": restart_count,
                "created_at": metadata.get("creationTimestamp")
            })

        return {
            "status": "success",
            "namespace": namespace,
            "pod_count": len(pods),
            "pods": pods
        }
    except Exception as e:
        return {"status": "error", "error": f"Failed to parse kubectl output: {e}"}

def tail_k8s_logs(
    pod_name: Optional[str] = "gateway",
    namespace: str = "gateway",
    lines: int = 50
) -> Dict[str, Any]:
    """
    Tails live runtime logs and stack traces from a Kubernetes pod in the target cluster.
    Auto-detects matching pod name if partial string is given (e.g. 'gateway' -> 'gateway-7694f79849-z2qg6').
    """
    # 1. Resolve pod name if fuzzy
    target_pod = pod_name or "gateway"
    pods_res = get_k8s_pods(namespace=namespace)
    if pods_res.get("status") == "success" and "pods" in pods_res:
        available_pods = [p["name"] for p in pods_res["pods"]]
        # Find exact or prefix match
        match = None
        for p in available_pods:
            if target_pod.lower() in p.lower():
                match = p
                break
        if match:
            target_pod = match
        elif available_pods:
            target_pod = available_pods[0]

    # 2. Fetch logs
    res = _run_kubectl(["logs", f"-n={namespace}", target_pod, f"--tail={lines}"])
    if res.get("status") != "success":
        return res

    log_text = res.get("stdout", "")
    error_lines = []
    for line in log_text.splitlines():
        line_lower = line.lower()
        if any(err in line_lower for err in ["error", "exception", "traceback", "fatal", "fail", "500", "reject"]):
            error_lines.append(line.strip())

    return {
        "status": "success",
        "pod": target_pod,
        "namespace": namespace,
        "total_lines_read": len(log_text.splitlines()),
        "errors_detected": len(error_lines),
        "recent_error_traces": error_lines[-15:] if error_lines else [],
        "tail_output": log_text[-2500:] if log_text else "Pod log is empty."
    }
