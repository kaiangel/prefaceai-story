"""Chapter model"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    status = Column(String, default="pending")  # pending/generating_story/generating_images/generating_audio/compositing/completed/failed
    full_script = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    characters_json = Column(Text, nullable=True)
    scenes_json = Column(Text, nullable=True)
    storyboard_json = Column(Text, nullable=True)
    video_url = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)

    # Phase 3: Audio fields
    audio_url = Column(String, nullable=True)
    audio_path = Column(String, nullable=True)
    audio_duration_seconds = Column(Float, nullable=True)
    transcript_json = Column(Text, nullable=True)  # Whisper返回的完整转录
    timeline_json = Column(Text, nullable=True)    # 音画对齐结果
    voice_preset = Column(String, nullable=True)   # 使用的音色
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="chapters")
    jobs = relationship("GenerationJob", back_populates="chapter", cascade="all, delete-orphan")
