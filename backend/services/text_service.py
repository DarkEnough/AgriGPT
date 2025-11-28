# backend/services/text_service.py
"""
Unified Text Service (Production-Stable)
----------------------------------------
Guarantees:
- Retry logic for Groq 429 / 5xx / network errors
- Consistent system message behavior
- Uses unified ChatGroq client
- Safe prompt truncation
- Always returns clean string output
"""

from __future__ import annotations
import time
from typing import Optional

from backend.core.llm_client import get_llm

# -------------------------------
# Retry configuration
# -------------------------------
MAX_RETRIES = 3
RETRY_BACKOFF = (1, 2, 4)

# -------------------------------
# Prompt safety limits
# -------------------------------
MAX_PROMPT_CHARS = 4000


def _normalize_output(output: Optional[str]) -> str:
    """Normalize model output safely into plain text."""
    if output is None:
        return ""
    if isinstance(output, str):
        return output.strip()
    try:
        return str(output).strip()
    except Exception:
        return ""


def _is_retryable_error(error: Exception) -> bool:
    """Detect Groq / network errors that should be retried."""
    msg = str(error).lower()
    return any(
        token in msg
        for token in (
            "429",
            "rate limit",
            "too many requests",
            "timeout",
            "timed out",
            "connection reset",
            "connection aborted",
            "service unavailable",
            "gateway timeout",
            "internal server error",
            "500",
            "502",
            "503",
            "504",
        )
    )


def query_groq_text(
    prompt: str,
    system_msg: str = (
        "You are AgriGPT, a domain-expert agricultural assistant. "
        "Follow instructions strictly. "
        "Do not add information unless explicitly asked. "
        "Be factual, concise, and safety-aware."
    ),
) -> str:
    """
    Primary text-generation entrypoint.

    - Uses GPT-OSS-120B via Groq
    - Always returns a safe string
    """

    if not isinstance(prompt, str) or not prompt.strip():
        return "No valid input was provided."

    # --------------------------------------------------
    # Enforce prompt length safety
    # --------------------------------------------------
    if len(prompt) > MAX_PROMPT_CHARS:
        prompt = (
            prompt[:MAX_PROMPT_CHARS]
            + f"\n[Input truncated to {MAX_PROMPT_CHARS} characters]"
        )

    llm = get_llm()

    for attempt in range(MAX_RETRIES):
        try:
            response = llm.invoke(
                [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ]
            )

            content = getattr(response, "content", None)
            cleaned = _normalize_output(content)

            if cleaned:
                return cleaned

            return "I could not generate a response at this moment. Please try again."

        except Exception as e:
            if attempt < MAX_RETRIES - 1 and _is_retryable_error(e):
                time.sleep(RETRY_BACKOFF[attempt])
                continue

            return "The system is temporarily unavailable. Please try again later."
