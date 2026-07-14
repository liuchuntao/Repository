from __future__ import annotations

from typing import Any, Dict
from .emotion import Emotion

MOOD_MAP = {"开心": "明亮", "难过": "温柔关切", "焦虑": "安定专注", "愤怒": "沉稳陪伴", "疲惫": "轻柔安静", "平静": "平静"}


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def evolve_state(current: Dict[str, Any], emotion: Emotion, message: str) -> Dict[str, Any]:
    count = int(current["interaction_count"]) + 1
    intimacy_gain, trust_gain = 0.004, 0.003
    if len(message) >= 30:
        intimacy_gain += 0.004
    if emotion.label in {"难过", "焦虑", "疲惫"}:
        trust_gain += 0.006
    if any(word in message for word in ["谢谢", "信任", "只告诉你", "记住"]):
        intimacy_gain += 0.012
        trust_gain += 0.012
    intimacy = clamp(float(current["intimacy"]) + intimacy_gain * (1.05 - float(current["intimacy"])))
    trust = clamp(float(current["trust"]) + trust_gain * (1.05 - float(current["trust"])))
    target_energy = 0.78 if emotion.label in {"开心", "愤怒", "焦虑"} else 0.48 if emotion.label in {"难过", "疲惫"} else 0.64
    energy = clamp(float(current["energy"]) * 0.75 + target_energy * 0.25)
    return {"mood": MOOD_MAP.get(emotion.label, "平静"), "energy": round(energy, 3), "intimacy": round(intimacy, 3), "trust": round(trust, 3), "interaction_count": count}
