import os
import json
import logging
from typing import Dict, Any, List, Optional
from services.knowledge_manager import KnowledgeBaseManager

logger = logging.getLogger("cyberwar.tools.repo_inspector")

class TargetRepoInspector:
    """
    Safely inspects the target application's mounted source code repository.
    Enables autonomous code comprehension, dependency analysis, and architecture discovery.
    """
    def __init__(self, repo_dir: str = "/app/target_repo"):
        self.repo_dir = repo_dir
        self.kb = KnowledgeBaseManager()

    def _resolve_safe_path(self, relative_path: str) -> Optional[str]:
        """
        Prevents directory traversal attacks (e.g. ../../etc/passwd).
        """
        # Fallback to local workspace if running outside container
        base = self.repo_dir if os.path.exists(self.repo_dir) else os.getcwd()
        clean_rel = relative_path.lstrip("/\\")
        target_path = os.path.abspath(os.path.join(base, clean_rel))

        if not target_path.startswith(os.path.abspath(base)):
            logger.warning(f"Directory traversal attempt blocked: {relative_path}")
            return None
        return target_path

    def list_files(self, max_files: int = 40) -> Dict[str, Any]:
        """
        Lists files in the target repository root and immediate subdirectories.
        """
        base = self.repo_dir if os.path.exists(self.repo_dir) else os.getcwd()
        file_tree = []

        try:
            for root, dirs, files in os.walk(base):
                # Ignore node_modules, .git, venv
                dirs[:] = [d for d in dirs if d not in [".git", "node_modules", ".venv", "venv", "__pycache__"]]
                for f in files:
                    rel_path = os.path.relpath(os.path.join(root, f), base)
                    file_tree.append(rel_path.replace("\\", "/"))
                    if len(file_tree) >= max_files:
                        break
                if len(file_tree) >= max_files:
                    break

            return {
                "repository_path": base,
                "total_files_sampled": len(file_tree),
                "files": file_tree
            }
        except Exception as e:
            logger.error(f"Error listing repository files: {e}")
            return {"error": str(e), "files": []}

    def read_file(self, file_path: str = "README.md", max_lines: int = 150) -> Dict[str, Any]:
        """
        Reads content of a specified project file (e.g. package.json, README.md, Dockerfile).
        """
        safe_path = self._resolve_safe_path(file_path)
        if not safe_path:
            return {"error": "Invalid or forbidden file path."}

        if not os.path.exists(safe_path):
            return {
                "error": f"File '{file_path}' not found in repository.",
                "available_files_hint": self.list_files(max_files=10).get("files", [])
            }

        try:
            with open(safe_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = [f.readline() for _ in range(max_lines)]
                content = "".join(lines)

            # If reading package.json, auto-extract project purpose and tech stack
            if "package.json" in file_path.lower():
                try:
                    pkg = json.loads(content)
                    project_info = {
                        "name": pkg.get("name", "Unknown"),
                        "description": pkg.get("description", "No description in package.json"),
                        "version": pkg.get("version", "1.0.0"),
                        "main": pkg.get("main", "index.js"),
                        "dependencies": list(pkg.get("dependencies", {}).keys()),
                        "scripts": pkg.get("scripts", {})
                    }
                    # Update knowledge base overview
                    self.kb.save_or_update_knowledge(
                        category="target_overview",
                        data={
                            "target_name": project_info["name"],
                            "business_domain": project_info["description"],
                            "technology_stack": {
                                "runtime": "Node.js",
                                "dependencies": project_info["dependencies"][:15]
                            }
                        },
                        agent_name="recon-bot",
                        discovery_method="package_json_inspection"
                    )
                    return {
                        "file_path": file_path,
                        "project_info": project_info,
                        "raw_preview": content[:1200]
                    }
                except Exception:
                    pass

            return {
                "file_path": file_path,
                "lines_read": len(lines),
                "content": content
            }
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return {"error": str(e)}
