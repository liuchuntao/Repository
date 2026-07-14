from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=4000)
    device_context: Optional[Dict[str, Any]] = None


class EmotionResult(BaseModel):
    label: str
    intensity: float
    valence: float
    arousal: float
    confidence: float
    cues: List[str] = []


class CompanionState(BaseModel):
    mood: str
    energy: float
    intimacy: float
    trust: float
    interaction_count: int


class ChatResponse(BaseModel):
    reply: str
    emotion: EmotionResult
    companion_state: CompanionState
    recalled_memories: List[str]
    safety_mode: bool = False


class ProfileResponse(BaseModel):
    user_id: str
    companion_name: str
    preferences: Dict[str, Any]
    state: CompanionState
    recent_memories: List[Dict[str, Any]]
