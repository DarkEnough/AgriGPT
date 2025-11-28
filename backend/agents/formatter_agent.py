from typing import Any, Dict, List
from backend.services.text_service import query_groq_text
from backend.agents.agri_agent_base import AgriAgentBase


class FormatterAgent(AgriAgentBase):
    """
    FormatterAgent (PRODUCTION – GPT-OSS SAFE)

    Responsibilities:
    - Presentation only
    - Role-aware ordering
    - Zero hallucination surface
    - LLM used strictly for formatting
    """

    name = "FormatterAgent"

    # --------------------------------------------------
    # PUBLIC ENTRYPOINT
    # --------------------------------------------------
    def handle_query(self, payload: Any, image_path: str = None) -> str:

        # --------------------------------------------------
        # FAILSAFE — plain string input
        # --------------------------------------------------
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

        # --------------------------------------------------
        # STRUCTURED PAYLOAD (EXPECTED PATH)
        # --------------------------------------------------
        if not isinstance(payload, dict):
            return self.respond_and_record("", str(payload), image_path)

        user_query: str = str(payload.get("user_query", "")).strip()
        agent_results: List[Dict[str, str]] = payload.get("agent_results", [])
        routing_mode: str = str(payload.get("routing_mode", "unknown"))

        if not agent_results:
            return self.respond_and_record(
                user_query, "No agent responses were generated.", image_path
            )

        # --------------------------------------------------
        # DETERMINISTIC ROLE ORDER
        # --------------------------------------------------
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

        # --------------------------------------------------
        # BUILD ORDERED CONTENT BLOCKS
        # --------------------------------------------------
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

        # --------------------------------------------------
        # LOG META (✅ THIS IS WHAT WAS MISSING)
        # --------------------------------------------------
        meta = {
            "routing_mode": routing_mode,
            "agents": role_log,
            "agent_count": len(role_log),
        }

        # --------------------------------------------------
        # FORMAT USING LLM (PRESENTATION ONLY)
        # --------------------------------------------------
        return self._format_text(
            user_query=user_query,
            ordered_blocks=ordered_blocks,
            image_path=image_path,
            meta=meta,
        )

    # ==================================================
    # INTERNAL FORMATTER (SINGLE LLM CALL)
    # ==================================================
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
You are NOT an advisor.
You are NOT an expert.
You are NOT allowed to make decisions.

Your ONLY responsibility is PRESENTATION.

==================================================
CRITICAL CONTRACT (STRICT — DO NOT VIOLATE)
==================================================

The content below was written by domain experts.
It is already correct.

You MUST treat the content as READ-ONLY.

You MUST NOT:
- Add new advice
- Remove guidance
- Rewrite meaning
- Summarize expert logic
- Combine steps
- Correct agent content
- Infer missing information
- Modify numbers, dosages, timings, or instructions

==================================================
ALLOWED OPERATIONS (ONLY)
==================================================

You MAY:
- Fix grammar and spelling
- Improve sentence readability (meaning unchanged)
- Split long sentences
- Remove ONLY exact duplicate sentences
- Improve visual structure

==================================================
ORDERING GUARANTEE
==================================================

Content order is already correct:
1. PRIMARY
2. SUPPORTING
3. IMPACT

You must preserve this order exactly.

==================================================
OUTPUT FORMAT (STRICT)
==================================================

- One title (3–6 words)
- Bullet points using ONLY •
- One idea per bullet
- Simple, calm, farmer-friendly language
- One-line summary at the end

No markdown
No emojis
No extra headings
No special characters (except •)

==================================================
USER QUESTION (CONTEXT ONLY — DO NOT ANSWER):
{user_query}

==================================================
EXPERT CONTENT (DO NOT CHANGE MEANING):
{combined_content}

==================================================
FINAL OUTPUT:
Title
• Bullets
One-line summary
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
            meta=meta,   # ✅ LOG ROLES HERE
        )
