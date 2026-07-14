from __future__ import annotations

import re
from typing import Dict, List, Tuple

from .db import db


STOP_WORDS = {
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "这个", "那个",
    "就是", "然后", "但是", "因为", "所以", "还是", "已经", "现在", "今天",
    "真的", "感觉", "有点", "一个", "什么", "怎么", "可以", "需要", "觉得",
}

MEMORY_PATTERNS: List[Tuple[str, str, float]] = [
    (r"我(?:叫|是)([\u4e00-\u9fa5A-Za-z0-9_·]{2,20})", "身份", 0.95),
    (r"我喜欢(.{1,40})", "偏好", 0.85),
    (r"我不喜欢(.{1,40})", "偏好", 0.85),
    (r"我最喜欢(.{1,40})", "偏好", 0.92),
    (r"我的生日是(.{1,30})", "重要日期", 0.98),
    (r"我(?:在|住在)(.{1,30})", "地点", 0.75),
    (r"我(?:正在|最近在)(.{1,50})", "近况", 0.65),
    (r"记住[：:]?(.{2,80})", "显式记忆", 1.00),
]


def extract_terms(text: str) -> List[str]:
    chunks = re.findall(r"[\u4e00-\u9fa5]{2,8}|[A-Za-z0-9_]{3,}", text)
    terms = []
    for chunk in chunks:
        if chunk not in STOP_WORDS and chunk not in terms:
            terms.append(chunk)
    return terms[:16]


def extract_memories(text: str) -> List[Dict]:
    found: List[Dict] = []
    stripped = text.strip()
    for pattern, category, importance in MEMORY_PATTERNS:
        for match in re.finditer(pattern, stripped):
            value = match.group(1).strip("，。！？,.!? ")
            if len(value) < 2:
                continue
            if category == "身份":
                content = f"用户称自己为{value}"
            elif category == "偏好":
                prefix = "用户不喜欢" if "不喜欢" in match.group(0) else "用户喜欢"
                content = f"{prefix}{value}"
            elif category == "重要日期":
                content = f"用户的生日是{value}"
            elif category == "地点":
                content = f"用户所在或居住地点是{value}"
            elif category == "近况":
                content = f"用户近期在{value}"
            else:
                content = value
            found.append({"content": content[:120], "category": category, "importance": importance})
    emotional_markers = ["第一次", "终于", "分手", "离职", "入职", "结婚", "生日", "考试", "面试"]
    if any(marker in stripped for marker in emotional_markers) and len(stripped) <= 160:
        found.append({"content": f"用户提到一件值得后续关心的事情：{stripped}", "category": "重要经历", "importance": 0.72})
    unique, seen = [], set()
    for item in found:
        if item["content"] not in seen:
            seen.add(item["content"])
            unique.append(item)
    return unique[:4]


def store_memories(user_id: str, source_message: str) -> List[str]:
    stored = []
    for item in extract_memories(source_message):
        if db.add_memory(user_id, item["content"], item["category"], item["importance"], source_message):
            stored.append(item["content"])
    return stored


def recall_memories(user_id: str, query: str, limit: int) -> List[Dict]:
    return db.search_memories(user_id, extract_terms(query), limit)
