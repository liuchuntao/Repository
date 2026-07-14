from __future__ import annotations

from typing import Dict, List

import httpx

from .config import settings


class LLMError(RuntimeError):
    pass


async def generate_reply(system_prompt: str, history: List[Dict], user_message: str) -> str:
    if not (settings.llm_base_url and settings.llm_api_key and settings.llm_model):
        return fallback_reply(user_message)
    messages = [{"role": "system", "content": system_prompt}]
    for item in history:
        if item["role"] in {"user", "assistant"}:
            messages.append({"role": item["role"], "content": item["content"]})
    messages.append({"role": "user", "content": user_message})
    url = f"{settings.llm_base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    payload = {"model": settings.llm_model, "messages": messages, "temperature": 0.78, "top_p": 0.92, "max_tokens": 500}
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"].strip()
            if not content:
                raise LLMError("模型返回了空内容")
            return content
    except (httpx.HTTPError, KeyError, IndexError, TypeError, LLMError):
        return fallback_reply(user_message, degraded=True)


def fallback_reply(message: str, degraded: bool = False) -> str:
    prefix = "刚刚网络有点走神，不过我还在。 " if degraded else ""
    text = message.strip()
    if any(word in text for word in ["难过", "伤心", "委屈", "想哭"]):
        return prefix + "听起来这件事真的压在你心上了。先不用急着把自己劝好，你愿意跟我说说，最刺痛你的那一部分是什么吗？"
    if any(word in text for word in ["焦虑", "紧张", "担心", "睡不着"]):
        return prefix + "我在。咱们先不一次解决全部，只找眼下最让你不安的那一件事。它更像是怕结果不好，还是不知道下一步怎么做？"
    if any(word in text for word in ["累", "疲惫", "困", "没精神"]):
        return prefix + "听上去你已经撑了一阵子。现在不用表现得很有力气，先给自己几分钟缓下来。今天最消耗你的是什么？"
    if any(word in text for word in ["开心", "高兴", "太好了", "哈哈"]):
        return prefix + "这份开心我接住啦。快讲讲，是什么好事让你一下亮起来了？"
    if any(word in text for word in ["生气", "气死", "烦死", "受不了"]):
        return prefix + "这确实很让人上火。你先把最气的那句话说出来，我不急着替任何人解释。"
    return prefix + "我在听。你可以接着说，不用先整理得很完整。"
