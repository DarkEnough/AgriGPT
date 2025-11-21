from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase
from backend.services.rag_service import rag_service

class SubsidyAgent(AgriAgentBase):
    """
    Subsidy & Government Scheme Agent
    ---------------------------------
    Provides clear and accurate information about:
    - Central & State agricultural schemes
    - Drip/micro irrigation subsidies
    - Seed, fertilizer, machinery subsidies
    - Crop insurance, Kisan Credit, PM-Kisan
    - Eligibility + benefit amounts
    """

    name = "SubsidyAgent"

    def handle_query(self, query: str = None, image_path: str = None) -> str:
        """
        Handles subsidy and scheme-related queries.
        Image input is ignored; this is a text-only agent.
        """

        # ------------------------------------------------------
        # CASE 0 — No query
        # ------------------------------------------------------
        if not query or not query.strip():
            msg = (
                "Please ask about a specific subsidy or government scheme — for example:\n"
                "- 'Drip irrigation subsidy in Tamil Nadu'\n"
                "- 'PM-Kisan eligibility'\n"
                "- 'Kisan Credit Card loan details'\n"
                "- 'Fertilizer subsidy amount'"
            )
            return self.respond_and_record(
                "No query provided",
                msg,
                image_path=image_path
            )

        # ------------------------------------------------------
        # CASE 1 — Clean input
        # ------------------------------------------------------
        query_clean = query.strip()

        # ------------------------------------------------------
        # CASE 2 — RAG Retrieval
        # ------------------------------------------------------
        retrieved_docs = rag_service.retrieve(query_clean)
        context_str = ""
        if retrieved_docs:
            context_str = "\n\n**Retrieved Official Information:**\n"
            for i, doc in enumerate(retrieved_docs, 1):
                context_str += (
                    f"Scheme {i}: {doc['scheme_name']}\n"
                    f"- Eligibility: {doc['eligibility']}\n"
                    f"- Benefits: {doc['benefits']}\n"
                    f"- Application: {doc['application_steps']}\n"
                    f"- Documents: {doc['documents']}\n"
                    f"- Notes: {doc['notes']}\n\n"
                )

        # ------------------------------------------------------
        # CASE 3 — Build AI prompt
        # ------------------------------------------------------
        prompt = f"""
        You are AgriGPT, an expert assistant on Indian agricultural subsidies and schemes.

        The farmer asked:
        \"\"\"{query_clean}\"\"\"

        {context_str}

        If the Retrieved Official Information matches the user's query, USE IT as your primary source.
        If the context doesn't answer the question fully, rely on your general knowledge but be careful with numbers.

        Provide accurate, clear details including:
        1. Name of the scheme/subsidy
        2. Central or State government
        3. Eligibility
        4. Financial benefits
        5. Application process
        6. Important notes

        Style:
        - Simple language
        - Bullet points
        - Short sentences
        """

        # ------------------------------------------------------
        # CASE 4 — Query Groq LLM safely
        # ------------------------------------------------------
        try:
            result = query_groq_text(prompt)
        except Exception as e:
            result = f"Error retrieving subsidy details: {e}"

        # ------------------------------------------------------
        # RETURN + LOG
        # ------------------------------------------------------
        return self.respond_and_record(
            query_clean,
            result,
            image_path=image_path
        )
