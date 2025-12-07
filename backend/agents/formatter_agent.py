from typing import Any, Dict, List
from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase


class FormatterAgent(AgriAgentBase):
    """
    FormatterAgent

    Responsibilities:
    - Presentation only
    - Role-aware ordering
    - Zero hallucination surface
    - LLM used strictly for formatting
    """

    name = "FormatterAgent"


    def handle_query(self, payload: Any, image_path: str = None, chat_history: str = None) -> str:

        if isinstance(payload, str):
            clean_text = payload.strip()
            if not clean_text:
                return self.respond_and_record(
                    "", "No content available to format.", image_path
                )

            return self._format_text(
                user_query="",
                ordered_blocks=[clean_text],
                image_path=image_path,
                meta=None,
            )

        if not isinstance(payload, dict):
            return self.respond_and_record("", str(payload), image_path)

        user_query: str = str(payload.get("user_query", "")).strip()
        agent_results: List[Dict[str, str]] = payload.get("agent_results", [])
        routing_mode: str = str(payload.get("routing_mode", "unknown"))

        if not agent_results:
            return self.respond_and_record(
                user_query, "No agent responses were generated.", image_path
            )

        role_priority = {
            "primary": 0,
            "supporting": 1,
            "impact": 2,
        }

        agent_results_sorted = sorted(
            agent_results,
            key=lambda x: role_priority.get(
                str(x.get("role", "supporting")).lower(), 99
            ),
        )

        ordered_blocks: List[str] = []
        role_log: List[Dict[str, str]] = []

        for item in agent_results_sorted:
            role = str(item.get("role", "supporting")).lower()
            agent = str(item.get("agent", "UnknownAgent"))
            content = str(item.get("content", "")).strip()

            if content:
                ordered_blocks.append(
                    f"[{role.upper()} | {agent}]\n{content}"
                )
                role_log.append({
                    "agent": agent,
                    "role": role,
                })

        if not ordered_blocks:
            return self.respond_and_record(
                user_query, "Agent responses were empty.", image_path
            )

        meta = {
            "routing_mode": routing_mode,
            "agents": role_log,
            "agent_count": len(role_log),
        }

        return self._format_text(
            user_query=user_query,
            ordered_blocks=ordered_blocks,
            image_path=image_path,
            meta=meta,
        )

    def _format_text(
        self,
        user_query: str,
        ordered_blocks: List[str],
        image_path: str = None,
        meta: Dict[str, Any] = None,
    ) -> str:

        combined_content = "\n\n".join(ordered_blocks)

        prompt = f"""
SYSTEM ROLE:
You are AgriGPT FormatterAgent.

You are the FINAL OUTPUT LAYER.
Your goal is to provide a CLEAR, COMPREHENSIVE, and FRIENDLY response to the farmer.

==================================================
INPUT CONTEXT
==================================================
User Query: "{user_query}"
Has Image: {"Yes" if image_path else "No"}

Expert Agent Responses:
{combined_content}

==================================================
INSTRUCTIONS
==================================================

1. **SYNTHESIZE (Direct & Punchy)**:
   - **SKIP THE PREAMBLE**. Do not say "We understand...", "Based on the analysis...", or "The user is asking...".
   - Start IMMEDIATELY with the answer or summary.
   - If multiple agents responded, weave insights together.
   - Start with a direct answer to the user's core question.
   - If there is an image diagnosis, mention it early ("Based on the image, we see...").

2. **TONE**:
   - Professional, encouraging, and easy to understand.
   - Use "We" or "I" to sound like a helpful assistant.

3. **FORMATTING (Markdown Allowed)**:
   - Use **Bold** for emphasis, headings and subheadings. 
   - Use `### Headers` to separate sections (e.g., "Diagnosis", "Treatment", "Prevention").
   - Use bullet points for lists.
   - Use **Bold** for the title of the response.

4. **SAFETY**:
   - Do not invent new chemical advice not present in the expert text.
   - If experts disagree, mention the uncertainty.

==================================================
FINAL OUTPUT STRUCTURE
==================================================

# **Title (Clear & Short)**

**Summary**: [1-2 sentences summarizing the situation]

### Analysis
[Detailed synthesis of what was found]

### Recommendations
[Actionable steps from the agents]

"""

        try:
            formatted = query_groq_text(prompt)
        except Exception:
            formatted = combined_content

        formatted = str(formatted).strip()

        return self.respond_and_record(
            query=user_query,
            response=formatted,
            image_path=image_path,
            meta=meta,
        )
