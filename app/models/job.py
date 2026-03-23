"""Generation job model"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id"), nullable=False)
    status = Column(String(32), default="queued")  # queued/processing/completed/failed
    current_stage = Column(String(64), nullable=True)  # story_generation/storyboard/image_generation/tts/whisper/composition
    progress = Column(Integer, default=0)  # 0-100
    estimated_seconds = Column(Integer, nullable=True)
    stage_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    chapter = relationship("Chapter", back_populates="jobs")
