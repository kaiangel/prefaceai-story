"""Project model"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Text
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    user_id = Column(Integer, nullable=False)
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
