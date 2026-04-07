"""Generation job model"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class GenerationJob(Base):
    __tablename__ = "chapter_generation_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    chapter_id = Column(Integer, nullable=False)
    status = Column(String(32), default="queued")  # queued/processing/completed/failed
    current_stage = Column(String(64), nullable=True)  # story_generation/storyboard/image_generation/tts/whisper/composition
    progress = Column(Integer, default=0)  # 0-100
    estimated_seconds = Column(Integer, nullable=True)
    stage_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
