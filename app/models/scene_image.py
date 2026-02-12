"""Scene Image model for storing generated images"""

from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class SceneImage(Base):
    """
    场景图像表

    存储每个场景生成的图像信息
    一个场景可能有多个版本（重新生成时）
    """
    __tablename__ = "scene_images"

    id = Column(String, primary_key=True)
    chapter_id = Column(String, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(Integer, nullable=False)

    # Prompt信息
    image_prompt = Column(Text, nullable=False)  # 生成时使用的完整prompt
    character_prompts = Column(Text)  # 角色描述prompt（JSON）
    style_prompt = Column(Text)  # 风格prompt
    negative_prompt = Column(Text)  # 负面提示词

    # 存储路径
    image_path = Column(String, nullable=False)  # 本地存储路径
    image_url = Column(String)  # CDN/OSS URL（未来使用）
    thumbnail_path = Column(String)  # 缩略图路径

    # 图像属性
    width = Column(Integer, default=1024)
    height = Column(Integer, default=1024)
    aspect_ratio = Column(String, default="16:9")

    # 生成信息
    generation_model = Column(String)  # 使用的模型
    generation_params = Column(Text)  # 生成参数（JSON）
    generation_time_seconds = Column(Integer)  # 生成耗时

    # 状态
    is_active = Column(Boolean, default=True)  # 是否为当前使用版本
    retry_count = Column(Integer, default=0)  # 重试次数
    error_message = Column(Text)  # 错误信息

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())


class CharacterReference(Base):
    """
    角色参考图表

    存储用于保持角色一致性的参考图
    """
    __tablename__ = "character_references"

    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    character_name = Column(String, nullable=False)

    # 图像信息
    image_path = Column(String, nullable=False)
    image_url = Column(String)
    width = Column(Integer)
    height = Column(Integer)

    # 生成信息
    prompt_used = Column(Text)  # 生成时使用的prompt
    generation_model = Column(String)

    # 状态
    is_active = Column(Boolean, default=True)

    # 时间戳
    created_at = Column(DateTime, server_default=func.now())
