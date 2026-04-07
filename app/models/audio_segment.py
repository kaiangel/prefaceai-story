"""Audio segment model for fine-grained timeline management"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, Index
from app.database import Base


class AudioSegment(Base):
    """
    音频段落模型

    用于存储Whisper返回的时间戳信息和图片匹配结果
    """
    __tablename__ = "chapter_audio_segments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    chapter_id = Column(Integer, nullable=False)
    segment_index = Column(Integer, nullable=False)

    # 时间信息
    text = Column(Text, nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)

    # 匹配信息
    matched_scene_id = Column(Integer, nullable=True)
    matched_image_path = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index('idx_chapter_audio_segments_chapter', 'chapter_id'),
    )
