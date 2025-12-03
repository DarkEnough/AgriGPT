# backend/agents/crop_agent.py

from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase


class CropAgent(AgriAgentBase):
    """
    CropAgent:
    Handles general crop management questions.
    DOES NOT diagnose pests, diseases, or irrigation failures.
    """

    name = "CropAgent"

    def handle_query(self, query: str = None, image_path: str = None, chat_history: str = None) -> str:

        # --------------------------------------------------
        # Input validation
        # --------------------------------------------------
        if not query or not query.strip():
            response = (
                "Please ask a crop management question.\n"
                "Examples:\n"
                "• What fertilizer should I use for tomatoes?\n"
                "• How should I prepare soil for rice?\n"
                "• What practices improve crop growth?"
            )
            return self.respond_and_record("", response, image_path)

        clean_query = query.strip()

        # --------------------------------------------------
        # Crop-specific prompt (STRICT)
        # --------------------------------------------------
        prompt = " ".join([
            "You are AgriGPT CropAgent.",
            "ROLE: You are a crop management specialist.",
            "You provide guidance ONLY on crop cultivation practices, fertilizer planning (general or conditional), soil preparation, and crop growth stage care.",
            "STRICT BOUNDARIES: Do NOT diagnose pests or diseases. Do NOT identify insects or leaf damage. Do NOT analyze images.",
            "Do NOT give subsidy or loan information. Do NOT give irrigation schedules. Do NOT override other expert agents.",
            "SAFETY RULES: Do NOT guess soil type, crop variety, or region unless stated.",
            "Use conditional language when required. If essential details are missing, say so clearly.",
            "Do NOT invent chemical names or dosages.",
            f"PREVIOUS CONTEXT: {chat_history if chat_history else 'None'}",
            f"FARMER QUERY: {clean_query}",
            "RESPONSE INSTRUCTIONS:",
            "Give practical, actionable crop management advice.",
            "Use simple, farmer-friendly language.",
            "If fertilizer is mentioned, provide type (example: NPK, urea, compost) and a general dosage range or conditional guidance when exact dosage is unknown.",
            "Mention soil preparation steps if relevant.",
            "Focus ONLY on crop practices. Avoid repetition and theory.",
            "OUTPUT: Plain advisory text only. No formatting, no titles, no forced bullets."
        ])


        # --------------------------------------------------
        # LLM call
        # --------------------------------------------------
        try:
            resp = query_groq_text(prompt)
        except Exception as e:
            resp = "Crop advice could not be generated at this time."

        # --------------------------------------------------
        # Log + return
        # --------------------------------------------------
        return self.respond_and_record(
            query=clean_query,
            response=resp,
            image_path=image_path
        )
