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
✅ CONTEXT-AWARE (Memory)
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
from backend.core.memory_manager import get_chat_history, add_message_to_history, format_history_for_prompt

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
    image_path: Optional[str] = None,
    session_id: Optional[str] = None 
) -> str:

    registry = get_agent_registry()

    # 1. Input Validation
    clean_query = query.strip() if query else ""
    
    if clean_query and len(clean_query) > MAX_QUERY_CHARS:
        return "Your question is too long. Please shorten it."
    
    # 2. Get History
    chat_history_list = get_chat_history(session_id)
    chat_history_str = format_history_for_prompt(chat_history_list)

    # ========================================================
    # PATH A: IMAGE-ONLY (Direct Diagnosis)
    # ========================================================
    if image_path and not clean_query:
        pest_output = registry["PestAgent"].handle_query(
            query="",
            image_path=image_path,
            chat_history=chat_history_str
        )

        payload = {
            "user_query": "Image-based diagnosis",
            "routing_mode": "image_only",
            "agent_results": [
                {
                    "agent": "PestAgent",
                    "role": "primary",
                    "score": 100,
                    "content": pest_output,
                }
            ],
        }
        
        # Save Interaction
        if session_id:
             add_message_to_history(session_id, "user", "Uploaded an image")
             
        response = registry["FormatterAgent"].handle_query(payload) 
        
        if session_id:
             add_message_to_history(session_id, "assistant", response)
             
        return response

    if not clean_query:
        return "Please ask an agriculture-related question."

    # ========================================================
    # PATH B & C: TEXT-ONLY OR MULTIMODAL
    # ========================================================
    # 1. Semantic Routing (Text Intent + History)
    routed = llm_route_with_scores(clean_query, registry, chat_history_str)

    # 2. Fallback Logic
    if not routed:
        routed = [{"agent": "CropAgent", "role": "primary", "score": 0}]

    # 3. Ensure Primary Exists
    if not any(r["role"] == "primary" for r in routed):
        routed[0]["role"] = "primary"

    # 4. Image Injection (Multimodal Only)
    if image_path:
        pest_in_route = any(r["agent"] == "PestAgent" for r in routed)
        if not pest_in_route:
            routed.append({
                "agent": "PestAgent", 
                "role": "supporting", 
                "score": 100 
            })

    # 5. Execution Loop
    agent_results: List[Dict[str, Any]] = []
    
    # Limit execution count
    final_execution_list = routed[:MAX_ROUTED_AGENTS]
    
    if image_path and not any(r["agent"] == "PestAgent" for r in final_execution_list):
         final_execution_list[-1] = {"agent": "PestAgent", "role": "supporting", "score": 100}

    for item in final_execution_list:
        agent_name = item["agent"]
        role = item["role"]
        score = item.get("score", 0)

        if agent_name not in registry:
            continue

        # Pass History to Agent
        if agent_name == "PestAgent" and image_path:
            output = registry[agent_name].handle_query(
                query=clean_query, 
                image_path=image_path,
                chat_history=chat_history_str
            )
        else:
            output = registry[agent_name].handle_query(
                query=clean_query,
                chat_history=chat_history_str
            )

        agent_results.append({
            "agent": agent_name,
            "role": role,
            "score": score,
            "content": output,
        })

    # 6. Formatting
    payload = {
        "user_query": clean_query,
        "routing_mode": "multimodal" if image_path else "text_only",
        "agent_results": agent_results,
    }

    formatted_response = registry["FormatterAgent"].handle_query(payload)

    # 7. Save Interaction to Memory
    if session_id:
        add_message_to_history(session_id, "user", clean_query)
        add_message_to_history(session_id, "assistant", formatted_response)

    # Log Router Confidence
    score_summary = ", ".join(
        f"{res['agent']}: {res['score']}" 
        for res in agent_results 
        if 'score' in res
    )
    
    if score_summary:
        print(f"\n[ROUTER CONFIDENCE] {score_summary}\n")

    return formatted_response


# ============================================================
# LLM ROUTER WITH SCORING & THRESHOLDS
# ============================================================
def llm_route_with_scores(
    query: str,
    registry: Dict[str, Any],
    chat_history: str = ""
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

PREVIOUS CONVERSATION:
{chat_history}

RULES:
1. **Context Awareness**: If the user says "it", "that", or refers to a previous topic, use the HISTORY to infer the crop or issue.
2. **Score 0-100**: How well does the agent fit the query?
   - 90-100: Perfect match (Dominant Intent)
   - 70-89: Strong match
   - 50-69: Weak/Partial match
   - <50: Irrelevant
3. **Dominant Intent**: Identify the single most relevant agent.
4. **Multi-Intent**: Only include other agents if they truly cover a DISTINCT part of the query (score > 50).
5. **CropAgent Fallback**: If specific intent is unclear, CropAgent might have a moderate score, but prefer specific agents (Pest, Subsidy, etc.) if symptoms match.
6. **Output JSON ONLY**: Return a list of objects.

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
            if best_candidate["agent"] == "CropAgent":
                 final_routes.append({
                     "agent": "CropAgent", 
                     "role": "primary", 
                     "score": best_candidate["score"]
                 })
            else:
                 if best_candidate["score"] >= 50:
                     final_routes.append({
                         "agent": best_candidate["agent"], 
                         "role": "primary", 
                         "score": best_candidate["score"]
                     })
                 else:
                     return [{"agent": "CropAgent", "role": "primary", "score": 0}]

        # --- Secondary Selection ---
        for cand in candidates[1:]:
            if len(final_routes) >= MAX_ROUTED_AGENTS:
                break
            
            if cand["score"] >= SECONDARY_SCORE_THRESHOLD:
                final_routes.append({
                    "agent": cand["agent"], 
                    "role": "supporting", 
                    "score": cand["score"]
                })

        return final_routes

    except Exception as e:
        print(f"Router Error: {e}")
        return []
