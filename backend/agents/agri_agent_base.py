# backend/agents/agri_agent_base.py

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from backend.services.history_service import log_interaction


class AgriAgentBase(ABC):
    name: str = "AgriAgentBase"

    # --------------------------------------------------
    # Every agent must follow this signature
    # --------------------------------------------------
    @abstractmethod
    def handle_query(
        self,
        query: Optional[str] = None,
        image_path: Optional[str] = None,
        chat_history: Optional[str] = None,
    ) -> str:
        pass

    # --------------------------------------------------
    # Detect type for logging
    # --------------------------------------------------
    @staticmethod
    def _normalize_query(q: Optional[str]) -> str:
        if q is None:
            return ""
        return q.strip()

    @staticmethod
    def _detect_query_type(query, image_path):
        normalized_query = AgriAgentBase._normalize_query(query)

        if normalized_query and image_path:
            return "multimodal"
        if image_path:
            return "image"
        return "text"

    # --------------------------------------------------
    # ✅ ACTUAL LOGGING (META-AWARE)
    # --------------------------------------------------
    def record(
        self,
        query,
        response,
        query_type,
        image_path=None,
        meta: Optional[dict] = None,   # ✅ NEW
    ):
        safe_response = str(response)

        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name,
            "query": query or "",
            "response": safe_response[:5000],
            "type": query_type,
        }

        if image_path:
            entry["image_path"] = image_path

        # ✅ Store routing / role metadata IF provided
        if meta:
            entry["meta"] = meta

        try:
            log_interaction(entry)
        except Exception:
            pass  # Never break execution because of logging

    # --------------------------------------------------
    # ✅ WRAPPER USED BY ALL AGENTS
    # --------------------------------------------------
    def respond_and_record(
        self,
        query,
        response,
        image_path=None,
        meta: Optional[dict] = None,   # ✅ NEW
    ):
        query_type = self._detect_query_type(query, image_path)
        safe_response = str(response)

        self.record(
            query=query,
            response=safe_response,
            query_type=query_type,
            image_path=image_path,
            meta=meta,
        )

        return safe_response
