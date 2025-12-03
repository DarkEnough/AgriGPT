from typing import List, Dict, Any
import collections

#Using deque to store the last 10 messages
_CHAT_MEMORY: Dict[str, collections.deque] = {}

MAX_HISTORY_LENGTH = 10

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """
    Retrieve the chat history for a given session ID.
    Returns a list of messages: [{"role": "user", "content": "..."}, ...]
    """
    if not session_id:
        return []
    
    if session_id not in _CHAT_MEMORY:
        return []
    
    return list(_CHAT_MEMORY[session_id])

def add_message_to_history(session_id: str, role: str, content: str):
    """
    Add a message to the session's history.
    Automatically trims to MAX_HISTORY_LENGTH.
    """
    if not session_id:
        return

    if session_id not in _CHAT_MEMORY:
        # Create a new deque with a fixed size limit
        _CHAT_MEMORY[session_id] = collections.deque(maxlen=MAX_HISTORY_LENGTH)
    
    _CHAT_MEMORY[session_id].append({"role": role, "content": content})

def format_history_for_prompt(history: List[Dict[str, str]]) -> str:
    """
    Convert list of messages into a string for LLM context.
    """
    if not history:
        return "No previous conversation."
    
    formatted = []
    for msg in history:
        role = msg["role"].upper()
        content = msg["content"]
        formatted.append(f"{role}: {content}")
    
    return "\n".join(formatted)

