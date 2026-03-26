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
    aspect_ratio = Column(String(16), default="2:3")
    raw_outline_json = Column(Text, nullable=True)        # LLM 返回的原始大纲 JSON
    confirmed_outline_json = Column(Text, nullable=True)   # 用户确认后的最终大纲 JSON
    custom_style_analysis_json = Column(Text, nullable=True)       # 自定义风格分析结果
    character_refs_analysis_json = Column(Text, nullable=True)     # 角色参考图分析结果
    scene_refs_analysis_json = Column(Text, nullable=True)         # 场景参考图分析结果
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
