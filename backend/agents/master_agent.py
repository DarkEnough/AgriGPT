"""
Master Agent Router (LLM-FIRST, ROLE-AWARE)
------------------------------------------
✅ Fully LLM-based semantic + role routing
✅ Assigns roles: primary / supporting / impact
✅ Supports single or multi-agent (max 3)
✅ Formatter ALWAYS runs once
✅ CropAgent is LAST RESORT only
✅ OpenAPI-safe
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
import json
import re

from backend.core.langchain_tools import (
    get_agent_registry,
    NON_ROUTABLE_AGENTS,
    AGENT_DESCRIPTIONS,
)
from backend.core.llm_client import get_llm

MAX_QUERY_CHARS = 2000
MAX_ROUTED_AGENTS = 3


# ============================================================
# MAIN ENTRYPOINT
# ============================================================
def route_query(
    query: Optional[str] = None,
    image_path: Optional[str] = None
) -> str:

    registry = get_agent_registry()

    if query:
        query = query.strip()

    if query and len(query) > MAX_QUERY_CHARS:
        return "Your question is too long. Please shorten it."

    # --------------------------------------------------------
    # IMAGE → PestAgent ONLY
    # --------------------------------------------------------
    if image_path:
        pest_output = registry["PestAgent"].handle_query(
            query=query or "",
            image_path=image_path,
        )

        payload = {
            "user_query": query or "Image-based crop issue",
            "routing_mode": "single_agent",
            "agent_results": [
                {
                    "agent": "PestAgent",
                    "role": "primary",
                    "content": pest_output,
                }
            ],
        }

        return registry["FormatterAgent"].handle_query(
            json.dumps(payload, ensure_ascii=False)
        )

    if not query:
        return "Please ask an agriculture-related question."

    # --------------------------------------------------------
    # ✅ LLM SEMANTIC + ROLE ROUTING
    # --------------------------------------------------------
    routed = llm_route_with_roles(query, registry)

    # Hard fallback
    if not routed:
        routed = [{"agent": "CropAgent", "role": "primary"}]

    # Ensure exactly ONE primary
    if not any(r["role"] == "primary" for r in routed):
        routed[0]["role"] = "primary"

    agent_results: List[Dict[str, str]] = []

    for item in routed[:MAX_ROUTED_AGENTS]:
        agent_name = item["agent"]
        role = item["role"]

        output = registry[agent_name].handle_query(query=query)

        agent_results.append({
            "agent": agent_name,
            "role": role,
            "content": output,
        })

    payload = {
        "user_query": query,
        "routing_mode": "multi_agent" if len(agent_results) > 1 else "single_agent",
        "agent_results": agent_results,
    }

    # ✅ Formatter ALWAYS runs once
    return registry["FormatterAgent"].handle_query(
        payload
    )


# ============================================================
# LLM ROUTER WITH ROLE ASSIGNMENT
# ============================================================
def llm_route_with_roles(
    query: str,
    registry: Dict[str, Any],
) -> List[Dict[str, str]]:

    llm = get_llm()

    agent_map = "\n".join(
        f"- {a['name']}: {a['description']}"
        for a in AGENT_DESCRIPTIONS
    )

    prompt = f"""
You are an agricultural AI intent router.

TASK:
Select the best agent(s) AND assign roles.

ROLES:
- primary: main diagnosis or answer
- supporting: adds clarification
- impact: explains effects or next steps

STRICT RULES:
- Select ONE to THREE agents only
- EXACTLY ONE agent must be primary
- NEVER select FormatterAgent
- NEVER select CropAgent IF another agent fits
- CropAgent only if no others apply
- Output VALID JSON ARRAY ONLY

AVAILABLE AGENTS:
{agent_map}

FARMER QUERY:
{query}

OUTPUT FORMAT:
[
  {{ "agent": "PestAgent", "role": "primary" }},
  {{ "agent": "YieldAgent", "role": "impact" }}
]
"""

    try:
        raw = llm.invoke(prompt).content
        match = re.search(r"\[.*\]", raw, re.DOTALL)

        if not match:
            raise ValueError("No JSON")

        parsed = json.loads(match.group())

        cleaned = []
        seen = set()

        for item in parsed:
            agent = item.get("agent")
            role = item.get("role")

            if (
                agent in registry
                and agent not in NON_ROUTABLE_AGENTS
                and agent not in seen
                and role in {"primary", "supporting", "impact"}
            ):
                cleaned.append({"agent": agent, "role": role})
                seen.add(agent)

        return cleaned[:MAX_ROUTED_AGENTS]

    except Exception:
        return []
