import asyncio
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("cyberwar.tools.scanner")

class SandboxedScannerRunner:
    """
    Executes Nmap and Nuclei profiling inside the isolated sec-tools container.
    """
    def __init__(self, target_host: str = "nginx-proxy", target_port: int = 80):
        self.target_host = target_host
        self.target_port = target_port

    async def run_nmap_scan(self, target: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs nmap port and service detection against the target.
        """
        scan_target = target or self.target_host
        cmd = f"nmap -sV -Pn --top-ports 20 {scan_target}"
        logger.info(f"Executing Nmap: {cmd}")
        
        try:
            # We use docker exec against the sec-tools container
            proc = await asyncio.create_subprocess_exec(
                "docker", "exec", "cyberwar-sec-tools", "nmap", "-sV", "-Pn", "--top-ports", "20", scan_target,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="ignore")
            
            if proc.returncode != 0:
                logger.warning(f"Nmap returned non-zero code {proc.returncode}: {stderr.decode()}")
            
            return {
                "tool": "nmap",
                "target": scan_target,
                "raw_output": output,
                "status": "success" if proc.returncode == 0 else "warning"
            }
        except Exception as e:
            logger.error(f"Error running Nmap: {e}")
            return {
                "tool": "nmap",
                "target": scan_target,
                "raw_output": str(e),
                "status": "error"
            }

    async def run_nuclei_scan(self, target_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs Nuclei vulnerability scanner against the target endpoint.
        """
        url = target_url or f"http://{self.target_host}:{self.target_port}"
        logger.info(f"Executing Nuclei scan against: {url}")
        
        try:
            # Execute nuclei with JSON export
            proc = await asyncio.create_subprocess_exec(
                "docker", "exec", "cyberwar-sec-tools", "nuclei", "-u", url, "-tags", "sqli,xss,misconfig", "-json-export", "/scans/nuclei_out.json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="ignore")
            
            return {
                "tool": "nuclei",
                "target": url,
                "raw_output": output,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error running Nuclei: {e}")
            return {
                "tool": "nuclei",
                "target": url,
                "raw_output": str(e),
                "status": "error"
            }
