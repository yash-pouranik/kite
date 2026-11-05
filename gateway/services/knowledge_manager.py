import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

logger = logging.getLogger("cyberwar.services.knowledge")

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")

class KnowledgeBaseManager:
    """
    Manages reading, caching, updating, and scoring completeness for the
    multi-agent persistent knowledge base.
    """
    def __init__(self, base_dir: str = KNOWLEDGE_BASE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_file_path(self, category: str) -> str:
        filename = f"{category.lower().strip()}.json"
        return os.path.join(self.base_dir, filename)

    def get_knowledge(self, category: str) -> Optional[Dict[str, Any]]:
        """
        Reads knowledge file. Returns None if file does not exist or is corrupted.
        """
        filepath = self._get_file_path(category)
        if not os.path.exists(filepath):
            logger.info(f"Knowledge cache miss: {filepath} not found.")
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Knowledge cache hit: {category} (Completeness: {data.get('metadata', {}).get('knowledge_completeness_percentage', 0)}%)")
            return data
        except Exception as e:
            logger.error(f"Error reading knowledge file {filepath}: {e}")
            return None

    def is_knowledge_sufficient(self, category: str, threshold_percentage: int = 70) -> bool:
        """
        Checks if knowledge exists and has a completeness score >= threshold_percentage.
        """
        knowledge = self.get_knowledge(category)
        if not knowledge:
            return False
        completeness = knowledge.get("metadata", {}).get("knowledge_completeness_percentage", 0)
        return completeness >= threshold_percentage

    def save_or_update_knowledge(
        self,
        category: str,
        data: Dict[str, Any],
        agent_name: str,
        discovery_method: str = "automated_discovery",
        completeness_percentage: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Saves or appends to knowledge file with standardized audit metadata.
        """
        filepath = self._get_file_path(category)
        
        # Calculate completeness if not provided
        if completeness_percentage is None:
            completeness_percentage = self.calculate_completeness(category, data)

        metadata = {
            "last_scanned_at": datetime.now(timezone.utc).isoformat(),
            "last_updated_by": agent_name,
            "discovery_method": discovery_method,
            "knowledge_completeness_percentage": completeness_percentage,
            "confidence_score": round(completeness_percentage / 100.0, 2)
        }

        # Merge or wrap data with metadata
        data["metadata"] = metadata

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Knowledge base updated: {filepath} (Completeness: {completeness_percentage}%)")
            return data
        except Exception as e:
            logger.error(f"Error writing knowledge base {filepath}: {e}")
            return data

    def calculate_completeness(self, category: str, data: Dict[str, Any]) -> int:
        """
        Calculates factual completeness percentage based on category heuristics.
        Handles both list-of-strings and list-of-dicts gracefully.
        """
        score = 0
        cat_lower = category.lower()

        if "auth" in cat_lower:
            endpoints = data.get("endpoints", {})
            if isinstance(endpoints, dict):
                if "login" in endpoints:
                    login_info = endpoints["login"]
                    if isinstance(login_info, dict):
                        if login_info.get("path"):
                            score += 30
                        if login_info.get("payload_fields"):
                            score += 30
                        if login_info.get("token_location") or login_info.get("auth_type"):
                            score += 20
                if "registration" in endpoints or "signup" in endpoints:
                    score += 20
            elif isinstance(endpoints, list):
                has_login = any("login" in (ep.get("path", "") if isinstance(ep, dict) else str(ep)).lower() for ep in endpoints)
                if has_login:
                    score += 60
                if len(endpoints) >= 3:
                    score += 40
            return min(score, 100)

        elif "overview" in cat_lower:
            if data.get("base_url"):
                score += 20
            if data.get("technology_stack"):
                score += 30
            if data.get("business_domain"):
                score += 20
            if data.get("endpoints") or data.get("target_name"):
                score += 30
            return min(score, 100)

        elif "api" in cat_lower or "inventory" in cat_lower:
            endpoints = data.get("endpoints", [])
            if isinstance(endpoints, list):
                if len(endpoints) > 0:
                    score += 40
                if any(isinstance(ep, dict) and (ep.get("query_params") or ep.get("body_params")) for ep in endpoints):
                    score += 30
                elif any("/api" in str(ep) for ep in endpoints):
                    score += 30
                if len(endpoints) >= 5:
                    score += 30
            elif isinstance(endpoints, dict):
                score += 60
            return min(score, 100)

        return 50 # Default fallback
