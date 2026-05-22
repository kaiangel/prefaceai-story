"""Job management service for async task tracking"""

import json
import logging
import time
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models.job import GenerationJob
from app.models.chapter import Chapter
from app.models.project import Project
from app.services.story_generator import StoryGenerator

logger = logging.getLogger("xuhua")


# ---------------------------------------------------------------------------
# RISK-T17-5 (Wave 11.3): ETA helper — stage-aware remaining time calculation
# ---------------------------------------------------------------------------

# Stage duration baselines (seconds) — kept in sync with pipeline_orchestrator.py
# These are conservative estimates; actual values are computed dynamically.
# T21-NEW-7 (2026-05-21 DEC-047): 新增 Stage 4.5 (scene_image_preparation + scene_references_ready)
_ETA_STAGE_BASELINES: dict[str, int] = {
    "story_generation": 150,      # Stage 1 Sonnet (~137-180s realtime)
    "character_design": 120,      # Stage 2 Sonnet + portrait generation
    "character_ready": 0,         # R4-1: user wait phase — not counted in ETA
    "screenplay": 213,            # Stage 3 ScreenplayWriter (~213s realtime)
    "scenes_ready": 0,            # R4-2: user wait phase — not counted in ETA
    "storyboard": 236,            # Stage 4 StoryboardDirector (~236s realtime)
    "scene_image_preparation": 180,  # T21-NEW-7 Stage 4.5: scene anchor 生成 (interior+exterior per location)
    "scene_references_ready": 0,     # T21-NEW-7 R4-3: user wait phase — not counted in ETA
    "image_preparation": 270,     # 5a fullbody 参考图 (Stage 4.5 抽出 location 后只剩 fullbody)
    "image_generation": 360,      # 5b shot images — overridden dynamically by actual_shot_count
    "bgm": 120,                   # BGM synthesis + Whisper alignment
    "completed": 0,               # terminal state — ETA = 0
}

# Ordered stage sequence (must match pipeline_orchestrator.py)
_ETA_STAGE_ORDER = list(_ETA_STAGE_BASELINES.keys())

# Global progress bounds per stage (matches _STAGE_PROGRESS_BOUNDS in progress_callback)
# T21-NEW-7: storyboard 35-60 (留 60-63 给 Stage 4.5), scene_image_preparation 60-63,
# scene_references_ready 63 (R4-3 等), image_preparation 63-70, image_generation 70-92, bgm 92-100
_ETA_STAGE_PROGRESS_BOUNDS: dict[str, tuple[int, int]] = {
    "story_generation": (2, 6),
    "character_design": (6, 10),
    "character_ready": (10, 10),
    "screenplay": (11, 32),
    "scenes_ready": (32, 35),
    "storyboard": (35, 60),
    "scene_image_preparation": (60, 63),  # T21-NEW-7 DEC-047 Stage 4.5
    "scene_references_ready": (63, 63),   # T21-NEW-7 R4-3 等用户确认
    "image_preparation": (63, 70),
    "image_generation": (70, 92),
    "bgm": (92, 100),
    "completed": (100, 100),
}


def calculate_eta_remaining_sec(
    stage: str,
    progress: int,
    started_at: Optional[datetime] = None,
    elapsed: Optional[float] = None,
    actual_shot_count: int = 18,
    unique_location_count: int = 2,
    max_concurrent: int = 3,
) -> Optional[int]:
    """RISK-T17-5 (Wave 11.3): Stage-aware ETA calculation helper.

    Computes the estimated remaining seconds from the current pipeline stage and
    global progress percentage.  Each stage resets ETA independently — elapsed
    time from previous stages does NOT bleed into the next stage's estimate.

    Design:
    - Converts global progress (0-100) to within-stage progress (0.0-1.0)
      using _ETA_STAGE_PROGRESS_BOUNDS.
    - Subtracts the within-stage completed fraction from that stage's duration.
    - Adds the full duration of all subsequent stages.
    - image_generation duration is scaled dynamically: actual_shot_count × 60s / max_concurrent.
    - image_preparation duration is scaled by character + location count.
    - "completed" always returns 0.
    - Unknown stage returns None (caller decides whether to show ETA).

    Args:
        stage: Current pipeline stage name (e.g. "image_generation").
        progress: Global progress integer 0-100 from progress_callback.
        started_at: Job started_at timestamp (currently informational; reserved for
                    future elapsed-based correction).
        elapsed: Seconds elapsed since this stage started (currently informational;
                 reserved for future per-stage elapsed tracking).
        actual_shot_count: True shot count after Stage 4 completes (default 18).
        unique_location_count: Number of unique scene locations (default 2).
        max_concurrent: Seedream concurrent image slots (default 3).

    Returns:
        Estimated remaining seconds (>= 5 for non-terminal stages), 0 for
        "completed", None for unknown stages.

    Stage switching behaviour (key fix for T17-5):
        This function is STATELESS — it does NOT maintain monotonic state.
        Monotonic enforcement happens at the call-site (progress_callback) and
        is RESET on every stage switch, so a new stage always starts from its
        own full baseline rather than being capped by the previous stage's ETA.
    """
    if stage == "completed":
        return 0

    if stage not in _ETA_STAGE_BASELINES:
        logger.debug(f"[calculate_eta_remaining_sec] unknown stage={stage!r}, returning None")
        return None

    # Build dynamic stage durations
    durations = dict(_ETA_STAGE_BASELINES)

    # image_preparation: scale by character count (estimated) and location count
    char_count = max(1, min(actual_shot_count // 6, 6))  # rough: 6 shots per character, max 6
    durations["image_preparation"] = max(char_count * 90 + unique_location_count * 90, 180)

    # image_generation: scale by actual shot count and concurrency
    # RISK-T20-9 (2026-05-18): 60 → 80 s/shot — see pipeline_orchestrator.build_stage_durations 注释
    # 必须与 pipeline_orchestrator.py 保持同步, 两处 baseline 偏差会导致 ETA 跳变
    durations["image_generation"] = max(
        int(actual_shot_count * 80 / max(max_concurrent, 1)), 60
    )

    # Compute within-stage progress from global progress
    bounds = _ETA_STAGE_PROGRESS_BOUNDS.get(stage)
    if bounds and bounds[1] > bounds[0]:
        lo, hi = bounds
        stage_progress = max(0.0, min(1.0, (progress - lo) / (hi - lo)))
    else:
        stage_progress = 0.0  # unknown bounds → assume stage just started

    # Current stage: remaining fraction
    remaining = int(durations[stage] * (1.0 - stage_progress))

    # All subsequent stages: full duration
    idx = _ETA_STAGE_ORDER.index(stage)
    for s in _ETA_STAGE_ORDER[idx + 1:]:
        remaining += durations[s]

    # Minimum 5s for non-terminal in-progress stages (avoids "0s" flicker)
    return max(remaining, 5)


class JobManager:
    """Service for managing generation jobs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_job(self, chapter_id: int) -> GenerationJob:
        """Create a new generation job for a chapter"""
        job = GenerationJob(
            chapter_id=chapter_id,
            status="queued",
            current_stage="story_generation",
            progress=0,
            stage_message="等待开始生成...",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def update_job_status(
        self,
        job_id: int,
        status: str | None = None,
        stage: str | None = None,
        progress: int | None = None,
        message: str | None = None,
        estimated_seconds: int | None = None,
    ) -> GenerationJob:
        """Update job status and progress"""
        result = await self.db.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        job = result.scalar_one_or_none()

        if not job:
            raise ValueError(f"Job {job_id} not found")

        if status:
            job.status = status
            if status == "processing" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ("completed", "failed"):
                job.completed_at = datetime.utcnow()

        if stage:
            job.current_stage = stage
        if progress is not None:
            job.progress = progress
        if message:
            job.stage_message = message
        if estimated_seconds is not None:
            job.estimated_seconds = estimated_seconds

        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_job(self, job_id: int) -> GenerationJob | None:
        """Get job by ID"""
        result = await self.db.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_latest_job_for_chapter(self, chapter_id: int) -> GenerationJob | None:
        """Get the most recent job for a chapter"""
        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.chapter_id == chapter_id)
            .order_by(GenerationJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def _update_job_short_session(
    job_id: int,
    status: str | None = None,
    stage: str | None = None,
    progress: int | None = None,
    message: str | None = None,
    estimated_seconds: int | None = None,
    failed_shot_count: int | None = None,
    partial_failure: bool | None = None,
):
    """B-1: 使用短生命周期 session 更新 job 状态，避免长 pipeline 运行中 MySQL 连接超时
    B46: 增加 failed_shot_count / partial_failure 可选参数。
    """
    async with async_session_maker() as db:
        result = await db.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return

        if status:
            job.status = status
            if status == "processing" and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ("completed", "failed"):
                job.completed_at = datetime.utcnow()

        if stage:
            job.current_stage = stage
        if progress is not None:
            job.progress = progress
        if message:
            job.stage_message = message
        if estimated_seconds is not None:
            job.estimated_seconds = estimated_seconds
        # B46: 部分失败字段
        if failed_shot_count is not None:
            job.failed_shot_count = failed_shot_count
        if partial_failure is not None:
            job.partial_failure = partial_failure

        await db.commit()


async def increment_failed_shot_count(job_id: int) -> int:
    """RISK-T15-9 (Wave 9 / DEC-030): mid-stage 单 shot 失败时立即累加。

    旧逻辑（B46）只在 Pipeline finalize 阶段（job_manager._update_job_short_session
    在 run_story_generation_task 末尾）一次性汇总 failed_shot_count。
    问题: Stage 5 中途 frontend 看不到 partial_failure 状态 → 用户看 progress 时
    不知道部分失败（test15 Shot 22 IncompleteRead 4 retry 全失败时暴露）。

    新机制: pipeline_orchestrator 的 Stage 5 内每张 shot 失败时立即调用此 helper，
    DB 实时反映 failed_shot_count + partial_failure。

    设计要点:
      - 短生命周期 session（与 _update_job_short_session 一致，避免长事务）
      - 失败时返 -1（不抛异常 — Pipeline 不应因 DB 更新失败而中断）
      - partial_failure 永远跟 failed_shot_count > 0 同步
      - 重复调用累加（不去重 — 调用方应只在失败 path 调一次）

    Returns:
        累加后的 failed_shot_count（成功），-1（失败）。
    """
    try:
        async with async_session_maker() as db:
            result = await db.execute(
                select(GenerationJob).where(GenerationJob.id == job_id)
            )
            job = result.scalar_one_or_none()
            if not job:
                logger.warning(
                    f"[increment_failed_shot_count] job_id={job_id} 未找到（非阻塞）"
                )
                return -1

            # 读 + 自增 + 重评估 partial_failure
            current = job.failed_shot_count or 0
            job.failed_shot_count = current + 1
            job.partial_failure = True  # 一旦有失败就是 True（不会被外部清零）

            await db.commit()
            new_count = job.failed_shot_count
            logger.info(
                f"[increment_failed_shot_count] job_id={job_id}: "
                f"failed_shot_count {current} -> {new_count} (partial_failure=True)"
            )
            return new_count
    except Exception as e:
        # 非阻塞: DB 更新失败不应中断 Pipeline
        logger.warning(
            f"[increment_failed_shot_count] job_id={job_id} DB update failed (non-blocking): {e}"
        )
        return -1


async def run_story_generation_task(
    db: AsyncSession,
    job_id: int,
    chapter_id: int,
    idea: str,
    style: str,
    chapter_number: int,
    total_chapters: int,
    duration_minutes: int,
    character_count: int,
    language: str,
    previous_summary: str | None = None,
    characters_json: str | None = None,
    confirmed_outline: dict | None = None,
    project_uuid: str | None = None,
    aspect_ratio: str = "2:3",  # D.15 P0: 用户选择的画幅，默认 "2:3" 兼容旧调用
    user_selected_mood: str | None = None,  # B33: Stage A 用户选的情绪基调
):
    """
    Background task to generate story

    B-1: 所有 DB 操作使用短生命周期 session（async_session_maker），
    不复用传入的长生命周期 db 参数，避免 LLM 调用间隙 MySQL 连接超时。
    """
    logger.info(f"[JobManager] ========== run_story_generation_task 开始 ==========")
    logger.info(f"[JobManager] job_id={job_id}, chapter_id={chapter_id}, style={style}")
    logger.info(f"[JobManager] idea: {idea[:80]}{'...' if len(idea) > 80 else ''}")
    logger.info(f"[JobManager] has_confirmed_outline={'是' if confirmed_outline else '否'}, project_uuid={project_uuid}")
    task_start = time.time()

    generator = StoryGenerator()

    try:
        # B-5: 根据 scene 数量动态估算总时间
        scene_count = 6  # 默认短篇
        if confirmed_outline:
            scene_count = len(confirmed_outline.get("plot_points", [])) or 6
        estimated_total = 75 + 45 + (scene_count * 35) + (scene_count * 70) + 30
        # 约: Stage1=75s + Stage2=45s + Stage3=(scene*35s) + Stage4=(scene*70s) + Stage5=30s

        # RB-5: 根据是否有 confirmed_outline 调整初始消息
        if confirmed_outline:
            initial_message = "大纲已确认，正在设计角色..."
            initial_stage = "character_design"
        else:
            initial_message = "正在构思故事大纲..."
            initial_stage = "story_generation"

        # Update job status to processing (短 session)
        await _update_job_short_session(
            job_id,
            status="processing",
            stage=initial_stage,
            progress=2,
            message=initial_message,
            estimated_seconds=estimated_total,
        )

        # B-1: progress_callback 使用短生命周期 session
        # UX-11: stage="completed" 时同步将 job.status 设为 "completed"
        # P1-2 UX-7: progress 单调 guard — 新 progress < 当前 progress 时保留当前（避免 BGM 入口倒退）
        # BUG-ETA-DISAPPEAR-AT-STAGE-EDGE (Wave 6 / 2026-05-11):
        #   - 旧逻辑 progress_callback **完全忽略** estimated_remaining_seconds，
        #     并且**从不更新** job.estimated_seconds，只在 task 启动时设置一次
        #   - 结果 stage 边界 chapters.py status 端点 fallback 到 job.estimated_seconds - elapsed
        #     当 stage 名不在 STAGE_DURATIONS（如 character_ready）时 estimate_remaining 抛 KeyError
        #     fallback 算法用过期的 task-start estimated_seconds → 跳变或不显示
        #   - 新逻辑：每次 callback 都计算 stage-aware ETA + 单调递减 guard + 写 job.estimated_seconds
        _last_progress: list[int] = [0]  # 用列表包装以便闭包内修改
        _last_eta: list[int | None] = [None]
        # RISK-T17-5 (Wave 11.3): track current stage to detect stage switches and reset
        # monotonic guard — prevents previous stage's ETA from capping the new stage's ETA.
        _last_stage: list[str | None] = [None]
        # Round 2 (2026-05-13): mutable closure state for dynamic ETA params
        # pipeline_orchestrator 在 Stage 4 完成后可通过 progress_callback(actual_shot_count=N,
        # unique_location_count=M) 更新这两个值，让后续 image_generation ETA 动态反映实际 shot 数
        _dyn_shot_count: list[int] = [18]           # 默认短篇 18 shots
        _dyn_location_count: list[int] = [2]        # 默认 2 locations
        _dyn_max_concurrent: list[int] = [3]        # 默认并发 3

        async def progress_callback(
            stage: str,
            progress: int,
            message: str,
            estimated_remaining_seconds: int | None = None,  # A.2: default value 不破坏现有调用
            actual_shot_count: int | None = None,           # Round 2: Stage 4 完成后传入真实 shot 数
            unique_location_count: int | None = None,       # Round 2: Stage 1 完成后传入真实 location 数
            max_concurrent: int | None = None,              # Round 2: 从 settings 传入
        ):
            # Round 2: 更新 mutable closure state（如果 caller 传入了新值）
            if actual_shot_count is not None and actual_shot_count > 0:
                _dyn_shot_count[0] = actual_shot_count
            if unique_location_count is not None and unique_location_count > 0:
                _dyn_location_count[0] = unique_location_count
            if max_concurrent is not None and max_concurrent > 0:
                _dyn_max_concurrent[0] = max_concurrent

            # RISK-T17-5: detect stage switch — reset monotonic ETA guard on every stage transition.
            # Without this reset, min(_last_eta, new_eta) caps the new stage's fresh ETA at the
            # old stage's final (low) value, causing "前面1分钟/后面8分钟" jump problem.
            _stage_switched = (_last_stage[0] is not None and _last_stage[0] != stage)
            if _stage_switched:
                logger.debug(
                    f"[progress_callback] Stage switch {_last_stage[0]!r} → {stage!r}: "
                    f"resetting ETA monotonic guard (was {_last_eta[0]}s)"
                )
                _last_eta[0] = None  # reset: allow new stage to start from its own baseline
            _last_stage[0] = stage

            # 单调 guard: 若新 progress 小于上次 progress，使用上次值
            _guarded_progress = max(progress, _last_progress[0])
            _last_progress[0] = _guarded_progress
            _status = "completed" if stage == "completed" else None

            # BUG-ETA-DISAPPEAR-AT-STAGE-EDGE + RISK-T17-5: 计算 stage-aware ETA
            # 优先用 caller 传入的 override，否则用 calculate_eta_remaining_sec()
            _eta: int | None
            if estimated_remaining_seconds is not None and estimated_remaining_seconds >= 0:
                _eta = int(estimated_remaining_seconds)
            else:
                try:
                    if stage == "completed":
                        _eta = 0
                    else:
                        # RISK-T17-5: use the new calculate_eta_remaining_sec() helper
                        # (stateless, stage-reset-safe, dynamically scaled by shot/location counts)
                        _eta = calculate_eta_remaining_sec(
                            stage=stage,
                            progress=_guarded_progress,
                            actual_shot_count=_dyn_shot_count[0],
                            unique_location_count=_dyn_location_count[0],
                            max_concurrent=_dyn_max_concurrent[0],
                        )
                except Exception as _e:
                    logger.debug(f"[progress_callback] ETA 计算失败（非阻塞）: {_e}")
                    _eta = None

            # 单调递减 guard: 新 ETA 不能大于上次 ETA（防止跳涨）
            # 例外: completed、None、stage 刚切换（_last_eta 已被重置为 None）
            if _eta is not None and _last_eta[0] is not None and stage != "completed":
                _eta = min(_last_eta[0], _eta)
            _last_eta[0] = _eta

            await _update_job_short_session(
                job_id,
                status=_status,
                stage=stage,
                progress=_guarded_progress,
                message=message,
                estimated_seconds=_eta,
            )

        # B-6: checkpoint_callback — 每个 Stage 完成后存中间结果到 chapter 表
        async def checkpoint_callback(column_name: str, data):
            """将 stage 中间结果写入 chapter 表的指定列"""
            try:
                async with async_session_maker() as short_db:
                    chapter_result = await short_db.execute(
                        select(Chapter).where(Chapter.id == chapter_id)
                    )
                    chapter = chapter_result.scalar_one_or_none()
                    if chapter:
                        if isinstance(data, (dict, list)):
                            setattr(chapter, column_name, json.dumps(data, ensure_ascii=False))
                        else:
                            setattr(chapter, column_name, data)
                        await short_db.commit()
                        print(f"  [B-6] ✅ 已写入 chapter.{column_name}")
            except Exception as e:
                print(f"  [B-6] ⚠️ 写入 chapter.{column_name} 失败: {e}")

        # Generate story
        if confirmed_outline:
            # 有用户确认大纲 → 用 PipelineOrchestrator（跳过 Stage 1）
            from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator
            pipeline = Phase2PipelineOrchestrator()
            pipeline_result = await pipeline.run(
                idea=idea,
                style_preset=style,
                target_duration_minutes=duration_minutes,
                language=language,
                character_count=character_count,
                generate_images=True,
                confirmed_outline=confirmed_outline,
                project_uuid=project_uuid,
                chapter_id=chapter_id,  # ARCH-1: 传入 chapter_id，让 pipeline 批量写入 chapter_scene_images
                aspect_ratio=aspect_ratio,  # D.15 P0: 传入用户选择的画幅
                user_selected_mood=user_selected_mood,  # B33: Stage A 情绪基调透传给 BGM
                job_id=job_id,  # RISK-T15-9 (Wave 9 / DEC-030): mid-stage failed_count 实时累加用
                progress_callback=progress_callback,
                checkpoint_callback=checkpoint_callback,
            )
            # Wave 10 / RISK-T16-6: 透传 pipeline 自身的 success 标记。
            # 原代码硬编码 success=True → Pipeline 失败时 chapter.status 仍走 "completed" 路径。
            if pipeline_result.get("success", True):
                result = {"success": True, "data": pipeline_result}
            else:
                result = {
                    "success": False,
                    "error": (
                        f"[Stage {pipeline_result.get('failed_stage', '?')}] "
                        f"{pipeline_result.get('error', 'Pipeline 运行失败')}"
                    ),
                    "data": pipeline_result,
                }
        else:
            result = await generator.generate_story(
                idea=idea,
                style=style,
                chapter_number=chapter_number,
                total_chapters=total_chapters,
                duration_minutes=duration_minutes,
                character_count=character_count,
                language=language,
                previous_summary=previous_summary,
                characters_json=characters_json,
            )

        if not result["success"]:
            task_elapsed = time.time() - task_start
            logger.error(f"[JobManager] ❌ 生成失败 (耗时 {task_elapsed:.1f}s): {result.get('error', '未知错误')}")
            # B-1: 使用短 session 更新失败状态
            await _update_job_short_session(
                job_id,
                status="failed",
                progress=0,
                message=f"生成失败: {result.get('error', '未知错误')}",
            )
            async with async_session_maker() as short_db:
                chapter_result = await short_db.execute(
                    select(Chapter).where(Chapter.id == chapter_id)
                )
                chapter = chapter_result.scalar_one()
                chapter.status = "failed"
                chapter.error_message = result.get("error", "未知错误")
                await short_db.commit()
            return

        # B-1: 使用短 session 更新 chapter 数据
        story_data = result["data"]
        async with async_session_maker() as short_db:
            chapter_result = await short_db.execute(
                select(Chapter).where(Chapter.id == chapter_id)
            )
            chapter = chapter_result.scalar_one()

            chapter.status = "completed"
            chapter.full_script = json.dumps(story_data, ensure_ascii=False)
            stage_results = story_data.get("stage_results", {})
            summary_data = story_data.get("summary", {})
            chapter.summary = summary_data.get("title", "") if isinstance(summary_data, dict) else str(summary_data)
            chapter.characters_json = json.dumps(
                stage_results.get("characters", {}).get("characters", []), ensure_ascii=False
            )
            chapter.scenes_json = json.dumps(
                stage_results.get("screenplay", {}).get("scenes", []), ensure_ascii=False
            )
            chapter.storyboard_json = json.dumps(
                stage_results.get("storyboard", {}), ensure_ascii=False
            )

            # Update project title if first chapter
            if chapter_number == 1 and story_data.get("title"):
                project_result = await short_db.execute(
                    select(Project).where(Project.id == chapter.project_id)
                )
                project = project_result.scalar_one()
                if project.title == "未命名项目":
                    project.title = story_data["title"]

            await short_db.commit()

        # Update job as completed (短 session)
        # P0-2: stage 必须设成 'completed' 而不是 'story_generation'，
        # 否则前端 STAGE_LABEL["story_generation"] 会让大标题倒退到"正在生成故事大纲"
        # B46: 统计 Stage 5 失败 shot 数量，写入 failed_shot_count / partial_failure
        _failed_shot_count = 0
        _partial_failure = False
        if confirmed_outline:
            # pipeline_result 包含 stage_results.images（image_results 列表）
            try:
                _image_results = story_data.get("stage_results", {}).get("images", [])
                _failed_shot_count = sum(
                    1 for r in _image_results if isinstance(r, dict) and not r.get("success", True)
                )
                _partial_failure = _failed_shot_count > 0
                if _partial_failure:
                    logger.info(
                        f"[JobManager] B46: partial_failure=True, "
                        f"failed_shot_count={_failed_shot_count}/{len(_image_results)}"
                    )
            except Exception as _b46_e:
                logger.warning(f"[JobManager] B46: failed_shot_count 统计失败（非阻塞）: {_b46_e}")

        task_elapsed = time.time() - task_start
        logger.info(f"[JobManager] ✅ 生成任务完成 (总耗时 {task_elapsed:.1f}s)")
        await _update_job_short_session(
            job_id,
            status="completed",
            stage="completed",
            progress=100,
            message="故事生成完成！",
            failed_shot_count=_failed_shot_count,
            partial_failure=_partial_failure,
        )

    except Exception as e:
        task_elapsed = time.time() - task_start
        logger.error(f"[JobManager] ❌ 系统异常 (耗时 {task_elapsed:.1f}s): {e}")
        # B-1: 异常处理也用短 session
        await _update_job_short_session(
            job_id,
            status="failed",
            progress=0,
            message=f"系统错误: {str(e)}",
        )
        try:
            async with async_session_maker() as short_db:
                chapter_result = await short_db.execute(
                    select(Chapter).where(Chapter.id == chapter_id)
                )
                chapter = chapter_result.scalar_one_or_none()
                if chapter:
                    chapter.status = "failed"
                    chapter.error_message = str(e)
                    await short_db.commit()
        except Exception:
            pass  # 防止异常处理中再次失败导致未处理异常
