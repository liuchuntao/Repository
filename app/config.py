from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "SoulPal AI 情感陪伴智能体")
    database_path: str = os.getenv("DATABASE_PATH", "data/soulpal.db")

    # 支持任意 OpenAI-compatible Chat Completions 服务。
    llm_base_url: str = os.getenv("LLM_BASE_URL", "").rstrip("/")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "40"))

    companion_name: str = os.getenv("COMPANION_NAME", "小栖")
    default_personality: str = os.getenv(
        "DEFAULT_PERSONALITY",
        "温暖、敏锐、自然、不说教，偶尔有一点俏皮；重视倾听和长期陪伴。"
    )
    max_history_messages: int = int(os.getenv("MAX_HISTORY_MESSAGES", "12"))
    max_memories: int = int(os.getenv("MAX_MEMORIES", "6"))


settings = Settings()
