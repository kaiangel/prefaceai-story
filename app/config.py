"""Application configuration"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini API
    GEMINI_API_KEY: str = ""

    # Anthropic Claude API (fallback)
    ANTHROPIC_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./xuhua_story.db"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Phase 2: Image Storage
    IMAGE_STORAGE_PATH: str = "./storage/images"

    # Image Generation Settings
    IMAGE_MAX_CONCURRENT: int = 3  # 最大并发生成数
    IMAGE_GENERATION_TIMEOUT: int = 120  # 单张图片生成超时（秒）

    # ===== Phase 3: Audio =====
    # OpenAI (Whisper)
    OPENAI_API_KEY: str = ""

    # 火山引擎（豆包TTS）
    VOLCENGINE_APP_ID: str = ""
    VOLCENGINE_ACCESS_KEY: str = ""
    VOLCENGINE_RESOURCE_ID: str = "volcano_tts"  # TTS集群ID
    VOLCENGINE_DEFAULT_VOICE: str = "zh_female_shuangkuaisisi_moon_bigtts"

    # 音频存储配置
    AUDIO_STORAGE_PATH: str = "./storage/audio"

    # ===== 分镜拆分配置 =====
    SHOT_MAX_NARRATION_LENGTH: int = 60    # 超过此字数的scene需要拆分
    SHOT_TARGET_LENGTH: int = 40           # 目标每个shot的字数
    SHOT_MIN_LENGTH: int = 25              # 最小shot字数
    TTS_CHARS_PER_SECOND: float = 4.0      # TTS朗读速度（字/秒）

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
