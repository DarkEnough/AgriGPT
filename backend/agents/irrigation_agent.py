# backend/agents/irrigation_agent.py

from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase


class IrrigationAgent(AgriAgentBase):
    """
    IrrigationAgent:
    Handles irrigation and water management questions ONLY.
    """

    name = "IrrigationAgent"

    def handle_query(self, query: str = None, image_path: str = None) -> str:

        # --------------------------------------------------
        # Input validation
        # --------------------------------------------------
        if not query or not isinstance(query, str) or not query.strip():
            response = (
                "Please ask an irrigation-related question.\n"
                "Examples:\n"
                "• How often should I irrigate tomatoes?\n"
                "• How to save water using drip irrigation?\n"
                "• How should irrigation change during summer?"
            )
            return self.respond_and_record("", response, image_path)

        clean_query = query.strip()

        # --------------------------------------------------
        # Irrigation prompt (STRICT)
        # --------------------------------------------------
        prompt = " ".join([
            "You are AgriGPT IrrigationAgent.",
            "ROLE: You are an irrigation and water management specialist.",

            "YOU HANDLE ONLY irrigation frequency (stage-based or conditional), soil moisture management,",
            "and drip, sprinkler, and flood irrigation practices, including water-saving methods.",

            "STRICT BOUNDARIES:",
            "Do NOT diagnose pests, diseases, or nutrient deficiencies.",
            "Do NOT analyze images.",
            "Do NOT calculate or optimize yield.",
            "Do NOT recommend chemicals or fertilizers.",
            "Do NOT give subsidy or government scheme advice.",

            "SAFETY RULES:",
            "Do NOT guess soil type or crop stage unless the farmer explicitly states it.",
            "Use conditional guidance such as 'if sandy soil' or 'if high temperature'.",
            "If essential details are missing, say so clearly.",
            "Avoid exact schedules when conditions are unknown.",

            f"FARMER QUERY: {clean_query}",

            "RESPONSE INSTRUCTIONS:",
            "Give clear and practical irrigation advice.",
            "Explain when to water and when NOT to water.",
            "Mention visible signs of overwatering and underwatering only.",
            "Suggest water-saving practices where relevant.",
            "Keep language farmer-friendly and easy to follow.",
            "Avoid repetition and theory.",

            "OUTPUT:",
            "Plain advisory text only.",
            "No formatting, no titles, no forced bullets."
        ])

        # --------------------------------------------------
        # LLM call
        # --------------------------------------------------
        try:
            resp = query_groq_text(prompt)
        except Exception:
            resp = "Irrigation advice could not be generated at this time."

        # --------------------------------------------------
        # Log + return
        # --------------------------------------------------
        return self.respond_and_record(
            query=clean_query,
            response=resp,
            image_path=image_path,
        )
