"""Project schemas"""

from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


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
    # B33: 用户在 Stage A 选择的情绪基调（大纲生成前确定，最高优先级）
    user_selected_mood: Optional[Literal["温馨", "紧张", "幽默", "感人", "治愈", "热血", "悬疑", "浪漫"]] = Field(
        default=None,
        description="用户在 Stage A 选择的情绪基调，注入 Stage 1 LLM prompt"
    )


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
    created_at: str   # ISO 8601 with timezone, e.g. "2026-04-28T15:38:00Z"
    updated_at: str   # ISO 8601 with timezone, e.g. "2026-04-28T15:38:00Z"
    confirmed_outline: dict[str, Any] | None = None  # 用户确认后的大纲（含 summary/mood/user_selected_mood/music_hint/plot_points）
    raw_outline: dict[str, Any] | None = None         # Stage 1 LLM 原始输出（pre-confirm 状态，供前端 hydrate 用）
    aspect_ratio: str | None = None                   # 画面比例 "2:3" / "16:9" 等
    # R7-1: Dashboard 列表扩展字段（Wave 2 Agent D）
    cover_image_url: str | None = None   # storyboard shots[0].image_url（/static/... 路径，前端 toAbsoluteUrl 转绝对 URL）
    shot_count: int = 0                  # storyboard shots 数组长度
    mood: str | None = None              # confirmed_outline.user_selected_mood ?? confirmed_outline.mood ?? None
    # R7-2: 点赞
    is_favorite: bool = False            # 用户点赞状态（null 老数据视为 False）
    # B33: Stage A 用户选 mood（最高优先级，直接来自 projects.user_selected_mood 列）
    user_selected_mood: str | None = None
    # B49: 角色是否已确认（前端 createUrl 判断是否应跳转到 /scenes）
    characters_confirmed: bool = False
    # B58 / R4-2: 场景是否已确认（前端 createUrl 判断是否应跳转到 /generating；后端 R4-2 wait loop 闸门）
    scenes_confirmed: bool = False

    class Config:
        from_attributes = True
