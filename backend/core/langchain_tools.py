"""
OpenAPI-safe langchain_tools.py
--------------------------------
NO global agent instances.
Only pure data objects are allowed globally.
Factories create agents on demand.
"""

from __future__ import annotations
from typing import Dict, List, TypeAlias

# Import agent classes (no instantiation)
from backend.agents.crop_agent import CropAgent
from backend.agents.irrigation_agent import IrrigationAgent
from backend.agents.pest_agent import PestAgent
from backend.agents.subsidy_agent import SubsidyAgent
from backend.agents.yield_agent import YieldAgent
from backend.agents.formatter_agent import FormatterAgent


# =========================================================
# TYPES
# =========================================================
AgentRegistry: TypeAlias = Dict[str, object]


# =========================================================
# NON-ROUTABLE AGENTS
# =========================================================
# FormatterAgent must NEVER be selected by router
NON_ROUTABLE_AGENTS = {"FormatterAgent"}


# =========================================================
# FACTORY: CREATE CLEAN AGENT INSTANCES
# =========================================================
def get_agent_registry() -> AgentRegistry:
    """
    Return a fresh registry on each call.

    ✅ No global state
    ✅ OpenAPI-safe
    ✅ Works with FastAPI reload
    ✅ Prevents stale agent memory
    """
    return {
        "CropAgent": CropAgent(),
        "PestAgent": PestAgent(),
        "IrrigationAgent": IrrigationAgent(),
        "SubsidyAgent": SubsidyAgent(),
        "YieldAgent": YieldAgent(),
        "FormatterAgent": FormatterAgent(),
    }


# =========================================================
# ROUTER METADATA (PURE DATA — SAFE)
# =========================================================
AGENT_DESCRIPTIONS: List[dict] = [
    {
        "name": "CropAgent",
        "description": (
            "General crop management and cultivation advice. "
            "Use for fertilizer selection and dosage, soil preparation, "
            "planting methods, crop growth stages, crop rotation, "
            "and overall best farming practices. "
            "Also use if the query is broad or unclear and needs general guidance."
        ),
    },
    {
        "name": "PestAgent",
        "description": (
            "Pest, disease, or nutrient deficiency diagnosis. "
            "Use when the farmer reports insects, worms, larvae, "
            "leaf spots, fungal or bacterial infection, "
            "yellowing, curling, wilting, discoloration, or damage symptoms. "
            "This agent MUST be selected for image-based crop problems."
        ),
    },
    {
        "name": "IrrigationAgent",
        "description": (
            "Irrigation and water management expert. "
            "Use for watering frequency, irrigation scheduling, "
            "water stress (overwatering or drought), soil moisture, "
            "drip or sprinkler systems, and water-saving practices."
        ),
    },
    {
        "name": "YieldAgent",
        "description": (
            "Yield improvement and productivity analysis. "
            "Use when the farmer mentions low yield, poor harvest, "
            "reduced output, small fruits, fewer tillers, "
            "or asks how to increase crop productivity."
        ),
    },
    {
        "name": "SubsidyAgent",
        "description": (
            "Government subsidy and agricultural scheme information (India-focused). "
            "Use for PM-Kisan, loan support, crop insurance, "
            "drip irrigation subsidy, equipment or machinery grants, "
            "and eligibility for government financial assistance."
        ),
    },
]
