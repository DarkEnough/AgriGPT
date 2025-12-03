from backend.services.text_service import query_groq_text
from backend.services.vision_service import query_groq_image
from backend.agents.agri_agent_base import AgriAgentBase


class PestAgent(AgriAgentBase):
    """
    PestAgent:
    Handles pest, disease, and visible symptom analysis.
    Image input ALWAYS takes priority over text.
    """

    name = "PestAgent"

    def handle_query(self, query: str = None, image_path: str = None, chat_history: str = None) -> str:

        # --------------------------------------------------
        # CASE 0 — No input
        # --------------------------------------------------
        if not query and not image_path:
            response = (
                "Please upload a crop image or describe visible symptoms such as "
                "yellowing, spots, holes, insects, wilting, or abnormal leaf color."
            )
            return self.respond_and_record("", response, image_path)

        # --------------------------------------------------
        # CASE 1 — IMAGE-BASED OBSERVATION ONLY
        # --------------------------------------------------
        if image_path:
            vision_prompt = (
                "You are AgriGPT Vision, an expert agricultural diagnostics assistant. "
                "Analyze this crop image in detail. "
                "1. DESCRIBE symptoms clearly (e.g., yellow halo, brown necrotic spots, white powdery coating). "
                "2. IDENTIFY the likely issue (fungal, bacterial, pest, or nutrient) if visual evidence is strong. "
                "3. ESTIMATE severity (mild, moderate, severe) based on visual extent. "
                "Do not recommend chemical treatments yet. Focus on accurate diagnosis to help other agents provide the solution."
            )

            try:
                result = query_groq_image(image_path, vision_prompt)
            except Exception:
                result = "The image could not be analyzed clearly."

            return self.respond_and_record(
                "Image-based symptom observation",
                result,
                image_path=image_path,
            )

        # --------------------------------------------------
        # CASE 2 — TEXT-BASED SYMPTOM ANALYSIS
        # --------------------------------------------------
        clean_query = query.strip()

        text_prompt = (
            "You are AgriGPT PestAgent. "
            "Analyze the farmer's description of crop symptoms. "
            f"CONTEXT FROM PREVIOUS CHAT: {chat_history if chat_history else 'None'} "
            "1. VALIDATE: Do these symptoms match known pests/diseases? "
            "2. DIAGNOSE: List top 2-3 probable causes. "
            "3. EXPLAIN: Why do these symptoms occur? "
            "4. ADVISE: Immediate organic or cultural control steps. "
            f"Farmer description: {clean_query}"
        )

        try:
            result = query_groq_text(text_prompt)
        except Exception:
            result = "Pest analysis could not be generated at this time."

        return self.respond_and_record(
            clean_query,
            result,
            image_path=image_path,
        )
