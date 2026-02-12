"""Chapter schemas"""

from datetime import datetime
from pydantic import BaseModel
from typing import Any


class ChapterStatus(BaseModel):
    """Chapter generation status"""

    status: str
    stage: str | None
    progress: int
    estimated_remaining_seconds: int | None
    message: str | None


class ChapterResponse(BaseModel):
    """Basic chapter information"""

    id: str
    project_id: str
    chapter_number: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SceneInfo(BaseModel):
    """Scene information from generated story"""

    scene_id: int
    location: str
    time: str
    mood: str
    visual_description: str
    narration: str
    duration_hint: str | int


class CharacterInfo(BaseModel):
    """Character information from generated story"""

    name: str
    description: str
    personality: str


class ChapterStory(BaseModel):
    """Full story content for a chapter"""

    title: str
    summary: str
    full_script: dict[str, Any]
    scenes: list[SceneInfo]
    characters: list[CharacterInfo]
