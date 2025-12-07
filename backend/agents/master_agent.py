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
from backend.core.memory_manager import (
    get_chat_history, 
    add_message_to_history, 
    format_history_for_prompt,
    set_session_image,
    get_session_image,
)

MAX_QUERY_CHARS = 2000
MAX_ROUTED_AGENTS = 3

PRIMARY_SCORE_THRESHOLD = 75  
SECONDARY_SCORE_THRESHOLD = 50  


def route_query(
    query: Optional[str] = None,
    image_path: Optional[str] = None,
    session_id: Optional[str] = None 
) -> str:

    registry = get_agent_registry()

    clean_query = query.strip() if query else ""
    
    if clean_query and len(clean_query) > MAX_QUERY_CHARS:
        return "Your question is too long. Please shorten it."
    
    chat_history_list = get_chat_history(session_id)
    chat_history_str = format_history_for_prompt(chat_history_list)
    
    # Image Persistence: Save new image or retrieve saved one
    if image_path and session_id:
        set_session_image(session_id, image_path)
    elif not image_path and session_id:
        image_path = get_session_image(session_id)

    # IMAGE-ONLY (Direct Diagnosis)
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
        
        if session_id:
             add_message_to_history(session_id, "user", "Uploaded an image")
             
        response = registry["FormatterAgent"].handle_query(payload) 
        
        if session_id:
             add_message_to_history(session_id, "assistant", response)
             
        return response

    if not clean_query:
        return "Please ask an agriculture-related question."

    # TEXT-ONLY OR MULTIMODAL
    routed = llm_route_with_scores(clean_query, registry, chat_history_str)

    if not routed:
        routed = [{"agent": "CropAgent", "role": "primary", "score": 0}]

    if not any(r["role"] == "primary" for r in routed):
        routed[0]["role"] = "primary"

    # CLARIFICATION CHECK
    # If the Router chose ClarificationAgent as PRIMARY, execute it alone.
    primary_agent = next((r for r in routed if r["role"] == "primary"), None)
    
    if primary_agent and primary_agent["agent"] == "ClarificationAgent":
        clarification_output = registry["ClarificationAgent"].handle_query(
            query=clean_query,
            image_path=image_path,
            chat_history=chat_history_str
        )
        
        if session_id:
            add_message_to_history(session_id, "user", clean_query)
            add_message_to_history(session_id, "assistant", clarification_output)
            
        return clarification_output

    # Image Injection (Multimodal)
    if image_path:
        pest_in_route = any(r["agent"] == "PestAgent" for r in routed)
        if not pest_in_route:
            routed.append({
                "agent": "PestAgent", 
                "role": "supporting", 
                "score": 100 
            })

    agent_results: List[Dict[str, Any]] = []
    
    final_execution_list = routed[:MAX_ROUTED_AGENTS]
    
    if image_path and not any(r["agent"] == "PestAgent" for r in final_execution_list):
         final_execution_list[-1] = {"agent": "PestAgent", "role": "supporting", "score": 100}

    for item in final_execution_list:
        agent_name = item["agent"]
        role = item["role"]
        score = item.get("score", 0)

        if agent_name not in registry:
            continue

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

    payload = {
        "user_query": clean_query,
        "routing_mode": "multimodal" if image_path else "text_only",
        "agent_results": agent_results,
    }

    formatted_response = registry["FormatterAgent"].handle_query(payload)

    if session_id:
        add_message_to_history(session_id, "user", clean_query)
        add_message_to_history(session_id, "assistant", formatted_response)

    score_summary = ", ".join(
        f"{res['agent']}: {res['score']}" 
        for res in agent_results 
        if 'score' in res
    )
    
    if score_summary:
        print(f"\n[ROUTER CONFIDENCE] {score_summary}\n")

    return formatted_response


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

        raw = llm.invoke(prompt).content
        
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in router response")

        parsed = json.loads(match.group())

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

        candidates.sort(key=lambda x: x["score"], reverse=True)

        final_routes = []
        
        if not candidates:
            return []

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
