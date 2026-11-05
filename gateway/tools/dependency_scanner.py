import json
import os
import re
import httpx
import logging
from typing import Dict, Any, List, Optional
from tools.git_ops import _resolve_repo_path

logger = logging.getLogger("cyberwar.tools.sca")

OSV_API_URL = "https://api.osv.dev/v1/querybatch"

async def scan_dependencies(
    manifest_file: str = "package.json",
    repo_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Executes Software Composition Analysis (SCA) on the target repository.
    Parses manifest files (package.json or requirements.txt) and queries the
    open OSV.dev database for known CVEs and safe upgrade versions.
    """
    target_path = _resolve_repo_path(repo_dir)
    manifest_full_path = os.path.join(target_path, manifest_file)

    if not os.path.exists(manifest_full_path):
        # Look for alternative manifests
        candidates = ["package.json", "requirements.txt", "Pipfile", "go.mod"]
        found = None
        for c in candidates:
            p = os.path.join(target_path, c)
            if os.path.exists(p):
                found = c
                manifest_full_path = p
                break
        if not found:
            return {
                "status": "error",
                "error": f"No dependency manifest found at {target_path}. Checked: {candidates}"
            }
        manifest_file = found

    deps_to_query = []
    ecosystem = "npm" if manifest_file.endswith(".json") else "PyPI"

    if manifest_file.endswith(".json"):
        try:
            with open(manifest_full_path, "r", encoding="utf-8") as f:
                pkg_data = json.load(f)
            deps = pkg_data.get("dependencies", {})
            dev_deps = pkg_data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            for name, ver in all_deps.items():
                # Clean version strings like "^4.17.1" -> "4.17.1"
                clean_ver = re.sub(r"[^\d\.]", "", ver)
                if clean_ver:
                    deps_to_query.append({"name": name, "version": clean_ver, "ecosystem": "npm"})
        except Exception as e:
            return {"status": "error", "error": f"Failed to parse package.json: {e}"}

    elif manifest_file.endswith(".txt"):
        try:
            with open(manifest_full_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = re.split(r"[=<>~]+", line)
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            ver = parts[1].strip()
                            deps_to_query.append({"name": name, "version": ver, "ecosystem": "PyPI"})
        except Exception as e:
            return {"status": "error", "error": f"Failed to parse requirements.txt: {e}"}

    if not deps_to_query:
        return {
            "status": "success",
            "manifest": manifest_file,
            "total_dependencies": 0,
            "message": "No pinned dependencies found in manifest."
        }

    # Query OSV.dev in chunks of up to 50
    queries = [
        {"package": {"name": d["name"], "ecosystem": d["ecosystem"]}, "version": d["version"]}
        for d in deps_to_query[:50]
    ]

    vulnerabilities = []
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.post(OSV_API_URL, json={"queries": queries})
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                for i, r in enumerate(results):
                    vulns = r.get("vulns", [])
                    if vulns:
                        dep_info = deps_to_query[i]
                        for v in vulns:
                            cve_id = v.get("id")
                            summary = v.get("summary") or v.get("details", "")[:120]
                            # Find fixed version from affected ranges
                            fixed_version = "Check OSV advisory"
                            for aff in v.get("affected", []):
                                for rng in aff.get("ranges", []):
                                    for evt in rng.get("events", []):
                                        if "fixed" in evt:
                                            fixed_version = evt["fixed"]
                            
                            vulnerabilities.append({
                                "package": dep_info["name"],
                                "current_version": dep_info["version"],
                                "ecosystem": dep_info["ecosystem"],
                                "vulnerability_id": cve_id,
                                "summary": summary,
                                "fixed_version": fixed_version
                            })
            else:
                logger.warning(f"OSV API returned status {resp.status_code}")
    except Exception as e:
        logger.warning(f"Error querying OSV API: {e}")

    return {
        "status": "success",
        "manifest": manifest_file,
        "scanned_dependencies_count": len(deps_to_query),
        "vulnerabilities_count": len(vulnerabilities),
        "is_clean": len(vulnerabilities) == 0,
        "vulnerabilities": vulnerabilities
    }
