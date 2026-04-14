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
    video_url = Column(String(500), nullable=True)
    error_message = Column(LONGTEXT, nullable=True)

    # Phase 3: Audio fields
    audio_url = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    transcript_json = Column(LONGTEXT, nullable=True)  # Whisper返回的完整转录
    timeline_json = Column(LONGTEXT, nullable=True)    # 音画对齐结果
    voice_preset = Column(String(128), nullable=True)   # 使用的音色
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
