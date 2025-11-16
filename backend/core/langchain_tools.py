"""
langchain_tools.py
------------------
Keeps a single source of truth for the specialist agents PLUS short, friendly
descriptions so the LangChain router prompt can explain each tool in plain words.
"""

from __future__ import annotations

from typing import Dict, List

from backend.agents import (
    crop_agent,
    irrigation_agent,
    pest_agent,
    subsidy_agent,
    yield_agent,
)

# Spin up one instance of each agent so the LangChain layer shares logging + state.
CROP_AGENT = crop_agent.CropAgent()
PEST_AGENT = pest_agent.PestAgent()
IRRIGATION_AGENT = irrigation_agent.IrrigationAgent()
SUBSIDY_AGENT = subsidy_agent.SubsidyAgent()
YIELD_AGENT = yield_agent.YieldAgent()

# Registry so other modules (like master_agent) can reuse the same objects.
AGENT_REGISTRY: Dict[str, object] = {
    "CropAgent": CROP_AGENT,
    "PestAgent": PEST_AGENT,
    "IrrigationAgent": IRRIGATION_AGENT,
    "SubsidyAgent": SUBSIDY_AGENT,
    "YieldAgent": YIELD_AGENT,
}

# Lightweight descriptions that we can feed into the router prompt.
AGENT_DESCRIPTIONS: List[Dict[str, str]] = [
    {
        "name": CROP_AGENT.name,
        "description": "General crop advice, fertilizers, soil prep, growth stages, and friendly best practices.",
    },
    {
        "name": PEST_AGENT.name,
        "description": "Pest/disease identification, leaf spots, insect damage, and treatment suggestions.",
    },
    {
        "name": IRRIGATION_AGENT.name,
        "description": "Water scheduling, drip systems, rainfall management, and moisture troubleshooting.",
    },
    {
        "name": SUBSIDY_AGENT.name,
        "description": "Government schemes, subsidies, loans, grants, and financial assistance programs.",
    },
    {
        "name": YIELD_AGENT.name,
        "description": "Yield improvement, harvest timing, productivity tweaks, and high-output strategies.",
    },
]

