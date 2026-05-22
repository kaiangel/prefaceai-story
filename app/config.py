"""Application configuration"""

from functools import lru_cache
from urllib.parse import quote_plus
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Gemini API
    GEMINI_API_KEY: str = ""

    # Anthropic Claude API (fallback)
    ANTHROPIC_API_KEY: str = ""

    # Database
    DATABASE_URL: str = ""
    MYSQL_HOST: str = ""
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = ""
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = ""

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # Phase 2: Image Storage
    IMAGE_STORAGE_PATH: str = "./storage/images"

    # Image Generation Settings
    IMAGE_MAX_CONCURRENT: int = 3  # 最大并发生成数
    IMAGE_GENERATION_TIMEOUT: int = 210  # Wave 11.4: 防 Seedream 长尾 (177s+) 偶发超时, +30s buffer. 跟 SEEDREAM_TIMEOUT_SEC 统一

    # ===== Phase 3: Audio =====
    # OpenAI (Whisper)
    OPENAI_API_KEY: str = ""

    # 火山引擎（豆包TTS）
    VOLCENGINE_APP_ID: str = ""
    VOLCENGINE_ACCESS_KEY: str = ""          # Access Token（Bearer Auth，TTS HTTP API 直接使用）
    VOLCENGINE_API_KEY: str = ""             # API Key（控制台 → 访问控制，供签名鉴权备用）
    VOLCENGINE_SECRET_KEY: str = ""          # Secret Access Key（供签名鉴权备用）
    VOLCENGINE_RESOURCE_ID: str = "volcano_tts"  # TTS集群ID
    VOLCENGINE_DEFAULT_VOICE: str = "zh_female_shuangkuaisisi_moon_bigtts"

    # 音频存储配置
    AUDIO_STORAGE_PATH: str = "./storage/audio"

    # Mureka AI 音乐生成
    MUREKA_API_KEY: str = ""                 # Mureka AI 音乐生成 API Key

    # Stage 5 跳过模式（开发用：用 R8 测试图片代替生图）
    SKIP_IMAGE_GENERATION: bool = False

    # Prompt 格式：b_prime（默认，省 46% token）| legacy（A 格式原版）
    PROMPT_FORMAT: str = "b_prime"

    # 图像生成 Provider（TASK-SEEDREAM-INTEGRATION）
    # "nb2"      → Nano Banana 2（Gemini 3.1 Flash Image Preview），MVP 默认主力
    # "seedream" → Seedream 5.0-lite（火山方舟国内版），测试期主力（成本降 55%）
    # Seedream 路径会在 sanitize 3 次失败后自动降级到 NB2，保证 Pipeline 不断
    IMAGE_GEN_PROVIDER: str = "seedream"

    # 火山方舟 Ark API Key（Seedream 5.0-lite 调用鉴权）
    # 仅当 IMAGE_GEN_PROVIDER=seedream 时必需
    ARK_API_KEY: str = ""

    # 单次 Pipeline 成本上限（美元），超过时中止并抛 PipelineCostLimitExceeded
    PIPELINE_COST_LIMIT: float = 10.0

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


if not settings.DATABASE_URL:
    if all([
        settings.MYSQL_HOST,
        settings.MYSQL_USER,
        settings.MYSQL_DATABASE,
    ]):
        settings.DATABASE_URL = (
            "mysql+asyncmy://"
            f"{quote_plus(settings.MYSQL_USER)}:{quote_plus(settings.MYSQL_PASSWORD)}"
            f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
            "?charset=utf8mb4"
        )
    else:
        raise ValueError(
            "DATABASE_URL or MYSQL_* must be configured. "
            "SQLite/local file storage is not allowed for this backend."
        )

if not settings.DATABASE_URL.startswith(("mysql+asyncmy://", "mysql+aiomysql://")):
    raise ValueError(
        "Only MySQL is supported for backend storage. "
        "Please configure DATABASE_URL with a mysql+asyncmy or mysql+aiomysql URL."
    )
