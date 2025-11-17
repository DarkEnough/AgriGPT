"""
master_agent.py
---------------
Central orchestrator for routing user queries to the appropriate AgriGPT agent.
Now upgraded with LangChain so the model can *intelligently* pick the right
specialist based on the user's query.
"""

from __future__ import annotations

import json
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from backend.agents import (
    crop_agent,
    formatter_agent,
    irrigation_agent,
    pest_agent,
    subsidy_agent,
    yield_agent,
)
from backend.core.langchain_tools import AGENT_DESCRIPTIONS, AGENT_REGISTRY
from backend.core.llm_client import get_llm
from backend.services.text_service import query_groq_text

# Initialize agents once
crop = crop_agent.CropAgent()
pest = pest_agent.PestAgent()
irrigation = irrigation_agent.IrrigationAgent()
subsidy = subsidy_agent.SubsidyAgent()
yield_ = yield_agent.YieldAgent()
formatter = formatter_agent.FormatterAgent()

# --- LangChain setup -------------------------------------------------------
# One shared LLM instance that acts as a polite "router" deciding which agent fits best.
router_llm = get_llm()


def route_query(query: Optional[str] = None, image_path: Optional[str] = None) -> str:
    """
    Routes the user's input to the appropriate AgriGPT agent.

    Args:
        query (str, optional): The user's text query (e.g., "how to improve yield?")
        image_path (str, optional): The path of an uploaded crop image.

    Returns:
        str: Final formatted response from the relevant AgriGPT agent.
    """
    q = (query or "").lower().strip()

    #  Case 1: Combined Image + Text → Dual Reasoning
    if image_path and query:
        # Step 1: Analyze image using PestAgent
        pest_insight = pest.handle_query(image_path=image_path)

        # Step 2: Contextual reasoning from text (decide agent)
        if any(k in q for k in ["water", "irrigation", "moisture", "drip", "rain"]):
            context = irrigation.handle_query(query)
        elif any(k in q for k in ["yield", "harvest", "production", "output", "productivity"]):
            context = yield_.handle_query(query)
        elif any(k in q for k in ["subsidy", "scheme", "loan", "grant", "support", "fund"]):
            context = subsidy.handle_query(query)
        else:
            context = crop.handle_query(query)

        # Step 3: Merge image and text findings into one coherent answer
        combined_prompt = f"""
        You are AgriGPT, a multimodal agricultural expert.

        The farmer uploaded an image and asked:
        "{query}"

        Visual analysis of the image shows:
        {pest_insight}

        Contextual advice from the text query:
        {context}

        Combine these findings into one clear, actionable response.
        Keep it short, structured, and farmer-friendly.
        """

        combined_response = query_groq_text(combined_prompt)
        return formatter.handle_query(combined_response)

    #  Case 2: Image-only input → Pest/Disease Detection
    if image_path:
        response = pest.handle_query(image_path=image_path)
        return formatter.handle_query(response)

    #  Case 3: Text-only routing
    if not query:
        return "Please provide a query or an image for analysis."

    # Let LangChain reason about the best specialist for plain text questions.
    return _run_langchain_text_agent(query.strip())


def _run_langchain_text_agent(query: str) -> str:
    """
    Ask the LangChain LLM to deliberately pick the right domain expert.

    Instead of hard-coding keyword rules, we prompt the model with the list
    of available agents + descriptions, and ask it to reply with JSON containing
    the chosen agent and a short, human explanation.
    """
    if not query:
        return "Please share a bit more detail so I can help."

    agent_name, reasoning = _choose_agent_via_langchain(query)
    selected_agent = AGENT_REGISTRY.get(agent_name, crop)

    response = selected_agent.handle_query(query)
    formatted = formatter.handle_query(response)

    if reasoning:
        formatted += f"\n\n_(Routed to {agent_name} because: {reasoning})_"

    return formatted


def _choose_agent_via_langchain(query: str) -> tuple[str, str]:
    """
    Use a tiny prompt to capture the agent name + reason in JSON.
    Returns (agent_name, reason). Falls back to CropAgent on any parsing issues.
    """
    agent_list_text = "\n".join(
        f"- {item['name']}: {item['description']}" for item in AGENT_DESCRIPTIONS
    )
    system_prompt = (
        "You are AgriGPT Router. Your job is to pick the best domain expert for each farmer question.\n"
        "Available experts:\n"
        f"{agent_list_text}\n\n"
        "Respond ONLY with JSON in the form {\"agent\": \"<name>\", \"reason\": \"<short human explanation>\"}."
        "The agent value MUST be exactly one of the listed names."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query),
    ]

    ai_message = router_llm.invoke(messages)
    raw_content = _extract_text(ai_message.content)

    try:
        data = json.loads(raw_content)
        agent_name = data.get("agent", "CropAgent")
        reason = data.get("reason", "").strip()
    except Exception:
        agent_name = "CropAgent"
        reason = "Fell back to the general crop expert."

    if agent_name not in AGENT_REGISTRY:
        agent_name = "CropAgent"
        if not reason:
            reason = "Defaulted to the trusted crop expert."

    return agent_name, reason


def _extract_text(content) -> str:
    """
    LangChain messages sometimes return a plain string, other times a list of parts.
    This helper normalizes everything to a single string we can parse.
    """
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list) and content:
        # Some backends return [{"type": "text", "text": "..."}]
        first = content[0]
        if isinstance(first, dict) and "text" in first:
            return str(first["text"]).strip()
        return str(first).strip()
    return str(content).strip()
