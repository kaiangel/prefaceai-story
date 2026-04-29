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


class ChapterStory(BaseModel):
    """Full story content for a chapter.

    scenes and characters are raw dicts from the pipeline output.
    Stage 3 ScreenplayWriter produces scenes with fields like scene_id,
    scene_heading, time_of_day, atmosphere, etc. — not the old
    location/time/mood/visual_description naming. Using Dict[str, Any]
    avoids schema validation errors from field-name mismatch.
    Frontend adapts field names directly from the raw pipeline output.
    """

    title: str
    summary: str
    full_script: dict[str, Any]
    scenes: list[dict[str, Any]]
    characters: list[dict[str, Any]]
