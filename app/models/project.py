"""Project model"""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey("u_users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    original_idea = Column(Text, nullable=False)
    style_preset = Column(String(64), nullable=False)
    total_chapters = Column(Integer, default=1)
    chapter_duration_minutes = Column(Integer, default=3)
    character_count = Column(Integer, default=2)
    language = Column(String(32), default="zh-CN")
    voice_preset = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
