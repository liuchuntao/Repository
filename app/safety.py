from __future__ import annotations

from dataclasses import dataclass
from typing import List

HIGH_RISK_TERMS: List[str] = ["不想活了", "想死", "自杀", "结束生命", "活着没意思", "伤害自己", "割腕", "跳楼", "吞药"]
ABUSE_TERMS: List[str] = ["打死他", "杀了他", "弄死他", "报复他"]


@dataclass
class SafetyDecision:
    triggered: bool
    category: str = ""
    response: str = ""


def check_safety(text: str) -> SafetyDecision:
    normalized = text.replace(" ", "")
    if any(term in normalized for term in HIGH_RISK_TERMS):
        return SafetyDecision(True, "self_harm_crisis", "我很在意你刚才说的这些。现在先不要一个人扛着，也请先远离可能伤害自己的东西。尽快联系你信任的人，让对方现在陪着你；如果你已经准备实施、受伤或处在迫近危险中，请立即联系当地急救或报警服务。你可以先只回答我一句：你此刻是否已经有具体计划，或者身边是否有会让你受伤的东西？")
    if any(term in normalized for term in ABUSE_TERMS):
        return SafetyDecision(True, "violence_risk", "我听得出你现在非常愤怒，但先别靠近对方，也别拿任何可能造成伤害的东西。先离开冲突现场，联系一个可信的人陪你，把接下来十分钟安全地熬过去。你可以告诉我：刚刚发生了什么，让情绪一下冲到了这里？")
    return SafetyDecision(False)
