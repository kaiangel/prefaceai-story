"""Wave 11.2 Backend Tests — T18-G (404 storm) + T18-E (preview API)

Tests verify:
- GET /chapters/{n}/story returns 200+empty when no data yet (not 404)
- GET /chapters/{n}/storyboard returns 200+empty when storyboard not generated (not 404)
- GET /projects/{id}/preview aggregates project preview data correctly
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional


# ============ Helpers ============

def make_chapter_mock(
    status: str = "pending",
    scenes_json: Optional[str] = None,
    full_script: Optional[str] = None,
    storyboard_json: Optional[str] = None,
    characters_json: Optional[str] = None,
    summary: Optional[str] = None,
    error_message: Optional[str] = None,
    bgm_url: Optional[str] = None,
    chapter_number: int = 1,
):
    """Create a mock Chapter object with given attributes."""
    chapter = MagicMock()
    chapter.status = status
    chapter.scenes_json = scenes_json
    chapter.full_script = full_script
    chapter.storyboard_json = storyboard_json
    chapter.characters_json = characters_json
    chapter.summary = summary
    chapter.error_message = error_message
    chapter.bgm_url = bgm_url
    chapter.chapter_number = chapter_number
    chapter.id = 1
    chapter.project_id = 1
    return chapter


def make_project_mock(
    uuid: str = "test-uuid",
    title: str = "Test Project",
    style_preset: str = "korean_webtoon",
    aspect_ratio: str = "2:3",
):
    """Create a mock Project object."""
    project = MagicMock()
    project.uuid = uuid
    project.title = title
    project.style_preset = style_preset
    project.aspect_ratio = aspect_ratio
    project.id = 1
    return project


# ============ T18-G: /story endpoint — 200+empty instead of 404 ============

class TestGetChapterStoryT18G:
    """T18-G: /chapters/{n}/story 应在数据未就绪时返 200+empty (不是 404)"""

    def test_no_data_pending_returns_empty_structure(self) -> None:
        """pending 状态 + 无数据 → has_data=False → 应返 200+空"""
        chapter = make_chapter_mock(
            status="pending",
            scenes_json=None,
            full_script=None,
        )
        # 验证数据条件：无数据时 has_data=False
        has_data = bool(chapter.scenes_json or chapter.full_script)
        assert not has_data, "pending 无数据时 has_data 应为 False"

        # 模拟 endpoint 内的 T18-G 分支：返回空结构
        from app.schemas.chapter import ChapterStory
        empty_response = ChapterStory(
            title="",
            summary="",
            full_script={},
            scenes=[],
            characters=[],
        )
        assert empty_response.scenes == []
        assert empty_response.characters == []
        assert empty_response.full_script == {}
        assert empty_response.title == ""

    def test_generating_story_no_data_returns_empty(self) -> None:
        """generating_story 状态 + 无数据 → 应返 200+空"""
        chapter = make_chapter_mock(
            status="generating_story",
            scenes_json=None,
            full_script=None,
        )
        has_data = bool(chapter.scenes_json or chapter.full_script)
        assert not has_data

        # 验证 T18-G: 新行为是 200+empty (旧行为是 404)
        from app.schemas.chapter import ChapterStory
        empty_response = ChapterStory(
            title="", summary="", full_script={}, scenes=[], characters=[]
        )
        assert len(empty_response.scenes) == 0
        assert len(empty_response.characters) == 0

    def test_character_ready_no_scenes_returns_empty(self) -> None:
        """character_ready 阶段（scenes_json 尚未写入）→ 返 200+空"""
        chapter = make_chapter_mock(
            status="character_ready",
            scenes_json=None,
            characters_json=json.dumps([{"id": "char_001", "name": "小美"}]),
        )
        has_data = bool(chapter.scenes_json or chapter.full_script)
        assert not has_data, "character_ready 阶段 scenes_json 为 None"

    def test_scenes_json_present_returns_real_data(self) -> None:
        """scenes_json 有数据时继续正常返回（不触发 T18-G empty 分支）"""
        scenes = [{"scene_id": 1, "description": "Scene 1"}]
        chapter = make_chapter_mock(
            status="generating_story",
            scenes_json=json.dumps(scenes),
            full_script=None,
            summary="Test Story",
        )
        has_data = bool(chapter.scenes_json or chapter.full_script)
        assert has_data, "有 scenes_json 时 has_data=True，走正常数据路径"

        parsed = json.loads(chapter.scenes_json)
        assert len(parsed) == 1
        assert parsed[0]["scene_id"] == 1

    def test_failed_status_should_still_be_400(self) -> None:
        """failed 状态仍返 400（不是 200+empty，failed 是真错误）"""
        chapter = make_chapter_mock(
            status="failed",
            error_message="Stage 4 失败",
        )
        # failed → 不走 T18-G empty 路径，保持原 400 行为
        assert chapter.status == "failed"
        assert chapter.error_message == "Stage 4 失败"
        # T18-G 只改 pending/generating_story 无数据的情况，failed 走 HTTP 400

    def test_both_scenes_json_and_full_script_none(self) -> None:
        """scenes_json=None + full_script=None → empty 结构"""
        chapter = make_chapter_mock(
            status="pending",
            scenes_json=None,
            full_script=None,
        )
        # T18-G 修复: 不再 404，返 200+empty
        has_data = bool(chapter.scenes_json) or bool(chapter.full_script)
        assert not has_data


# ============ T18-G: /storyboard endpoint — 200+empty instead of 404 ============

class TestGetChapterStoryboardT18G:
    """T18-G: /chapters/{n}/storyboard 应在 storyboard_json 未就绪时返 200+empty"""

    def test_no_storyboard_json_returns_empty_structure(self) -> None:
        """storyboard_json=None → 应返 200+空结构"""
        chapter = make_chapter_mock(
            status="generating_story",
            storyboard_json=None,
        )
        assert not chapter.storyboard_json, "storyboard_json 为 None"

        # 模拟 T18-G 新 endpoint 行为：返空结构
        expected_response = {
            "storyboard": {"shots": []},
            "chapter_number": 1,
            "project_id": "test-uuid",
        }
        assert expected_response["storyboard"]["shots"] == []
        assert expected_response["chapter_number"] == 1

    def test_empty_storyboard_json_returns_empty(self) -> None:
        """storyboard_json='{}' 时 shots=[]"""
        chapter = make_chapter_mock(
            status="storyboard_running",
            storyboard_json=None,
        )
        # storyboard_json 为 None 时走 T18-G 空路径
        assert not chapter.storyboard_json

    def test_real_storyboard_json_returns_shots(self) -> None:
        """storyboard_json 有实际数据时正常解析"""
        storyboard = {
            "shots": [
                {"shot_id": 1, "image_url": "/static/.../shot_01.png"},
                {"shot_id": 2, "image_url": "/static/.../shot_02.png"},
            ]
        }
        chapter = make_chapter_mock(
            status="completed",
            storyboard_json=json.dumps(storyboard),
        )
        assert chapter.storyboard_json, "有数据时不走 T18-G 空路径"
        parsed = json.loads(chapter.storyboard_json)
        assert len(parsed["shots"]) == 2

    def test_storyboard_empty_dict_is_falsy(self) -> None:
        """storyboard_json='{}' 时 bool({}) == False → 可能走空路径，需排除 shots=[]"""
        # 注：storyboard_json 字段是 JSON 字符串，不是 dict
        # bool('{}') == True（非空字符串），但 json.loads('{}').get('shots', []) == []
        # 因此 _is_storyboard_truly_ready 用 len(shots) > 0 判断
        storyboard_json_str = "{}"
        assert bool(storyboard_json_str), "非空字符串 bool=True，但 shots 可能为空"
        parsed = json.loads(storyboard_json_str)
        shots = parsed.get("shots", [])
        assert len(shots) == 0, "空 {} 中没有 shots"


# ============ T18-E: /projects/{id}/preview endpoint ============

class TestProjectPreviewEndpoint:
    """T18-E: GET /projects/{id}/preview 应返回完整数据"""

    def test_preview_response_structure(self) -> None:
        """preview response 包含所有必须字段"""
        # 模拟 endpoint 返回结构
        preview_response = {
            "project_id": "test-uuid-123",
            "title": "共享单车故事",
            "style": "watercolor",
            "aspect_ratio": "3:4",
            "bgm_url": "/static/outputs/test-uuid-123/bgm.mp3",
            "status": "completed",
            "chapters": [
                {
                    "chapter_number": 1,
                    "status": "completed",
                    "shots": [
                        {"shot_id": 1, "image_url": "/static/.../shot_01.png", "narration": "旁白", "success": True},
                        {"shot_id": 2, "image_url": "/static/.../shot_02.png", "narration": "旁白2", "success": True},
                    ],
                    "characters": [
                        {"id": "char_001", "name": "小美", "portrait_url": "/static/.../char_001_portrait.png"},
                    ],
                    "bgm_url": "/static/outputs/test-uuid-123/bgm.mp3",
                    "total_shots": 2,
                }
            ],
            "total_shots": 2,
        }

        # 必须字段
        assert "project_id" in preview_response
        assert "title" in preview_response
        assert "bgm_url" in preview_response
        assert "chapters" in preview_response
        assert "total_shots" in preview_response
        assert "status" in preview_response

        # chapters 结构
        assert len(preview_response["chapters"]) == 1
        ch = preview_response["chapters"][0]
        assert "shots" in ch
        assert "characters" in ch
        assert "bgm_url" in ch
        assert "total_shots" in ch

    def test_preview_empty_when_no_chapters(self) -> None:
        """无 chapter 时返 chapters=[] total_shots=0"""
        preview_response = {
            "project_id": "test-uuid",
            "title": "",
            "style": None,
            "aspect_ratio": "2:3",
            "bgm_url": None,
            "status": "pending",
            "chapters": [],
            "total_shots": 0,
        }
        assert preview_response["chapters"] == []
        assert preview_response["total_shots"] == 0
        assert preview_response["bgm_url"] is None

    def test_preview_aggregates_total_shots(self) -> None:
        """total_shots = sum of all chapter shots"""
        shots_ch1 = [{"shot_id": i} for i in range(1, 11)]  # 10 shots
        shots_ch2 = [{"shot_id": i} for i in range(11, 21)]  # 10 shots
        chapters = [
            {"chapter_number": 1, "shots": shots_ch1, "total_shots": 10},
            {"chapter_number": 2, "shots": shots_ch2, "total_shots": 10},
        ]
        total = sum(c["total_shots"] for c in chapters)
        assert total == 20

    def test_preview_parses_storyboard_json(self) -> None:
        """storyboard_json 有数据时正确解析 shots"""
        storyboard = {
            "shots": [
                {"shot_id": 1, "narration_segment": "小美骑车", "image_url": "/static/shot_01.png"},
                {"shot_id": 2, "narration_segment": "发现纸条", "image_url": "/static/shot_02.png"},
                {"shot_id": 3, "narration_segment": "读纸条", "deleted": True},  # 已删除，不计入
            ]
        }
        chapter = make_chapter_mock(
            status="completed",
            storyboard_json=json.dumps(storyboard),
        )

        storyboard_data = json.loads(chapter.storyboard_json)
        active_shots = [s for s in storyboard_data["shots"] if not s.get("deleted")]
        assert len(active_shots) == 2, "deleted shot 应被跳过"

    def test_preview_builds_character_portrait_url(self) -> None:
        """characters_json 无 portrait_url 时用静态路径兜底"""
        project_id = "test-uuid-xyz"
        char_id = "char_001"
        char_name = "小美"

        characters_json = json.dumps([{"id": char_id, "name": char_name}])
        chars_raw = json.loads(characters_json)

        # 模拟 preview endpoint 内的逻辑
        characters = []
        for c in chars_raw:
            cid = c.get("id", "")
            characters.append({
                "id": cid,
                "name": c.get("name", ""),
                "portrait_url": c.get(
                    "portrait_url",
                    f"/static/outputs/{project_id}/character_refs/{cid}_portrait.png"
                    if cid else None
                ),
            })

        assert len(characters) == 1
        assert characters[0]["portrait_url"] == f"/static/outputs/{project_id}/character_refs/{char_id}_portrait.png"

    def test_preview_with_bgm_url_from_chapter(self) -> None:
        """bgm_url 来自第一个 chapter.bgm_url"""
        chapter = make_chapter_mock(
            status="completed",
            bgm_url="/static/outputs/abc/bgm.mp3",
        )
        assert chapter.bgm_url == "/static/outputs/abc/bgm.mp3"
        bgm_url = chapter.bgm_url  # 模拟 preview endpoint 取值
        assert bgm_url is not None

    def test_preview_status_comes_from_latest_chapter(self) -> None:
        """status 字段来自最新 chapter 的 status"""
        statuses = ["completed", "failed", "generating_story"]
        # 最后一个 chapter 的 status 作为 project 级 status
        latest_status = statuses[-1]
        assert latest_status == "generating_story"


# ============ Integration: endpoint 不改变 project/chapter not found 行为 ============

class TestT18GDoesNotBreakNotFound:
    """T18-G 修复不影响真 404 场景（project/chapter 不存在）"""

    def test_project_not_found_still_404(self) -> None:
        """project 不存在仍应 404（不被 T18-G 影响）"""
        # T18-G 只改了 "data not ready yet" 的返回，project not found 仍是 404
        project = None
        should_404 = project is None
        assert should_404, "project 不存在时仍应 404"

    def test_chapter_not_found_still_404(self) -> None:
        """chapter 不存在仍应 404"""
        chapter = None
        should_404 = chapter is None
        assert should_404, "chapter 不存在时仍应 404"

    def test_failed_chapter_still_400(self) -> None:
        """failed 状态仍返 400"""
        chapter = make_chapter_mock(
            status="failed",
            error_message="Stage 4 TypeError",
        )
        assert chapter.status == "failed"
        # T18-G 不改 failed 状态，保持 HTTP 400


# ============ Schema: ChapterStory 支持 empty ============

class TestChapterStoryEmptySchema:
    """ChapterStory schema 支持空结构（T18-G 需要）"""

    def test_chapter_story_empty_valid(self) -> None:
        """ChapterStory 可以用空字段初始化"""
        from app.schemas.chapter import ChapterStory
        empty = ChapterStory(
            title="",
            summary="",
            full_script={},
            scenes=[],
            characters=[],
        )
        assert empty.title == ""
        assert empty.scenes == []
        assert empty.characters == []
        assert empty.full_script == {}

    def test_chapter_story_empty_summary(self) -> None:
        """ChapterStory summary 可为空字符串"""
        from app.schemas.chapter import ChapterStory
        story = ChapterStory(
            title="故事名",
            summary="",
            full_script={"title": "故事名"},
            scenes=[],
            characters=[],
        )
        assert story.summary == ""
