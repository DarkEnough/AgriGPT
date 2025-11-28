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

    def handle_query(self, query: str = None, image_path: str = None) -> str:

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
                "You are AgriGPT Vision, an agricultural image observation assistant. "
                "Describe only what is clearly visible in the image. "
                "Allowed observations include leaf color changes, spots, holes, chewing damage, visible insects, mold, rot, wilting, or deformation. "
                "Do not name specific pests or diseases unless unmistakably visible. "
                "Do not guess causes, do not recommend chemicals, and do not infer crop stage or severity. "
                "If the image is unclear or insufficient, say so clearly."
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
            "Analyze the farmer-described crop symptoms conservatively. "
            "Do not give a definitive diagnosis and do not prescribe chemicals. "
            "Do not override irrigation, nutrition, or crop management advice. "
            "First summarize the main symptoms described by the farmer. "
            "Then list two or three possible causes using conditional language only. "
            "Suggest safe first-response actions such as monitoring, hygiene, mechanical removal, or low-risk organic practices. "
            "Clearly state when expert field inspection or laboratory testing is required. "
            "If symptoms may be caused by water stress or nutrient imbalance, say so explicitly. "
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
