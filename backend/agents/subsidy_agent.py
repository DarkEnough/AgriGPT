# backend/agents/subsidy_agent.py

from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase
from backend.services.rag_service import rag_service
import unicodedata


class SubsidyAgent(AgriAgentBase):
    """
    SubsidyAgent:
    Handles government schemes and agricultural subsidy information.
    Uses retrieved official data as the primary source.
    """

    name = "SubsidyAgent"

    def _sanitize_query(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\x00", "").replace("\u200c", "")
        return text.strip()

    def handle_query(self, query: str = None, image_path: str = None) -> str:

        if not query or not query.strip():
            response = (
                "Please ask about a specific agricultural subsidy or government scheme. "
                "For example, drip irrigation subsidy, PM-Kisan eligibility, or equipment support schemes."
            )
            return self.respond_and_record("", response, image_path)

        query_clean = self._sanitize_query(query)

        context_str = ""

        try:
            retrieved_docs = rag_service.retrieve(query_clean)

            if retrieved_docs:
                for i, doc in enumerate(retrieved_docs, 1):
                    context_str += (
                        f"Scheme information {i}: "
                        f"Scheme name: {doc.get('scheme_name', 'Not specified')}. "
                        f"Eligibility: {doc.get('eligibility', 'Not specified')}. "
                        f"Benefits: {doc.get('benefits', 'Not specified')}. "
                        f"Application steps: {doc.get('application_steps', 'Not specified')}. "
                        f"Required documents: {doc.get('documents', 'Not specified')}. "
                        f"Additional notes: {doc.get('notes', 'Not specified')}. "
                    )
            else:
                context_str = "No verified government scheme information was found for this query."

        except Exception as e:
            context_str = f"An error occurred while retrieving official information: {str(e)}"

        prompt = (
            "You are AgriGPT SubsidyAgent. "
            "You explain Indian agricultural subsidy schemes using ONLY verified official information provided below. "
            "Do not invent schemes, eligibility criteria, benefits, or application rules. "
            "If information is missing or unclear, state that clearly. "
            "Do not generalize nationwide rules unless explicitly stated. "
            "Present the information in simple, farmer-friendly language. "
            "Avoid legal or technical jargon. "
            "Do not provide advice beyond explaining what the scheme offers and how to apply. "
            f"Farmer question: {query_clean}. "
            f"Official information: {context_str}"
        )

        try:
            result = query_groq_text(prompt)
        except Exception:
            result = "Subsidy information could not be generated at this time."

        return self.respond_and_record(query_clean, result, image_path)
