"""Database models and data types"""

from app.models.user import User
from app.models.contact_us import ContactUs
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.job import GenerationJob
from app.models.scene_image import SceneImage, CharacterReference
from app.models.audio_segment import AudioSegment

# 角色类型系统
from app.models.character_types import (
    CharacterType,
    HumanAppearance,
    AnimalAppearance,
    FantasyCreatureAppearance,
    RobotAppearance,
    Character,
)

# 风格配置系统
from app.models.style_config import (
    ProjectStyleConfig,
    StyleConfigBuilder,
)

__all__ = [
    "User",
    "ContactUs",
    "Project",
    "Chapter",
    "GenerationJob",
    "SceneImage",
    "CharacterReference",
    "AudioSegment",
    # 角色类型
    "CharacterType",
    "HumanAppearance",
    "AnimalAppearance",
    "FantasyCreatureAppearance",
    "RobotAppearance",
    "Character",
    # 风格配置
    "ProjectStyleConfig",
    "StyleConfigBuilder",
]
