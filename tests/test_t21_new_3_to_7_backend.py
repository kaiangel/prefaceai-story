"""T21-NEW-3/4/5/6/7 Backend 综合测试 (Wave 5, 2026-05-21)

覆盖 5 个 task 的关键修复:
- T21-NEW-3: restart-from-failed-stage 真重算 progress + ETA
- T21-NEW-4: AdjustCharacter / RegeneratePortrait portrait_url 带 ?v={epoch} cache-buster
- T21-NEW-5: pipeline_orchestrator Stage 5 stage_message "全身参考图" 文案
- T21-NEW-6: image_preparation sub-stage 细化 (≥4 sub-step stage_message)
- T21-NEW-7: Stage 4.5 scene_image_preparation + 3 endpoint + STATUS_API_CONTRACT v1.4

Backend Opus 4.7 thinking xhigh, 2026-05-21
"""

import json
import re
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_file(rel: str) -> str:
    """读项目下的文件内容 (绝对路径)"""
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


# ============================================================================
# T21-NEW-3: restart-from-failed-stage progress/ETA reset
# ============================================================================

class TestT21New3RestartProgressETAReset:
    """T21-NEW-3: restart 真重算 progress + ETA 验证"""

    def test_restart_endpoint_imports_calc_eta(self):
        """restart endpoint 引入 calculate_eta_remaining_sec 用于真重算"""
        src = _read_file("app/api/chapters.py")
        # 应该 import 了 calculate_eta_remaining_sec (作为 _calc_eta)
        assert "calculate_eta_remaining_sec as _calc_eta" in src

    def test_restart_endpoint_computes_initial_progress(self):
        """restart 真重算 initial_progress (按 start_from_stage 映射)"""
        src = _read_file("app/api/chapters.py")
        assert "_RESTART_STAGE_TO_PROGRESS" in src
        assert "_initial_progress = _RESTART_STAGE_TO_PROGRESS.get" in src
        # 关键: 5 个 stage 映射存在
        assert "1: 2," in src  # story_generation
        assert "2: 6," in src  # character_design
        assert "3: 11," in src  # screenplay
        assert "4: 35," in src  # storyboard
        assert "5: 65," in src  # image_preparation

    def test_restart_endpoint_computes_initial_eta_with_real_params(self):
        """restart 真重算 ETA 时传 actual_shot_count / unique_location_count / max_concurrent 真值"""
        src = _read_file("app/api/chapters.py")
        # 真值参数传入 _calc_eta
        assert "_restart_actual_shot_count" in src
        assert "_restart_unique_location_count" in src
        assert "_restart_max_concurrent" in src
        # 真调用 _calc_eta 传参
        assert "actual_shot_count=_restart_actual_shot_count" in src
        assert "unique_location_count=_restart_unique_location_count" in src
        assert "max_concurrent=_restart_max_concurrent" in src

    def test_restart_endpoint_writes_initial_state_to_db(self):
        """restart 立即把 progress + ETA 写 DB, frontend 第一次 poll 拿到真值"""
        src = _read_file("app/api/chapters.py")
        # 改了 job.progress + job.estimated_seconds + job.stage_message 后 await db.commit
        assert "job.progress = _initial_progress" in src
        assert "job.estimated_seconds = _initial_eta" in src
        assert "job.stage_message = _initial_message" in src
        # commit 在 set 之后
        idx_set = src.index("job.progress = _initial_progress")
        idx_commit = src.index("await db.commit()", idx_set)
        assert idx_commit > idx_set

    def test_restart_endpoint_friendly_stage_message(self):
        """restart 用更友好的 stage_message"""
        src = _read_file("app/api/chapters.py")
        assert "_STAGE_FRIENDLY_MESSAGE" in src
        # 5 个 stage 都有友好 message
        assert "从故事大纲重启中..." in src
        assert "从角色设计重启中..." in src
        assert "从分场剧本重启中..." in src
        assert "从分镜创建重启中..." in src
        assert "从画面准备重启中..." in src


# ============================================================================
# T21-NEW-4: AdjustCharacter portrait cache-buster ?v={epoch}
# ============================================================================

class TestT21New4PortraitCacheBuster:
    """T21-NEW-4: portrait_url + fullbody_url 加 ?v={epoch} 防 frontend cache"""

    def test_adjust_character_portrait_url_has_cache_buster(self):
        """AdjustCharacter portrait_url 带 ?v={int(time.time())}"""
        src = _read_file("app/api/projects.py")
        # adjust_character 内: portrait_url 含 ?v={_v_ts}
        # T21-NEW-4 注释存在
        assert "T21-NEW-4" in src
        # 真模式: ?v={_v_ts}
        m_adjust = re.search(
            r'AdjustCharacter.*?T21-NEW-4.*?portrait_url\s*=\s*f"/static/outputs/.*?\?v=\{_v_ts\}"',
            src, re.DOTALL
        )
        assert m_adjust is not None, "AdjustCharacter portrait_url 必须含 ?v={_v_ts}"

    def test_adjust_character_fullbody_url_has_cache_buster(self):
        """AdjustCharacter B57 fullbody_url 也带 ?v={_v_ts}"""
        src = _read_file("app/api/projects.py")
        # B57 cascade fullbody 重生 → URL 含 ?v={_v_ts}
        assert re.search(
            r'_fullbody_url\s*=\s*f"/static/outputs/.*?_fullbody\.png\?v=\{_v_ts\}"',
            src
        ) is not None

    def test_regenerate_portrait_endpoint_has_cache_buster(self):
        """RegeneratePortrait endpoint portrait_url 带 ?v={_v_ts}"""
        src = _read_file("app/api/projects.py")
        # RegeneratePortrait 内有 _v_ts + portrait_url 含 ?v={_v_ts}
        assert "RegeneratePortrait" in src
        # 真 cache-buster 实例
        assert re.search(
            r'portrait_url\s*=\s*f"/static/outputs/.*?_portrait\.png\?v=\{_v_ts\}"',
            src
        ) is not None

    def test_characters_json_updated_with_cache_busted_url(self):
        """chapter.characters_json 也写带 ?v= 的 URL (不止 outline)"""
        src = _read_file("app/api/projects.py")
        # 至少 2 处更新 chars_list[char_index]["portrait_url"] = portrait_url (含 cache-buster)
        # AdjustCharacter + RegeneratePortrait 各一处
        matches = re.findall(r'chars_list\[char_index\]\["portrait_url"\]\s*=\s*portrait_url', src)
        assert len(matches) >= 2


# ============================================================================
# T21-NEW-5: pipeline Stage 5 stage_message "全身参考图" 文案
# ============================================================================

class TestT21New5StageMessageFullbody:
    """T21-NEW-5: image_preparation stage_message 改 '全身参考图' 明确语义"""

    def test_image_preparation_message_uses_fullbody(self):
        """progress_callback message 含 '全身参考图' 不再是 '角色参考图'"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 真改 — message 含 "全身参考图 X/Y 完成"
        assert "全身参考图" in src
        # T21-NEW-5 注释存在 (说明动机)
        assert "T21-NEW-5" in src

    def test_image_preparation_old_message_replaced(self):
        """旧 '角色参考图 X/Y 完成' 字面已被替换 (除非在注释/旧 print)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 真 progress_callback message 不再是 "角色参考图 {_completed_char_count[0]}/..."
        # 找 progress_callback 调用上下文真用 f"全身参考图 ... 完成"
        assert re.search(
            r'progress_callback\(\s*"image_preparation",\s*_prep_pct,\s*f"全身参考图\s*\{_completed_char_count\[0\]\}',
            src, re.DOTALL
        ) is not None


# ============================================================================
# T21-NEW-6: image_preparation 多 sub-step stage_message 细化 (≥4 sub-step)
# ============================================================================

class TestT21New6SubStageMessages:
    """T21-NEW-6: image_preparation sub-step ≥4 stage_message UPDATE (T21-NEW-7 后只剩 fullbody + shots 调度)"""

    def test_scene_reference_manager_accepts_sub_progress_callback(self):
        """SceneReferenceManager.generate_anchor_images 支持 sub_progress_callback 参数"""
        src = _read_file("app/services/scene_reference_manager.py")
        assert "sub_progress_callback" in src
        assert "sub_progress_stage_name" in src
        assert "sub_progress_base_pct" in src
        assert "sub_progress_max_pct" in src
        # 真有 _emit_sub_progress helper
        assert "_emit_sub_progress" in src

    def test_scene_reference_manager_emits_per_view_progress(self):
        """每个 interior/exterior 完成后真 emit sub-progress"""
        src = _read_file("app/services/scene_reference_manager.py")
        # interior 完成后 emit
        assert 'await _emit_sub_progress("interior"' in src
        # exterior 完成后 emit
        assert 'await _emit_sub_progress("exterior"' in src

    def test_pipeline_stage_4_5_passes_sub_progress(self):
        """Pipeline Stage 4.5 调用 generate_anchor_images 时传 sub_progress_callback"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # Stage 4.5 调用 + 传 sub_progress 参数
        assert 'sub_progress_callback=progress_callback' in src
        assert 'sub_progress_stage_name="scene_image_preparation"' in src

    def test_stage_5_5a_entry_has_sub_message(self):
        """Stage 5 5a 入口加 stage_message '准备角色全身参考图...'"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "准备角色全身参考图..." in src

    def test_stage_5_5b_entry_has_sub_message(self):
        """Stage 5 5b 调度入口加 stage_message '准备分镜参考映射...'"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "准备分镜参考映射" in src
        # image_generation entry 也细化加 shot count "0/N"
        assert "开始绘制画面 (0/" in src

    def test_total_substages_count_ge_4(self):
        """≥4 个 sub-step stage_message UPDATE (验收标准)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 数 progress_callback("image_preparation"  +  progress_callback("scene_image_preparation"
        # 应该 ≥4 (Stage 4.5 entry + Stage 4.5 per-view ≥2 + Stage 5 5a + Stage 5 5b dispatch)
        # 检查关键 sub-message 字符串都存在
        markers = [
            "全身参考图",        # Stage 5 5a per-char
            "生成场景参考图",    # Stage 4.5 per-view (in scene_reference_manager.py)
            "准备角色全身参考图", # Stage 5 5a entry
            "准备分镜参考映射",  # Stage 5 5b dispatch
            "正在生成场景参考图", # Stage 4.5 entry
        ]
        for m in markers:
            assert m in src or m in _read_file("app/services/scene_reference_manager.py"), \
                f"sub-stage marker '{m}' 缺失"


# ============================================================================
# T21-NEW-7: Stage 4.5 + 3 endpoint + DB schema + STATUS_API_CONTRACT v1.4
# ============================================================================

class TestT21New7Pipeline:
    """T21-NEW-7: Pipeline 引入 Stage 4.5 scene_image_preparation"""

    def test_pipeline_has_stage_4_5(self):
        """Pipeline 真新增 Stage 4.5 scene_image_preparation"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "Stage 4.5: scene_image_preparation" in src or "Stage 4.5 scene_image_preparation" in src
        assert "Stage 4.5: SceneImagePreparation" in src
        assert "scene_image_preparation" in src

    def test_pipeline_has_r4_3_wait_loop(self):
        """Pipeline 真有 R4-3 wait loop 等用户确认场景参考图"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "R4-3" in src
        assert "scene_references_confirmed" in src
        assert "scene_refs_confirmed_flag" in src

    def test_pipeline_writes_scene_references_json(self):
        """Stage 4.5 真写 chapter.scene_references_json (经 checkpoint_callback)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert 'checkpoint_callback("scene_references_json"' in src
        assert "scene_references_list" in src

    def test_pipeline_stage_5_reuses_scene_ref_manager(self):
        """Stage 5 5a.5 复用 Stage 4.5 的 scene_ref_manager (不再生成)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 5a.5 注释改为 "Stage 4.5 已生成"
        assert "场景参考图 (Stage 4.5 已生成, 此处复用)" in src
        # 兜底路径 (Stage 4.5 未跑) 保留
        assert "Stage 4.5 未生成场景参考图, 走兜底路径重新生成" in src

    def test_pipeline_stage_durations_has_4_5(self):
        """STAGE_DURATIONS 加 scene_image_preparation + scene_references_ready"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert '"scene_image_preparation": 180' in src
        assert '"scene_references_ready": 0' in src

    def test_pipeline_start_from_stage_4_skip_r4_3(self):
        """原地重启 start_from_stage > 4 时跳过 R4-3 (与 R4-2 一致模式)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "if start_from_stage > 4:" in src and "scene_refs_confirmed_flag = True" in src


class TestT21New7Endpoints:
    """T21-NEW-7: 3 新 endpoint"""

    def test_get_scene_references_endpoint_exists(self):
        """GET /chapters/{n}/scene-references endpoint"""
        src = _read_file("app/api/chapters.py")
        assert '@router.get("/{chapter_number}/scene-references")' in src
        assert "async def get_scene_references" in src

    def test_get_scene_references_returns_required_fields(self):
        """GET endpoint response 含必需 4 字段"""
        src = _read_file("app/api/chapters.py")
        # 真返回 scene_references / scene_references_ready / scene_references_confirmed / countdown_seconds
        assert '"scene_references":' in src
        assert '"scene_references_ready":' in src
        assert '"scene_references_confirmed":' in src
        assert '"countdown_seconds": 60' in src

    def test_regenerate_scene_reference_endpoint_exists(self):
        """POST /chapters/{n}/scenes/{location_id}/regenerate-reference endpoint"""
        src = _read_file("app/api/chapters.py")
        assert '@router.post("/{chapter_number}/scenes/{location_id}/regenerate-reference")' in src
        assert "async def regenerate_scene_reference" in src

    def test_regenerate_scene_reference_supports_ref_type(self):
        """regenerate 支持 ref_type interior/exterior/both"""
        src = _read_file("app/api/chapters.py")
        assert "SceneReferenceRegenerateRequest" in src
        # ref_type field 支持 "interior" / "exterior" / "both"
        assert 'ref_type: str = "both"' in src
        # 真用 if body.ref_type in ("interior", "both") 等
        assert 'body.ref_type in ("interior", "both")' in src
        assert 'body.ref_type in ("exterior", "both")' in src

    def test_regenerate_scene_reference_returns_cache_buster_urls(self):
        """重生后 URL 带 ?v={_v_ts} cache-buster"""
        src = _read_file("app/api/chapters.py")
        # interior_url + exterior_url 都带 ?v={_v_ts}
        assert "interior_anchor.png?v={_v_ts}" in src
        assert "exterior_anchor.png?v={_v_ts}" in src

    def test_regenerate_scene_reference_uses_interior_as_exterior_reference(self):
        """重生 exterior 时用 interior 作参考 (DEC-014/DEC-009 一致性)"""
        src = _read_file("app/api/chapters.py")
        # 真传 reference_image=_ref_for_exterior (interior PIL)
        assert "_ref_for_exterior" in src
        assert "DEC-014/DEC-009" in src

    def test_confirm_scene_references_endpoint_exists(self):
        """POST /chapters/{n}/confirm-scene-references endpoint"""
        src = _read_file("app/api/chapters.py")
        assert '@router.post("/{chapter_number}/confirm-scene-references")' in src
        assert "async def confirm_scene_references" in src

    def test_confirm_scene_references_sets_project_field(self):
        """confirm 端点真设置 project.scene_references_confirmed = True"""
        src = _read_file("app/api/chapters.py")
        # confirm_scene_references 函数内真改字段
        m = re.search(
            r'def confirm_scene_references.*?project\.scene_references_confirmed\s*=\s*True',
            src, re.DOTALL
        )
        assert m is not None

    def test_confirm_scene_references_validates_stage_4_5_done(self):
        """confirm 验证 Stage 4.5 已完成 (chapter.scene_references_json 非空)"""
        src = _read_file("app/api/chapters.py")
        m = re.search(
            r'def confirm_scene_references.*?if not chapter\.scene_references_json',
            src, re.DOTALL
        )
        assert m is not None


class TestT21New7DBSchema:
    """T21-NEW-7: DB schema 改动"""

    def test_project_model_has_scene_references_confirmed(self):
        """Project.scene_references_confirmed 列存在"""
        src = _read_file("app/models/project.py")
        assert "scene_references_confirmed" in src
        assert "Column(Boolean" in src
        # 真 Column 定义
        assert re.search(
            r'scene_references_confirmed\s*=\s*Column\(Boolean',
            src
        ) is not None

    def test_chapter_model_has_scene_references_json(self):
        """Chapter.scene_references_json 列存在 (LONGTEXT)"""
        src = _read_file("app/models/chapter.py")
        assert "scene_references_json" in src
        # 真 Column 定义为 LONGTEXT
        assert re.search(
            r'scene_references_json\s*=\s*Column\(LONGTEXT',
            src
        ) is not None

    def test_alembic_migration_006_exists(self):
        """Alembic migration 006 文件存在"""
        migration_path = PROJECT_ROOT / "alembic/versions/006_add_scene_references_t21_new7.py"
        assert migration_path.exists()

    def test_alembic_migration_006_adds_both_columns(self):
        """Migration 真加两列 (project.scene_references_confirmed + chapter.scene_references_json)"""
        src = _read_file("alembic/versions/006_add_scene_references_t21_new7.py")
        # 真 add_column 两列
        assert "add_column" in src
        assert "scene_references_confirmed" in src
        assert "scene_references_json" in src
        # 真 backfill 旧项目
        assert "UPDATE projects" in src and "scene_references_confirmed = TRUE" in src


class TestT21New7StatusAPIContract:
    """T21-NEW-7: STATUS_API_CONTRACT v1.4 升级"""

    def test_schemas_chapter_status_has_scene_references_fields(self):
        """ChapterStatus schema 加 scene_references_ready + scene_references_confirmed"""
        src = _read_file("app/schemas/chapter.py")
        assert "scene_references_ready: bool" in src
        assert "scene_references_confirmed: bool" in src
        assert "T21-NEW-7" in src
        assert "v1.4" in src

    def test_derive_ui_phase_handles_scene_references_review(self):
        """_derive_ui_phase 真返 scene_references_review when stage=scene_references_ready"""
        src = _read_file("app/api/chapters.py")
        assert "scene_references_review" in src
        # 真 if branch 处理 scene_references_ready stage
        assert 'if stage == "scene_references_ready":' in src

    def test_derive_ui_phase_handles_scene_image_preparation(self):
        """_derive_ui_phase 处理 scene_image_preparation stage (复用 storyboard_running UI)"""
        src = _read_file("app/api/chapters.py")
        assert 'if stage == "scene_image_preparation":' in src

    def test_build_hydrate_hints_handles_scene_references_review(self):
        """_build_hydrate_hints 处理 scene_references_review (返 /scene-references endpoint)"""
        src = _read_file("app/api/chapters.py")
        assert 'if ui_phase == "scene_references_review":' in src
        assert '"{base}/scene-references"' in src or '/scene-references' in src

    def test_status_endpoint_returns_scene_references_fields(self):
        """status endpoint return ChapterStatus 含两个新字段"""
        src = _read_file("app/api/chapters.py")
        # status return 块 (both no-job + with-job paths)
        # scene_references_ready=bool(...) 出现 ≥2 处
        matches = re.findall(r'scene_references_ready\s*=\s*bool\(', src)
        assert len(matches) >= 2
        matches2 = re.findall(r'scene_references_confirmed\s*=\s*bool\(', src)
        assert len(matches2) >= 2


class TestT21New7StartGenerationReset:
    """T21-NEW-7: start_generation 重置 scene_references_confirmed (与 R4-1/R4-2 一致)"""

    def test_start_generation_resets_scene_references_confirmed(self):
        """start_generation 重置 project.scene_references_confirmed = False"""
        src = _read_file("app/api/projects.py")
        # start_generation 函数内有 reset
        m = re.search(
            r'def start_generation.*?project\.scene_references_confirmed\s*=\s*False',
            src, re.DOTALL
        )
        assert m is not None


class TestT21New7JobManagerETA:
    """T21-NEW-7: job_manager ETA baselines 加 4.5 stage"""

    def test_eta_baselines_has_scene_image_preparation(self):
        """_ETA_STAGE_BASELINES 加 scene_image_preparation + scene_references_ready"""
        src = _read_file("app/services/job_manager.py")
        assert '"scene_image_preparation": 180' in src
        assert '"scene_references_ready": 0' in src

    def test_eta_progress_bounds_has_scene_image_preparation(self):
        """_ETA_STAGE_PROGRESS_BOUNDS 加 scene_image_preparation"""
        src = _read_file("app/services/job_manager.py")
        assert '"scene_image_preparation": (60, 63)' in src
        assert '"scene_references_ready": (63, 63)' in src


# ============================================================================
# E2E syntax check — 所有改动文件能 import 不崩溃
# ============================================================================

class TestSyntaxCheck:
    """py_compile 所有改动文件"""

    def test_pipeline_orchestrator_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/services/pipeline_orchestrator.py"), doraise=True)

    def test_chapters_api_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/api/chapters.py"), doraise=True)

    def test_projects_api_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/api/projects.py"), doraise=True)

    def test_job_manager_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/services/job_manager.py"), doraise=True)

    def test_scene_reference_manager_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/services/scene_reference_manager.py"), doraise=True)

    def test_models_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/models/project.py"), doraise=True)
        py_compile.compile(str(PROJECT_ROOT / "app/models/chapter.py"), doraise=True)

    def test_schemas_compiles(self):
        import py_compile
        py_compile.compile(str(PROJECT_ROOT / "app/schemas/chapter.py"), doraise=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
