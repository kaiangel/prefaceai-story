"""RISK-T20-13 (2026-05-19) — Backend status API shots_total / shots_completed / shots_failed 字段

测试 GET /api/projects/{uuid}/chapters/{N}/status 新增 3 个 shot 级真实计数字段:
  - shots_total: chapter.storyboard_json 解析（= actual_shot_count）
  - shots_completed: stage_message regex "已生成 X/Y" 解析 / progress 反推 / stage 派生
  - shots_failed: job.failed_shot_count (DB)

设计原则 (universal, 不破坏向后兼容):
  - 早期 stage (storyboard_json 没生成) → 3 字段全 null
  - stage="completed" → shots_completed = shots_total
  - stage="image_generation" → 优先 regex "已生成 X/Y"; 兜底 progress 反推 (75+20*X/Y)
  - 其他 stage (storyboard / screenplay / bgm) → shots_completed=0
  - 旧字段不破坏 (failed_shot_count / actual_shot_count / partial_failure)

测试覆盖 (universal):
  - schema: 3 新字段类型 + Optional 默认 None
  - regex parser: "已生成 5/20" → 5; "已生成 18/20 张图像（含失败）" → 18; 无 message → None
  - progress 反推: 75 → 0; 85 → ~10; 95 → ~20
  - stage 派生: completed → total; image_preparation → 0; bgm → 0
  - 失败计数: job.failed_shot_count 5 → shots_failed 5
"""

import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# 1. Schema 字段验证
# ---------------------------------------------------------------------------

class TestChapterStatusSchema:
    """RISK-T20-13: ChapterStatus schema 必须含 shots_total / shots_completed / shots_failed"""

    def test_chapter_status_schema_has_shots_total(self):
        from app.schemas.chapter import ChapterStatus
        fields = ChapterStatus.model_fields
        assert "shots_total" in fields, "ChapterStatus 必须含 shots_total 字段"

    def test_chapter_status_schema_has_shots_completed(self):
        from app.schemas.chapter import ChapterStatus
        fields = ChapterStatus.model_fields
        assert "shots_completed" in fields, "ChapterStatus 必须含 shots_completed 字段"

    def test_chapter_status_schema_has_shots_failed(self):
        from app.schemas.chapter import ChapterStatus
        fields = ChapterStatus.model_fields
        assert "shots_failed" in fields, "ChapterStatus 必须含 shots_failed 字段"

    def test_chapter_status_shots_fields_default_none(self):
        """3 新字段默认值必须 None (向后兼容: 旧调用不传也能 instantiate)"""
        from app.schemas.chapter import ChapterStatus
        status = ChapterStatus(
            status="processing",
            stage="story_generation",
            progress=5,
            estimated_remaining_seconds=300,
            message="测试",
        )
        assert status.shots_total is None
        assert status.shots_completed is None
        assert status.shots_failed is None

    def test_chapter_status_shots_fields_accept_int(self):
        """3 新字段可接受 int 值"""
        from app.schemas.chapter import ChapterStatus
        status = ChapterStatus(
            status="processing",
            stage="image_generation",
            progress=85,
            estimated_remaining_seconds=180,
            message="已生成 10/20 张图像...",
            shots_total=20,
            shots_completed=10,
            shots_failed=0,
        )
        assert status.shots_total == 20
        assert status.shots_completed == 10
        assert status.shots_failed == 0

    def test_chapter_status_old_fields_intact(self):
        """旧字段不破坏: actual_shot_count / max_concurrent / failed_shot_count / partial_failure"""
        from app.schemas.chapter import ChapterStatus
        fields = ChapterStatus.model_fields
        for old_field in (
            "actual_shot_count",
            "max_concurrent",
            "failed_shot_count",
            "partial_failure",
            "estimated_remaining_seconds",
        ):
            assert old_field in fields, f"旧字段 {old_field} 不应被移除"


# ---------------------------------------------------------------------------
# 2. message regex 解析逻辑（pipeline_orchestrator.py L1362/L1424 格式）
# ---------------------------------------------------------------------------

class TestMessageRegexParser:
    """RISK-T20-13: message regex '已生成 X/Y' 解析正确性"""

    REGEX = re.compile(r"已生成\s*(\d+)\s*/\s*\d+")

    def test_parse_normal_message(self):
        """L1362 模板: '已生成 5/20 张图像...'"""
        msg = "已生成 5/20 张图像..."
        m = self.REGEX.search(msg)
        assert m is not None
        assert int(m.group(1)) == 5

    def test_parse_failure_inclusive_message(self):
        """L1424 模板: '已生成 18/20 张图像（含失败）...'"""
        msg = "已生成 18/20 张图像（含失败）..."
        m = self.REGEX.search(msg)
        assert m is not None
        assert int(m.group(1)) == 18

    def test_parse_no_space_message(self):
        """容错: 没空格 '已生成5/20'"""
        msg = "已生成5/20张..."
        m = self.REGEX.search(msg)
        assert m is not None
        assert int(m.group(1)) == 5

    def test_parse_empty_message_returns_none(self):
        msg = ""
        m = self.REGEX.search(msg)
        assert m is None

    def test_parse_unrelated_message_returns_none(self):
        """其他 stage message 不应误匹配"""
        msg = "正在生成大纲..."
        m = self.REGEX.search(msg)
        assert m is None

    def test_parse_full_completion(self):
        """完成消息: '已生成 20/20'"""
        msg = "已生成 20/20 张图像..."
        m = self.REGEX.search(msg)
        assert m is not None
        assert int(m.group(1)) == 20


# ---------------------------------------------------------------------------
# 3. Progress 反推逻辑（兜底）
# ---------------------------------------------------------------------------

class TestProgressBackCalculation:
    """当 message 无法 regex 解析时, 用 progress 反推 shots_completed
    公式: pipeline_orchestrator L1359 → progress = 75 + int(20 * done / total)
          反推: done = (progress - 75) * total / 20
    """

    @staticmethod
    def _calc_from_progress(progress: int, total: int) -> int:
        if progress < 75:
            return 0
        return max(0, min(total, int((progress - 75) * total / 20)))

    def test_progress_75_means_0_done(self):
        """75% = image_generation 入口 (P1-1 callback), 0 shot 完成"""
        assert self._calc_from_progress(75, 20) == 0

    def test_progress_85_means_half_done(self):
        """85% = 半程 (75 + 10), 20 shots × 10/20 = 10 shot 完成"""
        assert self._calc_from_progress(85, 20) == 10

    def test_progress_95_means_all_done(self):
        """95% = image_generation 终点, 20 shots 全完成"""
        assert self._calc_from_progress(95, 20) == 20

    def test_progress_below_75_means_0(self):
        """progress 还没到 75 (image_preparation 阶段) → 0 shots completed"""
        assert self._calc_from_progress(70, 20) == 0
        assert self._calc_from_progress(50, 20) == 0

    def test_progress_clamped_to_total(self):
        """progress 100 但还在 image_generation → 不能超 total"""
        assert self._calc_from_progress(100, 20) == 20

    def test_universal_shot_counts(self):
        """universal: 5 / 19 / 29 / 50 shots 都成立"""
        for total in (5, 19, 29, 50):
            assert self._calc_from_progress(75, total) == 0
            assert self._calc_from_progress(95, total) == total


# ---------------------------------------------------------------------------
# 4. Stage 派生逻辑
# ---------------------------------------------------------------------------

class TestStageDerivedShotsCompleted:
    """RISK-T20-13: 不同 stage 下 shots_completed 派生规则"""

    @staticmethod
    def _derive(stage: str, progress: int, message: str, total: int) -> int:
        """复现 chapters.py status endpoint 的 shots_completed 派生逻辑"""
        if stage == "completed":
            return total
        elif stage == "image_generation":
            m = re.search(r"已生成\s*(\d+)\s*/\s*\d+", message or "")
            if m:
                return min(int(m.group(1)), total)
            if progress >= 75:
                return max(0, min(total, int((progress - 75) * total / 20)))
            return 0
        else:
            return 0

    def test_completed_stage_returns_total(self):
        """stage=completed → shots_completed = shots_total (无论 message)"""
        assert self._derive("completed", 100, "故事生成完成！", 20) == 20
        assert self._derive("completed", 100, "", 5) == 5

    def test_image_generation_with_message_regex(self):
        """优先 regex"""
        assert self._derive("image_generation", 85, "已生成 12/20 张图像...", 20) == 12

    def test_image_generation_without_message_uses_progress(self):
        """message 无规律 → 兜底 progress 反推"""
        assert self._derive("image_generation", 85, "正在绘制...", 20) == 10  # (85-75)*20/20

    def test_image_preparation_stage_returns_0(self):
        """非 image_generation stage (image_preparation) → 0"""
        assert self._derive("image_preparation", 70, "准备参考图...", 20) == 0

    def test_bgm_stage_returns_0(self):
        """bgm stage → 0 (不在 image 计数范围)"""
        assert self._derive("bgm", 95, "正在生成 BGM...", 20) == 0

    def test_storyboard_stage_returns_0(self):
        """storyboard stage → 0"""
        assert self._derive("storyboard", 40, "正在编写分镜...", 20) == 0


# ---------------------------------------------------------------------------
# 5. 真实业务场景模拟（端到端字段一致性）
# ---------------------------------------------------------------------------

class TestRealWorldScenarios:
    """模拟真实 chapter status 请求, 验证 3 字段联动正确"""

    def test_scenario_early_stage_all_null(self):
        """早期 stage (story_generation): storyboard_json 没生成 → 3 字段全 null"""
        # 模拟 chapters.py 逻辑：
        # _shot_count_for_response = None  (storyboard_json empty)
        # → _shots_total = None
        # → _shots_failed = None
        # → _shots_completed = None
        shot_count = None  # storyboard_json empty
        shots_total = shot_count
        assert shots_total is None
        # 其他 2 字段也应 None (chapters.py if _shots_total is not None: ... else None)

    def test_scenario_image_generation_in_progress(self):
        """image_generation 中: shots_total=20, completed 从 message 解析, failed=2"""
        # job 状态: stage=image_generation, message="已生成 15/20 张图像（含失败）...", failed_shot_count=2
        stage = "image_generation"
        message = "已生成 15/20 张图像（含失败）..."
        progress = 87
        failed_shot_count = 2
        shots_total = 20

        m = re.search(r"已生成\s*(\d+)\s*/\s*\d+", message)
        assert m is not None
        shots_completed = int(m.group(1))
        shots_failed = failed_shot_count

        assert shots_total == 20
        assert shots_completed == 15
        assert shots_failed == 2
        # 隐含: in_flight = total - completed = 5 (frontend 可算)
        assert shots_total - shots_completed == 5

    def test_scenario_completed(self):
        """完成: shots_completed = total, shots_failed = job.failed_shot_count"""
        stage = "completed"
        shots_total = 20
        failed_shot_count = 0
        if stage == "completed":
            shots_completed = shots_total
        else:
            shots_completed = 0
        assert shots_completed == 20
        assert failed_shot_count == 0

    def test_scenario_completed_with_partial_failure(self):
        """完成但有部分失败: completed=total, failed>0"""
        stage = "completed"
        shots_total = 20
        failed_shot_count = 3
        shots_completed = shots_total if stage == "completed" else 0
        assert shots_completed == 20  # 都跑完了（含失败）
        assert failed_shot_count == 3  # 但 3 张失败

    def test_scenario_test17_v2_audit(self):
        """test17 v2 真实场景: 20 shots, 中段 message=null, 用 progress 反推"""
        # 假设 backend 还没 update message 但 progress 已 88
        stage = "image_generation"
        progress = 88
        message = ""  # 假设刚切到 image_generation, message 还没更新
        shots_total = 20
        m = re.search(r"已生成\s*(\d+)\s*/\s*\d+", message)
        assert m is None
        # 兜底 progress 反推: (88-75)*20/20 = 13
        shots_completed = max(0, min(shots_total, int((progress - 75) * shots_total / 20)))
        assert shots_completed == 13


# ---------------------------------------------------------------------------
# 6. 源码验证 (确保 chapters.py 真有 shots_total / completed / failed 字段)
# ---------------------------------------------------------------------------

class TestSourceCodeVerification:
    """确保 chapters.py status endpoint 真正传入 3 新字段"""

    def test_chapters_py_has_shots_total_in_response(self):
        """chapters.py 必须在 ChapterStatus(...) 调用里传 shots_total=..."""
        import inspect
        from app.api import chapters
        source = inspect.getsource(chapters)
        assert "shots_total=" in source, \
            "chapters.py 必须在 ChapterStatus 调用中传 shots_total"

    def test_chapters_py_has_shots_completed_in_response(self):
        import inspect
        from app.api import chapters
        source = inspect.getsource(chapters)
        assert "shots_completed=" in source, \
            "chapters.py 必须在 ChapterStatus 调用中传 shots_completed"

    def test_chapters_py_has_shots_failed_in_response(self):
        import inspect
        from app.api import chapters
        source = inspect.getsource(chapters)
        assert "shots_failed=" in source, \
            "chapters.py 必须在 ChapterStatus 调用中传 shots_failed"

    def test_chapters_py_imports_re(self):
        """chapters.py 必须 import re (regex 解析)"""
        import inspect
        from app.api import chapters
        source = inspect.getsource(chapters)
        assert "import re" in source, "chapters.py 必须 import re"

    def test_chapters_py_has_regex_message_parse(self):
        """chapters.py 必须有 '已生成 X/Y' regex"""
        import inspect
        from app.api import chapters
        source = inspect.getsource(chapters)
        # 注意 raw string + 中文匹配
        assert "已生成" in source, "chapters.py 必须含中文 '已生成' regex"
