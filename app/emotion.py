from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List


LEXICON: Dict[str, List[str]] = {
    "开心": ["开心", "高兴", "快乐", "兴奋", "太好了", "哈哈", "喜欢", "幸福", "期待", "爽"],
    "难过": ["难过", "伤心", "失落", "委屈", "想哭", "哭了", "孤独", "寂寞", "没意思"],
    "焦虑": ["焦虑", "紧张", "担心", "害怕", "不安", "压力", "慌", "怎么办", "睡不着"],
    "愤怒": ["生气", "愤怒", "烦死", "气死", "讨厌", "火大", "受不了", "滚"],
    "疲惫": ["累", "疲惫", "困", "没精神", "不想动", "精疲力尽"],
    "平静": ["还好", "平静", "正常", "一般", "没事"],
}

VALENCE = {"开心": 0.85, "平静": 0.10, "疲惫": -0.25, "焦虑": -0.55, "难过": -0.70, "愤怒": -0.65}
AROUSAL = {"开心": 0.65, "平静": 0.20, "疲惫": 0.18, "焦虑": 0.78, "难过": 0.42, "愤怒": 0.90}


@dataclass
class Emotion:
    label: str
    intensity: float
    valence: float
    arousal: float
    confidence: float
    cues: List[str]

    def as_dict(self):
        return {"label": self.label, "intensity": self.intensity, "valence": self.valence, "arousal": self.arousal, "confidence": self.confidence, "cues": self.cues}


def detect_emotion(text: str) -> Emotion:
    normalized = re.sub(r"\s+", "", text.lower())
    scores: Dict[str, float] = {label: 0.0 for label in LEXICON}
    cues: Dict[str, List[str]] = {label: [] for label in LEXICON}
    for label, words in LEXICON.items():
        for word in words:
            if word in normalized:
                scores[label] += 1.0 + min(len(word), 4) * 0.08
                cues[label].append(word)
    exclamations = text.count("！") + text.count("!") + text.count("？") + text.count("?")
    repetition = 1.0 if re.search(r"(.)\1{2,}", normalized) else 0.0
    best_label, best_score = max(scores.items(), key=lambda item: item[1])
    if best_score == 0:
        best_label = "平静"
    intensity = min(1.0, 0.30 + best_score * 0.18 + min(exclamations, 5) * 0.06 + repetition * 0.12)
    confidence = min(0.96, 0.48 + best_score * 0.15)
    if best_score == 0:
        intensity, confidence = 0.28, 0.42
    return Emotion(best_label, round(intensity, 3), VALENCE[best_label], AROUSAL[best_label], round(confidence, 3), cues[best_label][:5])
