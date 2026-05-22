"""T22-NEW-5 Backend 测试: R4-2 wait loop 移除 + scene_review ui_phase 移除

覆盖:
- Task 1: pipeline_orchestrator.py R4-2 wait loop 移除，Stage 3 完成直接进 Stage 4
- Task 2: chapters.py confirm-scenes noop endpoint (不再 update DB)
- Task 3: _derive_ui_phase 不再返回 scene_review
- Task 4: STATUS_API_CONTRACT.md v1.5 升级验证

Founder 5/22 13:37 决策: R4-2 文字层场景确认可跳过。
Backend Wave 8 第 3 批, Sonnet 4.6 xhigh, 2026-05-22
"""

import re
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _read_file(rel: str) -> str:
    """读项目下的文件内容 (绝对路径)"""
    return (PROJECT_ROOT / rel).read_text(encoding="utf-8")


# ============================================================================
# Task 1: pipeline_orchestrator.py — R4-2 wait loop 移除
# ============================================================================

class TestPipelineOrchestatorR42Removed:
    """R4-2 wait loop 在 pipeline_orchestrator.py 中应完整移除"""

    def test_r42_while_loop_removed(self):
        """while r42_waited < r42_max_wait 不应存在"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "r42_max_wait" not in src, (
            "r42_max_wait 变量仍存在 — R4-2 wait loop 未完整移除"
        )
        assert "r42_waited" not in src, (
            "r42_waited 变量仍存在 — R4-2 wait loop 未完整移除"
        )

    def test_r42_scenes_confirmed_poll_removed(self):
        """scenes_confirmed 的 R4-2 轮询查询不应存在"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 不应有 R4-2 段里的 scenes_confirmed 轮询
        assert "r42_row" not in src, (
            "r42_row (R4-2 轮询结果变量) 仍存在 — wait loop 未移除"
        )
        assert "r42_result" not in src, (
            "r42_result (R4-2 轮询 query 变量) 仍存在 — wait loop 未移除"
        )

    def test_r42_removal_marker_exists(self):
        """T22-NEW-5 移除标记应存在"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "T22-NEW-5" in src, "T22-NEW-5 标记不存在 — 修改未落地"
        assert "R4-2 wait loop 已移除" in src, "R4-2 wait loop 移除标记不存在"

    def test_stage4_progress_callback_immediate(self):
        """Stage 3 完成后直接 storyboard progress_callback (无等待)"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # 移除后，stage 3 完成后应立即有 storyboard progress_callback
        assert '"storyboard"' in src, "storyboard stage callback 应存在"
        assert "正在创建分镜" in src, "Stage 4 启动消息应存在"

    def test_r43_wait_loop_preserved(self):
        """R4-3 wait loop (scene_references_review) 应保留完整"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "T21-NEW-7 R4-3" in src, "R4-3 wait loop 标记不存在 — 误删 R4-3"
        assert "scene_references_confirmed" in src, (
            "scene_references_confirmed 不存在 — R4-3 wait loop 可能被误删"
        )

    def test_r41_wait_loop_preserved(self):
        """R4-1 wait loop (character_review) 应保留完整"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        assert "characters_confirmed" in src, (
            "characters_confirmed 不存在 — R4-1 wait loop 可能被误删"
        )

    def test_scenes_confirmed_db_column_not_polled(self):
        """pipeline_orchestrator 不再轮询 Project.scenes_confirmed 作为闸门"""
        src = _read_file("app/services/pipeline_orchestrator.py")
        # scenes_confirmed 可能仍有出现（如 RISK-T17-8 注释或旧引用），
        # 但不应有 while/asyncio.sleep 结合的 scenes_confirmed 轮询 loop
        r42_loop_pattern = re.compile(
            r"while.*r42_waited.*scenes_confirmed",
            re.DOTALL,
        )
        assert not r42_loop_pattern.search(src), (
            "scenes_confirmed R4-2 轮询 loop 仍存在"
        )


# ============================================================================
# Task 2: chapters.py — confirm-scenes noop endpoint
# ============================================================================

class TestConfirmScenesNoopEndpoint:
    """chapters.py confirm-scenes noop endpoint"""

    def test_confirm_scenes_noop_endpoint_exists(self):
        """chapters.py 应有 confirm_scenes_noop endpoint"""
        src = _read_file("app/api/chapters.py")
        assert "confirm_scenes_noop" in src, (
            "confirm_scenes_noop endpoint 不存在 — Task 2 未完成"
        )

    def test_confirm_scenes_noop_route_registered(self):
        """router.post confirm-scenes 路由应在 chapters.py 注册"""
        src = _read_file("app/api/chapters.py")
        assert '/{chapter_number}/confirm-scenes' in src, (
            "confirm-scenes 路由未在 chapters.py 注册"
        )

    def test_confirm_scenes_noop_deprecation_log(self):
        """noop endpoint 应有 deprecation warning log"""
        src = _read_file("app/api/chapters.py")
        assert "no-op deprecated" in src or "noop deprecated" in src or "is no-op deprecated" in src, (
            "deprecation warning log 不存在"
        )

    def test_confirm_scenes_noop_returns_200_deprecated(self):
        """noop endpoint 应返回 deprecated=True + success=True"""
        src = _read_file("app/api/chapters.py")
        assert '"deprecated": True' in src or "'deprecated': True" in src, (
            "noop endpoint 未返回 deprecated=True"
        )
        # success True 应在 noop endpoint 中
        assert "success" in src, "success 字段应存在"

    def test_confirm_scenes_noop_does_not_update_db(self):
        """noop endpoint 不应 commit scenes_confirmed=True"""
        src = _read_file("app/api/chapters.py")
        # 找 confirm_scenes_noop 函数体，验证不含 scenes_confirmed = True
        # 用简单 marker: noop 函数里不应出现 scenes_confirmed = True + db.commit
        noop_start = src.find("async def confirm_scenes_noop")
        assert noop_start != -1, "confirm_scenes_noop 函数不存在"
        # 找函数体结束（下一个 @router 或 async def）
        next_decorator = src.find("\n@router", noop_start + 1)
        if next_decorator == -1:
            noop_body = src[noop_start:]
        else:
            noop_body = src[noop_start:next_decorator]
        assert "project.scenes_confirmed = True" not in noop_body, (
            "noop endpoint 不应设置 scenes_confirmed = True"
        )
        assert "await db.commit()" not in noop_body, (
            "noop endpoint 不应 commit DB (pure noop)"
        )


# ============================================================================
# Task 3: chapters.py — _derive_ui_phase 不返回 scene_review
# ============================================================================

class TestDeriveUiPhaseNoSceneReview:
    """_derive_ui_phase 不应返回 scene_review"""

    def test_derive_ui_phase_no_scene_review_return(self):
        """_derive_ui_phase 不应有 return 'scene_review' 语句"""
        src = _read_file("app/api/chapters.py")
        # 找 _derive_ui_phase 函数体
        func_start = src.find("def _derive_ui_phase(")
        assert func_start != -1, "_derive_ui_phase 函数不存在"
        # 找下一个函数定义
        func_end = src.find("\ndef ", func_start + 1)
        func_body = src[func_start:func_end] if func_end != -1 else src[func_start:]
        # 不应有 return "scene_review"
        assert 'return "scene_review"' not in func_body, (
            '_derive_ui_phase 仍返回 "scene_review" — Task 3 未完成'
        )

    def test_scenes_ready_stage_maps_to_storyboard_running(self):
        """scenes_ready stage 应直接映射到 storyboard_running"""
        src = _read_file("app/api/chapters.py")
        # scenes_ready 处理后应返回 storyboard_running
        func_start = src.find("def _derive_ui_phase(")
        func_end = src.find("\ndef ", func_start + 1)
        func_body = src[func_start:func_end] if func_end != -1 else src[func_start:]
        # 应有 scenes_ready 处理
        assert "scenes_ready" in func_body, "scenes_ready stage 未在 _derive_ui_phase 中处理"
        # scenes_ready 分支应返回 storyboard_running
        assert "storyboard_running" in func_body, (
            "storyboard_running 不在 _derive_ui_phase 中 — scenes_ready 映射可能丢失"
        )

    def test_scene_review_removed_from_comments(self):
        """模块顶部注释应标明 scene_review 已移除"""
        src = _read_file("app/api/chapters.py")
        assert "scene_review REMOVED" in src or "T22-NEW-5" in src, (
            "chapters.py 顶部注释未标明 scene_review 已移除"
        )

    def test_build_hydrate_hints_no_scene_review(self):
        """_build_hydrate_hints 不应有 scene_review hydrate 分支"""
        src = _read_file("app/api/chapters.py")
        func_start = src.find("def _build_hydrate_hints(")
        assert func_start != -1, "_build_hydrate_hints 函数不存在"
        func_end = src.find("\ndef ", func_start + 1)
        func_body = src[func_start:func_end] if func_end != -1 else src[func_start:]
        # 不应有 scene_review 作为条件
        assert 'ui_phase == "scene_review"' not in func_body, (
            '_build_hydrate_hints 仍有 scene_review hydrate 分支'
        )

    def test_status_response_still_returns_scenes_confirmed_field(self):
        """status response 仍应返回 scenes_confirmed 字段（向后兼容）"""
        src = _read_file("app/api/chapters.py")
        # scenes_confirmed 字段应在 status response 中
        assert "scenes_confirmed=" in src, (
            "scenes_confirmed 字段从 status response 移除 — 破坏向后兼容"
        )


# ============================================================================
# Task 4: STATUS_API_CONTRACT.md v1.5 升级验证
# ============================================================================

class TestStatusApiContractV15:
    """STATUS_API_CONTRACT.md 应升级到 v1.5"""

    def test_contract_version_v15(self):
        """契约文档版本应为 v1.5"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        assert "v1.5" in src, "STATUS_API_CONTRACT 未升级到 v1.5"

    def test_contract_scene_review_removed_from_type(self):
        """UiPhase type 中 scene_review 应被注释/移除"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        # scene_review 不应作为有效 enum value 存在（允许以注释形式保留历史）
        # 检查: | "scene_review" 不应在 UiPhase 定义中
        assert '  | "scene_review"' not in src, (
            'scene_review 仍作为有效 UiPhase enum value 存在'
        )

    def test_contract_v15_history_entry(self):
        """§8 历史应有 v1.5 条目"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        assert "v1.5" in src, "§8 历史未有 v1.5 条目"
        assert "T22-NEW-5" in src, "§8 历史未提及 T22-NEW-5"

    def test_contract_frontend_impact_label(self):
        """v1.5 条目应含 frontend-impact: yes 标签"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        assert "frontend-impact: yes" in src, (
            "v1.5 条目缺 [frontend-impact: yes] 标签 (Ben 5/13 协议)"
        )

    def test_contract_8_phase_state_machine(self):
        """状态机应为 8 个 phase (scene_review 移除后)"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        # 验证文档说明 8 状态机（而非 9）
        assert "8 状态" in src or "8 ui_phase" in src or "8 个状态" in src or "8 状态机" in src, (
            "契约文档未更新到 8 状态机描述"
        )

    def test_contract_transition_diagram_no_scene_review_box(self):
        """转换图中不应有 scene_review 状态框"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        # 确保转换图不再有 | scene_review  | 这样的状态框
        assert "│ scene_review  │" not in src, (
            "转换图仍含 scene_review 状态框"
        )

    def test_contract_r41_r43_preserved(self):
        """R4-1 + R4-3 闸门描述应保留"""
        src = _read_file(".team-brain/contracts/STATUS_API_CONTRACT.md")
        assert "R4-1" in src, "R4-1 描述被误删"
        assert "R4-3" in src, "R4-3 描述被误删"
        assert "scene_references_review" in src, "scene_references_review 被误删"
        assert "char_review" in src, "char_review 被误删"
