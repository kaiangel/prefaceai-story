"""
RISK-T15-14: Unit tests for storyboard_director post-process schema fix.

Scenario: Stage 4 LLM returns shots with missing top-level fields
  (characters_in_scene=None / shot_type=None / camera_angle=None).
After _validate_storyboard(), these fields MUST be populated via fallback.

Run:
  pytest tests/test_storyboard_director_schema_fix.py -v
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

from app.services.storyboard_director import StoryboardDirector


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_shot(
    shot_id: int = 1,
    scene_id: int = 1,
    image_prompt: str = "Test prompt.",
    shot_type: object = None,  # None simulates missing field
    camera_angle: object = None,
    characters_in_scene: object = None,
    camera: dict = None,
    characters_visible: list = None,
) -> dict:
    """Build a minimal shot dict mimicking LLM output with possible missing fields."""
    shot = {
        "shot_id": shot_id,
        "scene_id": scene_id,
        "image_prompt": image_prompt,
        "narration_segment": "旁白文字",
        "camera": camera or {
            "shot_size": "medium_close_up",
            "angle": "high_angle",
            "movement": "static",
        },
        "composition": {"subject_position": "center"},
        "lighting": {"key_light": "overhead fluorescent", "mood": "clinical"},
        "character_direction": {
            "characters_visible": characters_visible if characters_visible is not None else ["char_001"]
        },
        "estimated_duration": 8.0,
        "text_overlay": {"text_type": "thought", "chinese_text": "（测试）", "speaker_position": "bottom"},
    }
    # Only inject keys when explicitly provided (None means the LLM omitted the key entirely)
    if shot_type is not None:
        shot["shot_type"] = shot_type
    if camera_angle is not None:
        shot["camera_angle"] = camera_angle
    if characters_in_scene is not None:
        shot["characters_in_scene"] = characters_in_scene
    return shot


def _minimal_storyboard(shots: list) -> dict:
    return {
        "global_visual_direction": {
            "style_enforcement": "realistic_cinematic",
            "aspect_ratio": "2:3",
        },
        "shots": shots,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPostProcessSchemaFix:
    """Verify _validate_storyboard fallback for missing shot_type / camera_angle / characters_in_scene."""

    def setup_method(self):
        self.director = StoryboardDirector()

    def _run(self, storyboard: dict, characters: dict = None) -> list:
        """Run _validate_storyboard and return the processed shots."""
        self.director._validate_storyboard(storyboard, characters=characters or {"characters": []})
        return storyboard["shots"]

    # --- shot_type fallback ---

    def test_shot_type_filled_from_camera_shot_size(self):
        """shot_type missing → derived from camera.shot_size."""
        shot = _make_shot(
            camera={"shot_size": "medium_close_up", "angle": "high_angle"},
            # shot_type intentionally absent
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["shot_type"] == "medium close-up", (
            f"Expected 'medium close-up', got '{shots[0]['shot_type']}'"
        )

    def test_shot_type_not_overwritten_if_present(self):
        """shot_type already set → must NOT be overwritten."""
        shot = _make_shot(
            shot_type="close-up",
            camera={"shot_size": "medium_shot", "angle": "eye_level"},
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["shot_type"] == "close-up"

    def test_shot_type_wide_shot_mapping(self):
        shot = _make_shot(camera={"shot_size": "wide_shot", "angle": "eye_level"})
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["shot_type"] == "wide shot"

    def test_shot_type_establishing_mapping(self):
        shot = _make_shot(camera={"shot_size": "establishing", "angle": "eye_level"})
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["shot_type"] == "establishing shot"

    # --- camera_angle fallback ---

    def test_camera_angle_filled_from_camera_angle(self):
        """camera_angle missing → derived from camera.angle."""
        shot = _make_shot(
            camera={"shot_size": "medium_shot", "angle": "low_angle"},
            # camera_angle intentionally absent
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["camera_angle"] == "low angle"

    def test_camera_angle_eye_level_default(self):
        shot = _make_shot(camera={"shot_size": "medium_shot", "angle": "eye_level"})
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["camera_angle"] == "eye level"

    def test_camera_angle_not_overwritten_if_present(self):
        shot = _make_shot(
            camera_angle="high angle",
            camera={"shot_size": "medium_shot", "angle": "eye_level"},
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["camera_angle"] == "high angle"

    # --- characters_in_scene fallback ---

    def test_characters_in_scene_filled_from_characters_visible(self):
        """characters_in_scene missing → derived from character_direction.characters_visible."""
        shot = _make_shot(
            characters_visible=["char_001", "char_003"],
            # characters_in_scene intentionally absent
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["characters_in_scene"] == ["char_001", "char_003"]

    def test_characters_in_scene_empty_list_when_visible_empty(self):
        """characters_in_scene missing and characters_visible empty → []."""
        shot = _make_shot(characters_visible=[])
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["characters_in_scene"] == []

    def test_characters_in_scene_not_overwritten_if_present(self):
        """characters_in_scene already set (including explicit []) → not overwritten."""
        shot = _make_shot(
            characters_in_scene=["char_002"],
            characters_visible=["char_001"],  # different — must NOT override
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["characters_in_scene"] == ["char_002"]

    def test_characters_in_scene_explicit_empty_list_preserved(self):
        """characters_in_scene=[] explicitly set (e.g. establishing shot) → preserved as []."""
        shot = _make_shot(
            characters_in_scene=[],
            characters_visible=["char_001"],  # visible but in_scene explicitly empty
        )
        shots = self._run(_minimal_storyboard([shot]))
        assert shots[0]["characters_in_scene"] == []

    # --- Full scenario: all three missing (mirrors Shot 21/22 from test15) ---

    def test_all_three_missing_shot21_scenario(self):
        """Regression: Shot 21 / Shot 22 pattern — all three fields missing → all filled."""
        shot21 = _make_shot(
            shot_id=21,
            scene_id=11,
            image_prompt=(
                "High-angle medium-wide shot looking down at Lin Xiaoyue standing alone "
                "in the centre of the ICU corridor. EXACTLY 1 character visible."
            ),
            camera={"shot_size": "medium_wide", "angle": "high_angle"},
            characters_visible=["char_001"],
            # shot_type, camera_angle, characters_in_scene all absent (None)
        )
        shot22 = _make_shot(
            shot_id=22,
            scene_id=11,
            image_prompt=(
                "Eye-level medium close-up shot. Lin Xiaoyue at left third, Chen Guodong through glass. "
                "EXACTLY 2 characters visible."
            ),
            camera={"shot_size": "medium_close_up", "angle": "eye_level"},
            characters_visible=["char_001", "char_003"],
        )
        shots = self._run(_minimal_storyboard([shot21, shot22]))

        # shot 21
        assert shots[0]["shot_type"] == "medium wide shot", shots[0]["shot_type"]
        assert shots[0]["camera_angle"] == "high angle", shots[0]["camera_angle"]
        assert shots[0]["characters_in_scene"] == ["char_001"], shots[0]["characters_in_scene"]

        # shot 22
        assert shots[1]["shot_type"] == "medium close-up", shots[1]["shot_type"]
        assert shots[1]["camera_angle"] == "eye level", shots[1]["camera_angle"]
        assert shots[1]["characters_in_scene"] == ["char_001", "char_003"], shots[1]["characters_in_scene"]

    def test_multiple_shots_mixed(self):
        """Multi-shot storyboard: some shots have fields, some don't."""
        shot_with = _make_shot(
            shot_id=1,
            shot_type="close-up",
            camera_angle="low angle",
            characters_in_scene=["char_002"],
            camera={"shot_size": "wide_shot", "angle": "high_angle"},
            characters_visible=["char_001"],
        )
        shot_without = _make_shot(
            shot_id=2,
            camera={"shot_size": "close_up", "angle": "dutch_angle"},
            characters_visible=["char_003"],
        )
        shots = self._run(_minimal_storyboard([shot_with, shot_without]))

        # Shot 1: pre-existing values preserved
        assert shots[0]["shot_type"] == "close-up"
        assert shots[0]["camera_angle"] == "low angle"
        assert shots[0]["characters_in_scene"] == ["char_002"]

        # Shot 2: derived from camera fields
        assert shots[1]["shot_type"] == "close-up"
        assert shots[1]["camera_angle"] == "dutch angle"
        assert shots[1]["characters_in_scene"] == ["char_003"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
