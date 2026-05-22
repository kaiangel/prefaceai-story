"""Chapter model"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from app.database import Base


class Chapter(Base):
    __tablename__ = "project_chapters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    project_id = Column(Integer, nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status = Column(String(64), default="pending")  # pending/generating_story/generating_images/generating_audio/compositing/completed/failed
    full_script = Column(LONGTEXT, nullable=True)
    summary = Column(LONGTEXT, nullable=True)
    characters_json = Column(LONGTEXT, nullable=True)
    scenes_json = Column(LONGTEXT, nullable=True)
    storyboard_json = Column(LONGTEXT, nullable=True)
    # T21-NEW-7 (2026-05-21 DEC-047): Stage 4.5 scene_image_preparation 输出
    # JSON 结构: [{location_id, location_zh, interior_url, exterior_url, description_zh, atmosphere, time_of_day, lighting_condition}]
    # 前端 /scenes 页面真预览 + 重生 + 60s 倒计时 (镜像 characters 页面对偶设计)
    scene_references_json = Column(LONGTEXT, nullable=True)
    video_url = Column(String(500), nullable=True)
    error_message = Column(LONGTEXT, nullable=True)

    # Phase 3: Audio fields
    audio_url = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    transcript_json = Column(LONGTEXT, nullable=True)  # Whisper返回的完整转录
    timeline_json = Column(LONGTEXT, nullable=True)    # 音画对齐结果
    voice_preset = Column(String(128), nullable=True)   # 使用的音色

    # Wave 2: BGM fields (alembic migration: 001_add_bgm_fields_to_chapters)
    bgm_url = Column(String(500), nullable=True)           # BGM 文件 URL / 本地路径
    bgm_volume = Column(Float, default=1.0, nullable=True)  # 用户调节的音量系数（0.0-1.0）
    bgm_meta_version = Column(String(50), nullable=True)   # meta-prompt 版本（"mixed" / "en"）
    credits_used = Column(Integer, default=0, nullable=True)  # 本次 BGM 生成消耗积分（mock）

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
