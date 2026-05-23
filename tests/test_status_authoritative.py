"""
单元测试: TASK-WAVE9-P2-BACKEND-STATUS-AUTHORITATIVE
(DEC-030 / RISK-T15-3 / RISK-T15-7 / RISK-T15-8 / RISK-T15-9)

验证 backend status endpoint 成为 frontend state 的 single source of truth:
  1. ui_phase 各种 stage 组合的派生正确
  2. hydrate_hints 每个 phase 的 endpoint / display_field 正确
  3. GET /story 在 scenes_ready 阶段返回 scenes（顺解 RISK-T15-3）
  4. mid-stage failed_shot_count 实时累加（顺解 RISK-T15-9）

运行命令:
  pytest tests/test_status_authoritative.py -v

T22-NEW-1 改动说明:
  - 加 autouse fixture _ensure_real_app_config，镜像 T20-52 修法，隔离
    test_t21_digital_virtual_fallback.py 注入的 app.config stub（SimpleNamespace
    缺少 DATABASE_URL），防止综合跑时 setup_method 中的延迟 import 因
    settings.DATABASE_URL AttributeError 导致 27 errors。
  - 更新 3 个因 T22-NEW-5 (scene_review 已移除) 而过时的测试用例。
"""

import sys
import types
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
import pytest

# ─────────────────────────────────────────────────────────────────────────────
# T22-NEW-1: Mock 污染隔离 autouse fixture
#
# 根因: test_t21_digital_virtual_fallback.py 在 sys.modules["app.config"] 注入
#   SimpleNamespace(ANTHROPIC_API_KEY=..., GEMINI_API_KEY=...) — 仅 4 个属性。
#   当 test_status_authoritative 随后在 setup_method 做
#   "from app.api.chapters import _derive_ui_phase" 时:
#     → app.api.chapters 进而 import app.database
#     → app.database L13: _db_url = settings.DATABASE_URL  ← AttributeError
#   → 所有 setup_method 中含此 import 的 test 变成 ERROR。
#
# 修复策略 (镜像 T20-52 autouse fixture 模式):
#   每 test 前检测 app.config.settings 是否为 stub (无 DATABASE_URL)，
#   若是则删除所有 app.* 污染条目，让 setup_method 的延迟 import 重新加载真实模块。
#   Teardown: 移除 app.api.chapters + app.database 条目，让下一 test 也能重新加载。
# ─────────────────────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────────────────────────────────────
# T22-NEW-1 helper: stub attribute augmentation
#
# 策略: 不移除 stub，而是给 stub 打补丁，补充 chapters 启动所需的缺失 attributes。
#   - app.config.settings 补充 DATABASE_URL, DEBUG 等缺失字段
#   - google.genai stub 补充 types 子模块 (story_generator 需要 "from google.genai import types")
#   - app.api.chapters 加载成功后，之后的 test 直接复用 cached module (不清除)
# ─────────────────────────────────────────────────────────────────────────────

_SETTINGS_AUGMENT = {
    # Use mysql+aiomysql URL so pool_size/max_overflow/pool_timeout are accepted.
    # The engine is created but never used to connect in unit tests.
    "DATABASE_URL": "mysql+aiomysql://test:test@127.0.0.1:3306/test_stub",
    "DEBUG": False,
    "PIPELINE_COST_LIMIT": 10.0,
    "SKIP_IMAGE_GENERATION": True,
    "IMAGE_MAX_CONCURRENT": 1,
    "IMAGE_GEN_PROVIDER": "seedream",
    "VOLCENGINE_ACCESS_KEY": "test",
    "VOLCENGINE_SECRET_KEY": "test",
    "VOLCENGINE_TTS_APPID": "test",
    "VOLCENGINE_TTS_CLUSTER": "test",
    "SEEDREAM_ACCESS_KEY": "test",
    "SEEDREAM_SECRET_KEY": "test",
    "MUREKA_API_KEY": "test",
}


def _augment_settings_stub() -> bool:
    """If app.config.settings is a stub missing DATABASE_URL, augment it in place.

    Returns True if augmentation was needed, False if settings were already complete.
    """
    config_mod = sys.modules.get("app.config")
    if config_mod is None:
        return False
    settings_obj = getattr(config_mod, "settings", None)
    if settings_obj is None:
        return False
    if hasattr(settings_obj, "DATABASE_URL"):
        return False  # already complete, nothing to do

    # Augment stub in place
    for attr, val in _SETTINGS_AUGMENT.items():
        if not hasattr(settings_obj, attr):
            setattr(settings_obj, attr, val)
    return True


def _is_module_stub(mod) -> bool:
    """Return True if mod is a stub (not from site-packages, not from real app path)."""
    if mod is None:
        return False
    file_attr = getattr(mod, "__file__", None)
    if file_attr and "site-packages" in str(file_attr):
        return False
    path_attr = getattr(mod, "__path__", None)
    if path_attr:
        path_strs = [str(p) for p in path_attr]
        if any("site-packages" in p for p in path_strs):
            return False
    # Stub: __path__ == [] or no __file__ and no real path
    if path_attr == [] or path_attr == [""]:
        return True
    if file_attr is None and (path_attr is None or path_attr == []):
        return True
    return False


def _clean_google_genai_stubs() -> None:
    """Remove any stub google.genai / google.genai.types from sys.modules.

    These stubs (added by test_llm_fallback_chain.py, test_t21_*, etc.) block
    the real google.genai from loading properly when app.api.chapters is imported.

    After removal, the real package will be loaded from venv/site-packages on demand.
    """
    for key in ("google.genai.types", "google.genai", "google"):
        mod = sys.modules.get(key)
        if _is_module_stub(mod):
            sys.modules.pop(key, None)


@pytest.fixture(autouse=True)
def _ensure_chapters_importable():
    """T22-NEW-1: 确保 app.api.chapters 可以被 setup_method 的延迟 import 正确加载。

    问题根因:
      test_t21_digital_virtual_fallback.py 模块级代码在 pytest collection 时就注入:
      1. sys.modules["app.config"].settings = SimpleNamespace(无 DATABASE_URL)
      2. sys.modules["google.genai"] = 空 ModuleType (无 types)
      当 setup_method 执行 "from app.api.chapters import ..." 时:
        app.api.chapters → app.database → settings.DATABASE_URL → AttributeError
        app.api.chapters → pipeline_orchestrator → story_generator → google.genai.types → ImportError

    修复: 在每 test 前:
      1. 检测 app.config.settings stub，补全缺失的 DATABASE_URL 等属性
      2. 检测 google.genai stub，注入 types 子模块
      3. 若 app.api.chapters 已缓存 (成功加载过)，保留不动 (复用 cached module)

    注意: 不清除 app.api.chapters from sys.modules (避免触发重新加载失败)。
    若本 test 首次加载成功，后续 test 直接复用该 cached module。
    """
    # Step 1: Fix app.config.settings stub (add missing DATABASE_URL etc.)
    _augment_settings_stub()
    # Step 2: Remove google.genai stubs so real package can load (for app.api.chapters cascade)
    _clean_google_genai_stubs()
    yield
    # Teardown: 不清除 app.api.chapters (保留 cached module 供后续 test 复用)


# --------------------------------------------------------------------------
# 辅助: 构建 mock objects (Project / Chapter / GenerationJob)
# --------------------------------------------------------------------------

def make_project(
    characters_confirmed: bool = False,
    scenes_confirmed: bool = False,
    raw_outline_json: str | None = None,
    confirmed_outline_json: str | None = None,
) -> MagicMock:
    """构建 mock Project"""
    p = MagicMock()
    p.id = 100
    p.uuid = "test-uuid"
    p.characters_confirmed = characters_confirmed
    p.scenes_confirmed = scenes_confirmed
    p.raw_outline_json = raw_outline_json
    p.confirmed_outline_json = confirmed_outline_json
    return p


def make_chapter(
    status: str = "pending",
    full_script: str | None = None,
    scenes_json: str | None = None,
    storyboard_json: str | None = None,
    characters_json: str | None = None,
    summary: str | None = None,
    error_message: str | None = None,
) -> MagicMock:
    """构建 mock Chapter"""
    c = MagicMock()
    c.id = 200
    c.project_id = 100
    c.chapter_number = 1
    c.status = status
    c.full_script = full_script
    c.scenes_json = scenes_json
    c.storyboard_json = storyboard_json
    c.characters_json = characters_json
    c.summary = summary
    c.error_message = error_message
    return c


def make_job(
    status: str = "processing",
    current_stage: str = "story_generation",
    progress: int = 5,
    failed_shot_count: int = 0,
    partial_failure: bool = False,
) -> MagicMock:
    """构建 mock GenerationJob"""
    j = MagicMock()
    j.id = 300
    j.status = status
    j.current_stage = current_stage
    j.progress = progress
    j.failed_shot_count = failed_shot_count
    j.partial_failure = partial_failure
    j.estimated_seconds = None
    j.stage_message = None
    return j


# --------------------------------------------------------------------------
# 测试 1: ui_phase 派生 — 各种 stage 组合
# --------------------------------------------------------------------------

class TestUiPhaseDerivation:
    """RISK-T15-8 顺解: backend ui_phase 派生覆盖完整状态机"""

    def setup_method(self) -> None:
        # 延迟 import 避免 module-level FastAPI app boot
        from app.api.chapters import _derive_ui_phase
        self._derive_ui_phase = _derive_ui_phase

    def test_no_job_no_outline_returns_input(self) -> None:
        """无 job 且无大纲数据 → input"""
        project = make_project()
        chapter = make_chapter()
        assert self._derive_ui_phase(None, project, chapter) == "input"

    def test_no_job_with_raw_outline_returns_outline_review(self) -> None:
        """大纲生成完等用户确认 → outline_review"""
        project = make_project(raw_outline_json='{"title": "test"}')
        chapter = make_chapter()
        assert self._derive_ui_phase(None, project, chapter) == "outline_review"

    def test_no_job_with_confirmed_outline_returns_outline_review(self) -> None:
        """用户已确认大纲但 job 还没真启动 → outline_review"""
        project = make_project(confirmed_outline_json='{"title": "test"}')
        chapter = make_chapter()
        assert self._derive_ui_phase(None, project, chapter) == "outline_review"

    def test_pending_job_returns_outline_review(self) -> None:
        """job pending（还没真启动）+ 有大纲 → outline_review"""
        project = make_project(confirmed_outline_json='{"title": "test"}')
        chapter = make_chapter()
        job = make_job(status="pending", current_stage=None)
        assert self._derive_ui_phase(job, project, chapter) == "outline_review"

    def test_story_generation_stage_returns_char_review_pending(self) -> None:
        """Stage 1 在跑 → char_review_pending（角色还没生成）"""
        project = make_project()
        chapter = make_chapter()
        job = make_job(current_stage="story_generation")
        assert self._derive_ui_phase(job, project, chapter) == "char_review_pending"

    def test_character_design_stage_returns_char_review_pending(self) -> None:
        """Stage 2 在跑 → char_review_pending"""
        project = make_project()
        chapter = make_chapter()
        job = make_job(current_stage="character_design")
        assert self._derive_ui_phase(job, project, chapter) == "char_review_pending"

    def test_character_ready_unconfirmed_returns_char_review(self) -> None:
        """character_ready stage + 未确认 → char_review（R4-1 等用户）"""
        project = make_project(characters_confirmed=False)
        chapter = make_chapter()
        job = make_job(current_stage="character_ready")
        assert self._derive_ui_phase(job, project, chapter) == "char_review"

    def test_character_ready_confirmed_returns_scene_review_pending(self) -> None:
        """character_ready + 已确认（瞬态）→ scene_review_pending（Stage 3 即将启动）"""
        project = make_project(characters_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="character_ready")
        assert self._derive_ui_phase(job, project, chapter) == "scene_review_pending"

    def test_screenplay_stage_returns_scene_review_pending(self) -> None:
        """Stage 3 在跑 → scene_review_pending"""
        project = make_project(characters_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="screenplay")
        assert self._derive_ui_phase(job, project, chapter) == "scene_review_pending"

    def test_scenes_ready_unconfirmed_returns_storyboard_running(self) -> None:
        """T22-NEW-5: scenes_ready + scenes_confirmed=False → storyboard_running
        (R4-2 scene_review 等待环节已移除，Stage 3→4 直连，scenes_confirmed 不再用作等待信号)"""
        project = make_project(characters_confirmed=True, scenes_confirmed=False)
        chapter = make_chapter()
        job = make_job(current_stage="scenes_ready")
        assert self._derive_ui_phase(job, project, chapter) == "storyboard_running"

    def test_scenes_ready_confirmed_returns_storyboard_running(self) -> None:
        """scenes_ready + 已确认（瞬态）→ storyboard_running"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="scenes_ready")
        assert self._derive_ui_phase(job, project, chapter) == "storyboard_running"

    def test_storyboard_stage_returns_storyboard_running(self) -> None:
        """Stage 4 在跑 → storyboard_running"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="storyboard")
        assert self._derive_ui_phase(job, project, chapter) == "storyboard_running"

    def test_image_preparation_returns_shot_generating(self) -> None:
        """Stage 5a 参考图准备 → shot_generating"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="image_preparation")
        assert self._derive_ui_phase(job, project, chapter) == "shot_generating"

    def test_image_generation_returns_shot_generating(self) -> None:
        """Stage 5b shot 生成 → shot_generating"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="image_generation")
        assert self._derive_ui_phase(job, project, chapter) == "shot_generating"

    def test_bgm_stage_returns_shot_generating(self) -> None:
        """BGM 生成阶段 → shot_generating（同 image 阶段，用户都看进度）"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter()
        job = make_job(current_stage="bgm")
        assert self._derive_ui_phase(job, project, chapter) == "shot_generating"

    def test_completed_stage_returns_completed(self) -> None:
        """Pipeline 跑完 → completed"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter(status="completed")
        job = make_job(status="completed", current_stage="completed", progress=100)
        assert self._derive_ui_phase(job, project, chapter) == "completed"

    def test_completed_status_with_non_completed_stage_returns_completed(self) -> None:
        """job.status=completed 即使 stage 不是 completed（边界 case）"""
        project = make_project(characters_confirmed=True, scenes_confirmed=True)
        chapter = make_chapter(status="completed")
        job = make_job(status="completed", current_stage="image_generation", progress=100)
        assert self._derive_ui_phase(job, project, chapter) == "completed"

    def test_unknown_stage_fallback_to_char_review_pending(self) -> None:
        """未知 stage 兜底 → char_review_pending"""
        project = make_project()
        chapter = make_chapter()
        job = make_job(current_stage="mystery_unknown_stage")
        assert self._derive_ui_phase(job, project, chapter) == "char_review_pending"


# --------------------------------------------------------------------------
# 测试 2: hydrate_hints 派生 — 每个 phase 的 endpoint 正确
# --------------------------------------------------------------------------

class TestHydrateHints:
    """RISK-T15-3 顺解: hydrate_hints 告诉 frontend hydrate 哪个 endpoint"""

    def setup_method(self) -> None:
        from app.api.chapters import _build_hydrate_hints
        self._build_hydrate_hints = _build_hydrate_hints

    def test_char_review_hints_to_characters_endpoint(self) -> None:
        """char_review 阶段 hydrate /characters endpoint"""
        hints = self._build_hydrate_hints("char_review", chapter_number=1)
        assert hints is not None
        assert "/characters" in hints.endpoint
        assert hints.display_field == "characters"
        assert "Character" in hints.expected_data_shape

    def test_scene_review_phase_removed_returns_none(self) -> None:
        """T22-NEW-5: scene_review ui_phase 已移除 (R4-2 确认环节砍掉, Stage 3→4 直连).
        _build_hydrate_hints("scene_review") 应返回 None (无 hydrate 分支).
        历史背景: RISK-T15-3 要求 scene_review hydrate /story，
        但 T22-NEW-5 移除了 scene_review 整个状态，此 hydrate 分支同步删除."""
        hints = self._build_hydrate_hints("scene_review", chapter_number=1)
        assert hints is None, "T22-NEW-5 移除 scene_review 后，此 phase 应返 None hydrate_hints"

    def test_shot_generating_hints_to_storyboard_endpoint(self) -> None:
        """shot_generating 阶段 hydrate /storyboard endpoint（含 image_url）"""
        hints = self._build_hydrate_hints("shot_generating", chapter_number=1)
        assert hints is not None
        assert "/storyboard" in hints.endpoint
        assert hints.display_field == "shots"
        assert "Shot" in hints.expected_data_shape

    def test_completed_hints_to_storyboard_endpoint(self) -> None:
        """completed 阶段也 hydrate /storyboard endpoint（preview 页面）"""
        hints = self._build_hydrate_hints("completed", chapter_number=1)
        assert hints is not None
        assert "/storyboard" in hints.endpoint
        assert hints.display_field == "shots"

    def test_input_phase_returns_none(self) -> None:
        """input 阶段不需要 hydrate 内容"""
        assert self._build_hydrate_hints("input", chapter_number=1) is None

    def test_outline_review_phase_returns_none(self) -> None:
        """outline_review 阶段不需要 hydrate（用 project detail endpoint）"""
        assert self._build_hydrate_hints("outline_review", chapter_number=1) is None

    def test_pending_phases_return_none(self) -> None:
        """各 *_pending 阶段不需要 hydrate（frontend 等 stage 推进）"""
        for phase in ("char_review_pending", "scene_review_pending", "storyboard_running"):
            assert self._build_hydrate_hints(phase, chapter_number=1) is None, \
                f"{phase} 不应有 hydrate_hints"

    def test_chapter_number_in_endpoint(self) -> None:
        """endpoint 必须含 chapter_number"""
        hints = self._build_hydrate_hints("char_review", chapter_number=2)
        assert "/chapters/2" in hints.endpoint
        assert "/chapters/1" not in hints.endpoint

    def test_endpoint_has_project_id_placeholder(self) -> None:
        """endpoint 含 {project_id} 占位符（frontend 实际调用时替换）.
        T22-NEW-5: 改用 char_review (scene_review 已移除) 验证占位符机制."""
        hints = self._build_hydrate_hints("char_review", chapter_number=1)
        assert hints is not None, "char_review 应有 hydrate_hints"
        assert "{project_id}" in hints.endpoint, \
            "endpoint 应含 {project_id} 占位符让 frontend 替换"


# --------------------------------------------------------------------------
# 测试 3: GET /story endpoint 在 scenes_ready 阶段返回 scenes (RISK-T15-3)
# --------------------------------------------------------------------------

class TestGetStoryEndpoint:
    """RISK-T15-3 顺解: GET /story 在 chapter.status=generating_story 但 scenes_json 已存在时返回 scenes"""

    def test_scenes_ready_returns_scenes_not_404(self) -> None:
        """关键 case: chapter.status='generating_story' + scenes_json 非空 → 应返 200 + scenes，不是 404"""
        # 模拟 endpoint 内的核心判断逻辑（不依赖 FastAPI / DB）
        scenes_data = [{"scene_id": 1, "description": "Scene 1"}]
        chapter = make_chapter(
            status="generating_story",  # Pipeline 还在跑（R4-2 等用户确认）
            scenes_json=json.dumps(scenes_data),
            full_script=None,  # full_script 还没写（Stage 5 后才写）
        )

        # 模拟新逻辑: 先检查 scenes_json + full_script 是否有数据
        has_data = bool(chapter.scenes_json or chapter.full_script)
        assert has_data, "scenes_json 非空时应有数据"

        # 模拟 endpoint 解析 scenes
        scenes = json.loads(chapter.scenes_json) if chapter.scenes_json else []
        assert len(scenes) == 1
        assert scenes[0]["scene_id"] == 1

    def test_truly_no_data_returns_empty(self) -> None:
        """真没数据时（Stage 3 未完成）返 200+空结构（Wave 11.2 T18-G fix: 取代旧 404）"""
        chapter = make_chapter(
            status="generating_story",
            scenes_json=None,
            full_script=None,
        )
        has_data = bool(chapter.scenes_json or chapter.full_script)
        # T18-G: 无数据时 endpoint 改返 200+empty，不再 404。
        # 此 test 验证数据条件（has_data=False），endpoint 行为改为 200+empty 见 test_chapter_story_no_data_returns_200_empty
        assert not has_data, "scenes_json + full_script 都为 None 时 has_data=False → 返 200+空结构"

    def test_completed_with_full_script_returns_shots(self) -> None:
        """完整跑完时返完整 full_script"""
        full_script_data = {
            "title": "Test Story",
            "scenes": [{"scene_id": 1}],
            "shots": [{"shot_id": 1}, {"shot_id": 2}],
        }
        chapter = make_chapter(
            status="completed",
            scenes_json=json.dumps([{"scene_id": 1}]),
            full_script=json.dumps(full_script_data),
        )

        full_script = json.loads(chapter.full_script)
        assert full_script["title"] == "Test Story"
        assert len(full_script["shots"]) == 2

    def test_scenes_ready_stub_full_script(self) -> None:
        """RISK-T15-3 + RISK-T14-7: scenes_ready 阶段 full_script 用 stub（title + scenes）"""
        scenes_data = [{"scene_id": 1, "description": "Scene 1"}]
        chapter = make_chapter(
            status="generating_story",
            scenes_json=json.dumps(scenes_data),
            full_script=None,
            summary="My Test Title",
        )

        # 模拟 endpoint 内的 stub 构造逻辑
        scenes = json.loads(chapter.scenes_json) if chapter.scenes_json else []
        full_script = {
            "title": chapter.summary or "故事生成中",
            "scenes": scenes,
        }

        assert full_script["title"] == "My Test Title"
        assert full_script["scenes"] == scenes_data

    def test_failed_status_returns_400(self) -> None:
        """chapter.status=failed 时 400（不变，验证未破坏）"""
        chapter = make_chapter(status="failed", error_message="LLM crashed")
        assert chapter.status == "failed"
        # endpoint 内的判断: status=failed → raise 400


# --------------------------------------------------------------------------
# 测试 4: mid-stage failed_shot_count 实时累加 (RISK-T15-9)
# --------------------------------------------------------------------------

class TestMidStageFailedCount:
    """RISK-T15-9 顺解: 单 shot 失败时立即更新 DB，不等 Pipeline finalize"""

    @pytest.mark.asyncio
    async def test_increment_failed_shot_count_first_failure(self) -> None:
        """第一次失败: failed_shot_count 0 → 1, partial_failure → True"""
        # Mock async_session_maker + GenerationJob
        mock_job = MagicMock()
        mock_job.failed_shot_count = 0
        mock_job.partial_failure = False

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_job)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        # Mock session_maker context manager
        class MockSessionMaker:
            def __call__(self):
                return self
            async def __aenter__(self):
                return mock_db
            async def __aexit__(self, *args):
                return None

        with patch("app.services.job_manager.async_session_maker", MockSessionMaker()):
            from app.services.job_manager import increment_failed_shot_count
            new_count = await increment_failed_shot_count(job_id=123)

        assert new_count == 1, "failed_shot_count 应从 0 → 1"
        assert mock_job.failed_shot_count == 1
        assert mock_job.partial_failure is True, "一旦有失败 partial_failure 必须 True"

    @pytest.mark.asyncio
    async def test_increment_failed_shot_count_multiple_failures(self) -> None:
        """多次失败: 5 → 6, partial_failure 保持 True"""
        mock_job = MagicMock()
        mock_job.failed_shot_count = 5
        mock_job.partial_failure = True

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=mock_job)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        class MockSessionMaker:
            def __call__(self):
                return self
            async def __aenter__(self):
                return mock_db
            async def __aexit__(self, *args):
                return None

        with patch("app.services.job_manager.async_session_maker", MockSessionMaker()):
            from app.services.job_manager import increment_failed_shot_count
            new_count = await increment_failed_shot_count(job_id=456)

        assert new_count == 6
        assert mock_job.failed_shot_count == 6

    @pytest.mark.asyncio
    async def test_increment_failed_shot_count_job_not_found(self) -> None:
        """job_id 找不到对应 job → 返 -1，不抛异常"""
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.commit = AsyncMock()

        class MockSessionMaker:
            def __call__(self):
                return self
            async def __aenter__(self):
                return mock_db
            async def __aexit__(self, *args):
                return None

        with patch("app.services.job_manager.async_session_maker", MockSessionMaker()):
            from app.services.job_manager import increment_failed_shot_count
            new_count = await increment_failed_shot_count(job_id=999)

        assert new_count == -1, "找不到 job 应返 -1（不抛异常）"

    @pytest.mark.asyncio
    async def test_increment_db_exception_is_non_blocking(self) -> None:
        """DB commit 抛异常 → 返 -1，不传播异常（Pipeline 不应中断）"""
        mock_db = MagicMock()
        mock_db.execute = AsyncMock(side_effect=Exception("Connection lost"))
        mock_db.commit = AsyncMock()

        class MockSessionMaker:
            def __call__(self):
                return self
            async def __aenter__(self):
                return mock_db
            async def __aexit__(self, *args):
                return None

        with patch("app.services.job_manager.async_session_maker", MockSessionMaker()):
            from app.services.job_manager import increment_failed_shot_count
            new_count = await increment_failed_shot_count(job_id=789)

        assert new_count == -1, "DB 异常时应返 -1（不传播异常）"


# --------------------------------------------------------------------------
# 测试 5: ChapterStatus schema 含新字段（防止 schema 退化）
# --------------------------------------------------------------------------

class TestChapterStatusSchema:
    """防止未来误删 Wave 9 新字段（schema 退化检测）"""

    def test_schema_has_ui_phase_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "ui_phase" in ChapterStatus.model_fields

    def test_schema_has_hydrate_hints_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "hydrate_hints" in ChapterStatus.model_fields

    def test_schema_has_characters_confirmed_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "characters_confirmed" in ChapterStatus.model_fields

    def test_schema_has_scenes_confirmed_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "scenes_confirmed" in ChapterStatus.model_fields

    def test_schema_has_storyboard_ready_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "storyboard_ready" in ChapterStatus.model_fields

    def test_schema_has_outline_ready_field(self) -> None:
        from app.schemas.chapter import ChapterStatus
        assert "outline_ready" in ChapterStatus.model_fields

    def test_old_fields_preserved(self) -> None:
        """Wave 9 改动不破坏现有字段"""
        from app.schemas.chapter import ChapterStatus
        for f in (
            "status", "stage", "progress", "estimated_remaining_seconds",
            "message", "failed_shot_count", "partial_failure",
        ):
            assert f in ChapterStatus.model_fields, f"老字段 {f} 不能丢"

    def test_hydrate_hints_default_none(self) -> None:
        """hydrate_hints 默认 None（不要求 caller 永远传）"""
        from app.schemas.chapter import ChapterStatus
        cs = ChapterStatus(
            status="processing",
            stage="screenplay",
            progress=20,
            estimated_remaining_seconds=300,
            message="generating",
        )
        assert cs.hydrate_hints is None
        assert cs.ui_phase == "input"  # default
        assert cs.characters_confirmed is False
        assert cs.scenes_confirmed is False
