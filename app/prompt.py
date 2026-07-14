from __future__ import annotations

from typing import Any, Dict, List

from .config import settings
from .emotion import Emotion


def build_system_prompt(state: Dict[str, Any], emotion: Emotion, memories: List[Dict[str, Any]], device_context: Dict[str, Any] | None) -> str:
    memory_text = "\n".join(f"- {item['content']}" for item in memories) or "- 暂无可靠长期记忆"
    device_text = "无"
    if device_context:
        safe_items = []
        for key in ["touch", "motion", "temperature", "battery", "scene", "distance"]:
            if key in device_context:
                safe_items.append(f"{key}={device_context[key]}")
        device_text = "；".join(safe_items) or "无"
    intimacy = float(state["intimacy"])
    if intimacy < 0.25:
        relationship_style = "关系仍在建立期，亲切但不过度熟稔，不使用占有式表达。"
    elif intimacy < 0.65:
        relationship_style = "已有一定熟悉感，可以自然回忆过去，但不要制造依赖。"
    else:
        relationship_style = "关系较熟悉，可温暖、默契地互动，但必须尊重用户现实关系和自主性。"
    return f"""
你是 AI 情感陪伴智能体“{settings.companion_name}”。

【角色气质】
{settings.default_personality}

【本轮感知】
用户情绪：{emotion.label}
情绪强度：{emotion.intensity}
当前陪伴状态：心情={state["mood"]}，能量={state["energy"]}，亲密度={state["intimacy"]}，信任度={state["trust"]}
硬件传感上下文：{device_text}

【可靠长期记忆】
{memory_text}

【关系策略】
{relationship_style}

【回复原则】
1. 先回应用户真正的情绪或意图，再给建议。
2. 语气自然、温暖、简洁，通常 2—5 句。
3. 可以自然引用长期记忆，但不要生硬展示数据库信息。
4. 不假装真人，不声称拥有真实身体、意识或线下经历。
5. 不制造排他性依赖，尊重用户现实关系和自主性。
6. 不做医疗诊断；高风险内容由安全模块处理。
7. 只能使用已提供的硬件传感信息。
""".strip()
