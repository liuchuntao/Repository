from __future__ import annotations

from typing import Any, Dict

from .config import settings
from .db import db
from .emotion import detect_emotion
from .llm import generate_reply
from .memory import recall_memories, store_memories
from .prompt import build_system_prompt
from .safety import check_safety
from .state import evolve_state


async def chat(user_id: str, session_id: str, message: str, device_context: Dict[str, Any] | None = None) -> Dict[str, Any]:
    db.ensure_user(user_id)
    safety = check_safety(message)
    emotion = detect_emotion(message)
    current_state = db.get_state(user_id)
    next_state = evolve_state(current_state, emotion, message)
    db.update_state(user_id, next_state)
    db.add_message(user_id, session_id, "user", message, emotion.label)
    recalled = recall_memories(user_id, message, settings.max_memories)
    if safety.triggered:
        reply = safety.response
    else:
        history = db.get_recent_messages(user_id, session_id, settings.max_history_messages)
        if history and history[-1]["role"] == "user" and history[-1]["content"] == message:
            history = history[:-1]
        system_prompt = build_system_prompt(next_state, emotion, recalled, device_context)
        reply = await generate_reply(system_prompt, history, message)
    db.add_message(user_id, session_id, "assistant", reply)
    store_memories(user_id, message)
    return {
        "reply": reply,
        "emotion": emotion.as_dict(),
        "companion_state": next_state,
        "recalled_memories": [item["content"] for item in recalled],
        "safety_mode": safety.triggered,
    }
