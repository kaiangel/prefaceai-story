"""Project schemas"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal


StylePreset = Literal[
    "realistic",
    "illustration",
    "cyberpunk",
    "ink",
    "cartoon",
    "manga",
    "oil_painting",
    "watercolor",
    "pixel",
    "pixar_3d",
    "ghibli",
    "anime",
    "slam_dunk",
    "korean_webtoon",
    "children_book",
    # 新增 13 个
    "ukiyo_e",
    "vintage_film",
    "pencil_sketch",
    "chibi",
    "dark_fantasy",
    "pop_art",
    "paper_cut",
    "steampunk",
    "art_nouveau",
    "noir",
    "comic_western",
    "pastel_dream",
    "gothic",
]


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    original_idea: str = Field(default="", max_length=2000, description="用户原始创意")
    style_preset: StylePreset = Field(default="realistic", description="画面风格")
    total_chapters: int = Field(default=1, ge=1, le=10, description="总章节数")
    chapter_duration_minutes: int = Field(default=3, ge=1, le=10, description="每章时长（分钟）")
    character_count: int = Field(default=2, ge=1, le=6, description="角色数量")
    language: str = Field(default="zh-CN", description="语言")
    voice_preset: str | None = Field(default=None, description="TTS音色ID")
    aspect_ratio: str = Field(default="2:3", description="画面比例")
    document_text: str | None = Field(default=None, description="上传文档的解析文本")
    custom_style_analysis: dict | None = Field(default=None, description="自定义风格分析结果")
    character_refs_analysis: list[dict] | None = Field(default=None, description="角色参考图分析结果")
    scene_refs_analysis: list[dict] | None = Field(default=None, description="场景参考图分析结果")


class ProjectResponse(BaseModel):
    """Response after creating a project"""

    project_id: str
    chapter_id: str
    job_id: str
    status: str
    message: str


class ProjectDetail(BaseModel):
    """Detailed project information"""

    id: str
    user_id: int
    title: str
    original_idea: str
    style_preset: str
    total_chapters: int
    chapter_duration_minutes: int
    character_count: int
    language: str
    voice_preset: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
