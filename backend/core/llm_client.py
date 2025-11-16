"""
llm_client.py
-------------
Creates a single LangChain ChatGroq client so every part of AgriGPT
talks to Groq through the exact same, well-documented interface.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Final

from langchain_groq import ChatGroq

from backend.core.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGroq:
    """
    Build (and cache) the LangChain ChatGroq client.

    We cache this because spinning up the LangChain wrappers is a bit expensive
    and we want every request to reuse the same underlying connection details.
    """
    # These values come from .env via pydantic Settings, so nothing is hard-coded.
    api_key: Final[str] = settings.GROQ_API_KEY
    model_name: Final[str] = settings.MODEL_NAME

    # Return a ready-to-chat client with friendly defaults for farmer-facing advice.
    return ChatGroq(
        groq_api_key=api_key,
        model_name=model_name,
        temperature=0.4,  # keep answers practical and consistent
        max_tokens=800,
    )

