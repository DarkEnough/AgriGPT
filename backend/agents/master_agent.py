"""
Master Agent Router (LLM-FIRST, SCORING-AWARE)
---------------------------------------------
✅ Fully LLM-based semantic + role routing
✅ Stricter intent scoring & dominant-intent thresholding
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

# Thresholds for stricter routing
PRIMARY_SCORE_THRESHOLD = 75  # Dominant intent must be strong
SECONDARY_SCORE_THRESHOLD = 50  # Supporting agents must be relevant


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
                    "score": 100,
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
    # ✅ LLM SEMANTIC + SCORE-BASED ROUTING
    # --------------------------------------------------------
    routed = llm_route_with_scores(query, registry)

    # Hard fallback if router returns empty or low confidence
    if not routed:
        routed = [{"agent": "CropAgent", "role": "primary", "score": 0}]

    # Ensure exactly ONE primary (the logic in llm_route_with_scores should handle this, but double check)
    primary_exists = any(r["role"] == "primary" for r in routed)
    if not primary_exists and routed:
        routed[0]["role"] = "primary"

    agent_results: List[Dict[str, Any]] = []

    for item in routed[:MAX_ROUTED_AGENTS]:
        agent_name = item["agent"]
        role = item["role"]
        score = item.get("score", 0)

        # Double check registry
        if agent_name not in registry:
            continue

        output = registry[agent_name].handle_query(query=query)

        agent_results.append({
            "agent": agent_name,
            "role": role,
            "score": score,
            "content": output,
        })

    payload = {
        "user_query": query,
        "routing_mode": "multi_agent" if len(agent_results) > 1 else "single_agent",
        "agent_results": agent_results,
    }

    # ✅ Formatter ALWAYS runs once
    formatted_response = registry["FormatterAgent"].handle_query(payload)

    # ✅ Append Router Scores for visibility
    score_summary = ", ".join(
        f"{res['agent']}: {res['score']}" 
        for res in agent_results 
        if 'score' in res
    )
    
    if score_summary:
        formatted_response += f"\n\n**Router Confidence:** {score_summary}"

    return formatted_response


# ============================================================
# LLM ROUTER WITH SCORING & THRESHOLDS
# ============================================================
def llm_route_with_scores(
    query: str,
    registry: Dict[str, Any],
) -> List[Dict[str, Any]]:

    llm = get_llm()

    agent_map = "\n".join(
        f"- {a['name']}: {a['description']}"
        for a in AGENT_DESCRIPTIONS
    )

    prompt = f"""
You are an agricultural AI intent router.

TASK:
Analyze the farmer's query and assign a RELEVANCE SCORE (0-100) to EACH available agent.

AVAILABLE AGENTS:
{agent_map}

RULES:
1. **Score 0-100**: How well does the agent fit the query?
   - 90-100: Perfect match (Dominant Intent)
   - 70-89: Strong match
   - 50-69: Weak/Partial match
   - <50: Irrelevant
2. **Dominant Intent**: Identify the single most relevant agent.
3. **Multi-Intent**: Only include other agents if they truly cover a DISTINCT part of the query (score > 50).
4. **CropAgent Fallback**: If specific intent is unclear, CropAgent might have a moderate score, but prefer specific agents (Pest, Subsidy, etc.) if symptoms match.
5. **Output JSON ONLY**: Return a list of objects.

FARMER QUERY:
"{query}"

OUTPUT FORMAT (JSON Array):
[
  {{ "agent": "AgentName", "score": 95, "reason": "..." }},
  ...
]
"""

    try:
        # 1. Invoke LLM
        raw = llm.invoke(prompt).content
        
        # 2. Extract JSON
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in router response")

        parsed = json.loads(match.group())

        # 3. Normalize & Sort
        candidates = []
        seen = set()

        for item in parsed:
            agent = item.get("agent")
            score = item.get("score", 0)

            if (
                agent in registry
                and agent not in NON_ROUTABLE_AGENTS
                and agent not in seen
            ):
                candidates.append({"agent": agent, "score": score})
                seen.add(agent)

        # Sort by score descending
        candidates.sort(key=lambda x: x["score"], reverse=True)

        # 4. Apply Logic & Thresholds
        final_routes = []
        
        if not candidates:
            return []

        # --- Primary Selection ---
        best_candidate = candidates[0]
        if best_candidate["score"] >= PRIMARY_SCORE_THRESHOLD:
            final_routes.append({
                "agent": best_candidate["agent"], 
                "role": "primary", 
                "score": best_candidate["score"]
            })
        else:
            # If even the best score is weak, default to CropAgent (General) 
            # unless the best candidate IS CropAgent (then keep it)
            if best_candidate["agent"] == "CropAgent":
                 final_routes.append({
                     "agent": "CropAgent", 
                     "role": "primary", 
                     "score": best_candidate["score"]
                 })
            else:
                 # Fallback: Low confidence on specific agents -> General CropAgent
                 # But if the score is decent (e.g. 60), maybe we keep it? 
                 # If score < 75, we treat it as "General/Unsure" -> CropAgent.
                 # However, to be safe, let's include the best match if it's > 50, otherwise CropAgent.
                 if best_candidate["score"] >= 50:
                     final_routes.append({
                         "agent": best_candidate["agent"], 
                         "role": "primary", 
                         "score": best_candidate["score"]
                     })
                 else:
                     return [{"agent": "CropAgent", "role": "primary", "score": 0}]

        # --- Secondary Selection ---
        primary_agent = final_routes[0]["agent"]
        
        for cand in candidates[1:]:
            if len(final_routes) >= MAX_ROUTED_AGENTS:
                break
            
            # Threshold check for secondary
            if cand["score"] >= SECONDARY_SCORE_THRESHOLD:
                # Assign role based on score gap or nature? 
                # Simplified: secondary is 'supporting' or 'impact'.
                # Let's default to 'supporting' for now.
                final_routes.append({
                    "agent": cand["agent"], 
                    "role": "supporting", 
                    "score": cand["score"]
                })

        return final_routes

    except Exception as e:
        print(f"Router Error: {e}")
        return []
