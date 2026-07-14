import os
from pathlib import Path

TEST_DB = Path("data/test_soulpal.db")
os.environ["DATABASE_PATH"] = str(TEST_DB)

from app.emotion import detect_emotion
from app.memory import extract_memories
from app.safety import check_safety
from app.state import evolve_state


def test_emotion_detection():
    result = detect_emotion("我今天真的很焦虑，晚上都睡不着")
    assert result.label == "焦虑"
    assert result.intensity > 0.4


def test_memory_extraction():
    memories = extract_memories("我喜欢下雨天，也请记住我不喝咖啡")
    contents = [x["content"] for x in memories]
    assert any("下雨天" in x for x in contents)
    assert any("不喝咖啡" in x for x in contents)


def test_safety_detection():
    result = check_safety("我真的不想活了")
    assert result.triggered is True
    assert result.category == "self_harm_crisis"


def test_state_growth():
    state = {"mood": "平静", "energy": 0.7, "intimacy": 0.1, "trust": 0.1, "interaction_count": 0}
    emotion = detect_emotion("谢谢你，我只告诉你这件事")
    next_state = evolve_state(state, emotion, "谢谢你，我只告诉你这件事")
    assert next_state["intimacy"] > state["intimacy"]
    assert next_state["trust"] > state["trust"]
    assert next_state["interaction_count"] == 1
