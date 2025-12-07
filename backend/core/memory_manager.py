"""
memory_manager.py

Handles chat history and image persistence for user sessions.
Farmers can ask follow-up questions and we'll remember the context.
"""

from typing import List, Dict, Optional
import collections
import os
import shutil
from pathlib import Path
import time


# In-memory stores (reset on server restart)
_CHAT_MEMORY: Dict[str, collections.deque] = {}
_SESSION_IMAGES: Dict[str, str] = {}

# How many messages to keep per session
MAX_HISTORY_LENGTH = 10

# Where we save uploaded images so they survive the request lifecycle
SESSION_IMAGES_DIR = Path("backend/session_images")
SESSION_IMAGES_DIR.mkdir(exist_ok=True, parents=True)


# ─────────────────────────────────────────────────────────────
# Chat History
# ─────────────────────────────────────────────────────────────

def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    """Get the last N messages for this session."""
    if not session_id or session_id not in _CHAT_MEMORY:
        return []
    return list(_CHAT_MEMORY[session_id])


def add_message_to_history(session_id: str, role: str, content: str):
    """Save a message. The deque auto-trims to MAX_HISTORY_LENGTH."""
    if not session_id:
        return

    if session_id not in _CHAT_MEMORY:
        _CHAT_MEMORY[session_id] = collections.deque(maxlen=MAX_HISTORY_LENGTH)
    
    _CHAT_MEMORY[session_id].append({"role": role, "content": content})


def format_history_for_prompt(history: List[Dict[str, str]]) -> str:
    """Turn message list into a string the LLM can understand."""
    if not history:
        return "No previous conversation."
    
    lines = [f"{msg['role'].upper()}: {msg['content']}" for msg in history]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Image Persistence
# ─────────────────────────────────────────────────────────────

def set_session_image(session_id: str, image_path: str):
    """
    Copy the uploaded image to persistent storage.
    
    The temp file gets deleted after the request, so we need to
    save it somewhere else if we want to reference it later.
    """
    if not session_id or not image_path:
        return
    
    # Delete the old image if there is one
    if session_id in _SESSION_IMAGES:
        old_path = _SESSION_IMAGES[session_id]
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
    
    # Copy to our persistent folder
    try:
        ext = Path(image_path).suffix or ".jpg"
        new_path = SESSION_IMAGES_DIR / f"{session_id}_{int(time.time())}{ext}"
        shutil.copy2(image_path, new_path)
        _SESSION_IMAGES[session_id] = str(new_path)
    except Exception as e:
        print(f"Couldn't save session image: {e}")
        # Fallback - might break on follow-ups but better than nothing
        _SESSION_IMAGES[session_id] = image_path


def get_session_image(session_id: str) -> Optional[str]:
    """Get the image path for this session, if one was uploaded."""
    if not session_id:
        return None
    return _SESSION_IMAGES.get(session_id)


def clear_session_image(session_id: str):
    """Delete the stored image for this session."""
    if not session_id or session_id not in _SESSION_IMAGES:
        return
        
    image_path = _SESSION_IMAGES[session_id]
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
        except:
            pass
    
    del _SESSION_IMAGES[session_id]


def cleanup_old_session_images(max_age_hours: int = 24):
    """
    Delete images older than max_age_hours.
    Run this periodically (cron, startup, etc.) to free disk space.
    """
    if not SESSION_IMAGES_DIR.exists():
        return
    
    now = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for f in SESSION_IMAGES_DIR.glob("*"):
        if f.is_file():
            age = now - f.stat().st_mtime
            if age > max_age_seconds:
                try:
                    f.unlink()
                except:
                    pass
