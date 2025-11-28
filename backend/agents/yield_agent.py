# backend/agents/yield_agent.py

from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase


class YieldAgent(AgriAgentBase):
    """
    YieldAgent:
    Identifies reasons for low yield and provides
    high-level, conditional yield improvement guidance.
    """

    name = "YieldAgent"

    def handle_query(self, query: str = None, image_path: str = None) -> str:

        if not query or not isinstance(query, str) or not query.strip():
            response = (
                "Please describe the crop and the yield issue you are facing. "
                "For example, low harvest, poor fruit setting, or reduced grain output."
            )
            return self.respond_and_record("", response, image_path)

        clean_query = query.strip()

        prompt = (
            "You are AgriGPT YieldAgent. "
            "Your role is to analyze yield-related problems conservatively. "
            "Do not give guaranteed yield numbers or exact targets. "
            "Use conditional language only. "
            "Do not prescribe chemical dosages or irrigation schedules. "
            "Do not override crop, irrigation, or pest specialists. "

            "Explain the following clearly and simply: "
            "First, describe broad expected yield ranges only if crop and region are mentioned, "
            "and clearly state that actual yield depends on conditions. "

            "Next, identify the most common limiting factors that reduce yield, "
            "such as soil fertility gaps, water stress, planting time, seed quality, "
            "pest pressure, or climate stress. "

            "Then, suggest practical next steps focused on diagnosis and prioritization only, "
            "for example soil testing, irrigation review, or pest inspection, "
            "without giving exact schedules or dosages. "

            "If important details are missing, say so clearly. "
            "Keep the language farmer-friendly and non-technical. "
            "Avoid repetition and avoid theory. "

            f"Farmer question: {clean_query}"
        )

        try:
            result = query_groq_text(prompt)
        except Exception:
            result = "Yield analysis could not be generated at this time."

        return self.respond_and_record(
            query=clean_query,
            response=result,
            image_path=image_path,
        )
