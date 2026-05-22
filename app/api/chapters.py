"""Chapters API"""

import json
import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("xuhua")
from app.database import get_db
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.job import GenerationJob
from app.models.scene_image import SceneImage
from app.schemas.chapter import ChapterStatus, ChapterStory, ChapterResponse, HydrateHints
from app.api.projects import verify_user
from app.services.pipeline_orchestrator import estimate_remaining
from app.services.job_manager import calculate_eta_remaining_sec as _calculate_eta_with_progress

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


def _is_storyboard_truly_ready(chapter) -> bool:
    """Wave 10 / RISK-T16-5: storyboard_json 必须非空 + 含 shots > 0。

    旧逻辑 bool(chapter.storyboard_json) 在 storyboard_json="{}" 时误判为 True，
    导致前端提前进入 /preview 但数据为空。
    """
    if not chapter.storyboard_json:
        return False
    try:
        sb = json.loads(chapter.storyboard_json)
        shots = sb.get("shots", [])
        return len(shots) > 0
    except (TypeError, ValueError):
        return False


# ===========================================================================
# Wave 9 / DEC-030: ui_phase + hydrate_hints 派生 helpers
# T21-NEW-7 (2026-05-21 DEC-047 v1.4): 新增 scene_references_review (R4-3 闸门)
# ===========================================================================
#
# 设计原则:
#   - backend status response 是 frontend state 的 single source of truth
#   - frontend createUrl / subPhase / hydrate URL 全部从 ui_phase + hydrate_hints 派生
#   - 不再依赖 user click handler 触发本地缓存切换（顺解 RISK-T15-8）
#
# ui_phase 8 状态机 (T22-NEW-5 v1.5): scene_review 已移除 (R4-2 wait loop 移除)
#   input                    — 尚无 job 或 status='pending'，等大纲生成
#   outline_review           — 大纲已生成，用户在 StageB 确认（job 未启动）
#   char_review_pending      — Pipeline 正在 Stage 1/2 跑（角色还没生成完）
#   char_review              — Stage 2 完成，R4-1 等用户确认角色（character_ready stage）
#   scene_review_pending     — Pipeline 正在 Stage 3 跑（场景还在生成）
#   [scene_review REMOVED]   — T22-NEW-5: Founder 5/22 决策，R4-2 确认环节砍掉，Stage 3→4 直连
#   storyboard_running       — Stage 4 在跑分镜（Stage 3 完成后直接进入）
#   scene_references_review  — Stage 4.5 完成, R4-3 等用户确认场景参考图 (T21-NEW-7 DEC-047)
#   shot_generating          — Stage 5 + image_preparation + bgm（最终图像生成）
#   completed                — Pipeline 跑完，用户进 /preview


def _derive_ui_phase(
    job: GenerationJob | None,
    project: Project,
    chapter: Chapter,
) -> str:
    """Wave 9 / DEC-030: 从 backend authoritative state 派生 ui_phase。

    T22-NEW-5 (v1.5): scene_review 已移除，scenes_ready stage → 直接 storyboard_running。
    完整状态机（见模块顶部注释）— frontend 用此字段决定 createUrl / subPhase。
    """
    # ---- 1. 无 job 或 pending: 看是否有大纲 ----
    if job is None or job.status == "pending" or job.status == "queued":
        # 无 confirmed_outline → 用户还在输入或大纲生成中
        # 有 confirmed_outline → 用户已确认大纲，等 job 启动
        if project.confirmed_outline_json:
            return "outline_review"  # 大纲已确认但 job 还没真启动
        if project.raw_outline_json:
            return "outline_review"  # 大纲生成完等用户在 StageB 确认
        return "input"

    # ---- 2. 终态 ----
    if job.current_stage == "completed" or job.status == "completed":
        return "completed"

    if job.status == "failed":
        # 失败状态保持 stage 派生（frontend 显示错误页）
        # 但 ui_phase 仍然反映 last_stage 让前端知道在哪步失败
        pass

    stage = job.current_stage or ""

    # ---- 3. R4-1 闸门: character_ready ----
    # 此 stage 是 Pipeline 等用户确认角色的稳态
    if stage == "character_ready":
        if project.characters_confirmed:
            # 用户已确认但 Pipeline 还没切到下一个 stage（瞬态）
            # 走入 scene_review_pending（Stage 3 即将启动）
            return "scene_review_pending"
        return "char_review"

    # ---- 4. Stage 1/2: 角色还在生成 ----
    if stage in ("story_generation", "character_design"):
        return "char_review_pending"

    # ---- 5. scenes_ready stage (T22-NEW-5: scene_review REMOVED) ----
    # R4-2 wait loop 已移除 (Founder 5/22 决策), Stage 3 完成后 Pipeline 直接进 Stage 4.
    # scenes_ready 是一个极短暂的过渡 stage，直接映射到 storyboard_running.
    # scenes_confirmed DB 列保留（向后兼容），运行时不再使用作为等待信号.
    if stage == "scenes_ready":
        return "storyboard_running"

    # ---- 6. Stage 3: 场景还在生成 ----
    if stage == "screenplay":
        return "scene_review_pending"

    # ---- 7. Stage 4: 分镜跑中 ----
    if stage == "storyboard":
        return "storyboard_running"

    # ---- 7.5. Stage 4.5: 场景参考图生成中/完成等用户确认 (T21-NEW-7 DEC-047 R4-3) ----
    if stage == "scene_image_preparation":
        # Stage 4.5 跑中 (LLM/Seedream 生成 interior+exterior anchor)
        # 与 storyboard_running 复用 UI (frontend 显示"正在准备场景..."进度条)
        return "storyboard_running"

    if stage == "scene_references_ready":
        # Stage 4.5 完成, R4-3 等用户确认场景参考图
        if getattr(project, "scene_references_confirmed", False):
            return "shot_generating"  # 用户已确认 → 即将进 Stage 5 (瞬态)
        return "scene_references_review"

    # ---- 8. Stage 5: 图像生成 ----
    if stage in ("image_preparation", "image_generation", "bgm"):
        return "shot_generating"

    # ---- Fallback: 未知 stage ----
    logger.warning(
        f"[_derive_ui_phase] Unknown stage={stage!r}, fallback to char_review_pending"
    )
    return "char_review_pending"


# ===========================================================================
# RISK-T20-9.v3 (2026-05-19): ETA 全局重审 — 基于真实 shots_total / shots_completed
# ===========================================================================
#
# Founder 5/19 16:08 反馈核心问题:
#   1. test17 v2 实测 progress=84% 但 Shot 14/20 才开始 — 真实 ~70%, ETA 严重失真
#   2. 前后端 ETA 脱节, "前端在自说自话"
#   3. progress >= 95% 显示"即将完成"无具体 ETA — 终态 UX 灾难
#   4. Stage 5 + Stage 6 BGM (~3min) + 后处理 (~30s) 必须算入剩余时间
#
# v3 核心改进 (基于 T20-13 已加的 shots_total/completed/failed 真字段):
#   - image_generation stage 优先用 (shots_total - shots_completed) * 80 / max_concurrent
#     比 progress 反推更精 (progress 受 stage_progress mapping 影响, shots_completed 直读 mid-stage 计数)
#   - bgm + 后处理 baseline (120s + 30s) 全部累积到 image_generation 阶段的 ETA
#   - completed → 0 (不变)
#   - 其他 stage 走原逻辑 (T20-9 旧 chain: job.estimated_seconds → calculate_eta_with_progress → estimate_remaining)
#
# 单调性 (避免前端"自说自话"):
#   - v3 ETA 必须 <= job.estimated_seconds (progress_callback 已写入 monotonic guard 值)
#   - 当 v3 更激进的减少时, 信 v3 (Founder 反馈 ETA 偏快 = 慢, 偏慢 = 快 — 真实数据接管)
#   - 当 v3 比 job.estimated_seconds 大时 — 这种情况几乎不发生 (shots 进展比 progress 表示得真实)
#
# Universal: 任何 shot count (5/19/29/50) / 任何 max_concurrent (1/3/6) 都准确
#
# 不破坏向后兼容:
#   - 早期 stage (shots_total=None) → 走原逻辑, 行为完全不变
#   - bgm / completed 仍是已有路径
#   - schema 字段不变 (estimated_remaining_seconds 字段语义不变, 算法升级)

# v3 baseline 常量 — 保持与 pipeline_orchestrator.build_stage_durations 同步
_V3_PER_SHOT_SECONDS: int = 80  # 实测平均 (含 long-tail), 与 T20-9 baseline 同源
_V3_BGM_BASELINE_SECONDS: int = 120  # bgm stage 总耗时 (与 STAGE_DURATIONS["bgm"] 同步)
_V3_POSTPROCESS_BASELINE_SECONDS: int = 30  # finalize / write json / cleanup
_V3_TERMINAL_PHASE_MIN_ETA: int = 5  # progress >= 95% 时仍显具体数 (Founder 4 P0 要求)


def _compute_v3_eta(
    job: GenerationJob,
    shots_total: int | None,
    shots_completed: int | None,
    max_concurrent: int,
    legacy_eta: int | None,
) -> int | None:
    """RISK-T20-9.v3: 基于真实 shots_total / shots_completed 计算 ETA.

    Args:
        job: GenerationJob (拿 current_stage / progress)
        shots_total: T20-13 已派生 — None 表示 storyboard 没生成
        shots_completed: T20-13 已派生 — None 同上
        max_concurrent: settings.IMAGE_MAX_CONCURRENT
        legacy_eta: 原 ETA chain 计算出的值 (job.estimated_seconds 或 fallback)

    Returns:
        v3 ETA 秒数, None 表示走 legacy_eta 不覆盖.

    设计:
        - completed → 0 (Founder 4 要求: "completed=true 才显故事生成完成")
        - shots_total=None → 早期 stage, 不接管, 返 None
        - image_generation/bgm → v3 真实计算
        - 其他 stage (storyboard/screenplay/character_design 等) → 返 None 走原逻辑
        - v3 ETA <= legacy_eta (单调性 guard, 避免忽涨忽跌)
    """
    if job is None:
        return None

    stage = job.current_stage or ""

    # ---- 终态 ----
    if stage == "completed":
        return 0

    # ---- 没有 shots_total → 早期 stage, v3 不接管 ----
    if shots_total is None or shots_total <= 0:
        return None

    # ---- shots_completed 兜底 (T20-13 已保证 image_generation 阶段非 None) ----
    _done = shots_completed if shots_completed is not None else 0
    _done = max(0, min(_done, shots_total))

    # ---- v3 image_generation: 真实剩余 shots * per_shot * concurrent_factor ----
    if stage == "image_generation":
        remaining_shots = shots_total - _done
        per_shot = _V3_PER_SHOT_SECONDS
        conc = max(max_concurrent, 1)
        image_gen_remaining = int(remaining_shots * per_shot / conc)

        # 跨 stage 累积: image_generation 之后还有 bgm + finalize
        total = image_gen_remaining + _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS

        # 终态保底: progress >= 95% 仍显具体 ETA (Founder 反馈 "78% → 即将完成 → 没数字")
        # 这里 v3 自然能给出真实 ETA, 但若 remaining_shots=0 且仍在 image_generation, 给 BGM baseline
        if total <= 0:
            total = _V3_TERMINAL_PHASE_MIN_ETA

        # Founder 5/19 16:08 反馈: legacy progress-based ETA "偏快" (progress=84% 但实际 13/19),
        # 当 v3 真实数据比 legacy 大时, v3 必须接管 (这正是 Founder 反馈的核心问题).
        # 不再用 1.5× legacy cap — 让真实 shots_completed 数据完全接管 image_generation ETA.
        # legacy 仍作为 None 兜底 (当 v3 算不出时), 但 v3 算出后无视 legacy 上限.
        return max(total, _V3_TERMINAL_PHASE_MIN_ETA)

    # ---- v3 bgm: bgm baseline + finalize ----
    if stage == "bgm":
        # bgm stage 内进度: (job.progress - 92) / (100-92) — 简化用 job.estimated_seconds 反馈
        # 或直接给 bgm baseline + finalize, 让 progress_callback 写入的 ETA 接管细节
        bgm_remaining = _V3_BGM_BASELINE_SECONDS
        # 用 stage 内 progress 折扣
        _prog = int(job.progress or 92)
        if _prog >= 92:
            _stage_frac = max(0.0, min(1.0, (_prog - 92) / 8.0))
            bgm_remaining = max(int(_V3_BGM_BASELINE_SECONDS * (1.0 - _stage_frac)), 0)
        total = bgm_remaining + _V3_POSTPROCESS_BASELINE_SECONDS
        return max(total, _V3_TERMINAL_PHASE_MIN_ETA)

    # ---- image_preparation: 还没进 image_generation, 全部剩余 ----
    if stage == "image_preparation":
        # 用 baseline: full image_gen + bgm + postprocess
        full_image_gen = int(shots_total * _V3_PER_SHOT_SECONDS / max(max_concurrent, 1))
        # image_preparation 自己也耗时 (剩余部分, 用 legacy_eta 兜底)
        # 简化: legacy_eta 通常已含 image_preparation 剩余, 我们只追加 image_gen 完整 budget
        # 防止与 legacy 双重累积 — 只在 legacy 显著小于纯 image_gen 时接管
        v3_min = full_image_gen + _V3_BGM_BASELINE_SECONDS + _V3_POSTPROCESS_BASELINE_SECONDS
        if legacy_eta is None:
            return v3_min
        # 信 legacy (它已含 image_preparation 剩余), 但保底不低于 v3_min
        return max(legacy_eta, v3_min)

    # ---- 其他 stage (storyboard / screenplay / character_design / story_generation) ----
    # v3 不接管, 返 None 走原 chain
    return None


def _build_hydrate_hints(
    ui_phase: str,
    chapter_number: int,
) -> HydrateHints | None:
    """Wave 9 / DEC-030: 根据 ui_phase 返回 frontend 应 hydrate 哪个 endpoint。

    T22-NEW-5 (v1.5): scene_review phase 已移除，scene_review hydrate 分支删除.
    """
    base = f"/api/projects/{{project_id}}/chapters/{chapter_number}"

    if ui_phase == "char_review":
        # frontend /characters 页面 hydrate
        return HydrateHints(
            endpoint=f"{base}/characters",
            display_field="characters",
            expected_data_shape="list[Character]",
        )

    # T22-NEW-5: scene_review hydrate 分支已移除
    # (scene_review ui_phase 不再存在，scenes_ready stage 直接 → storyboard_running)

    if ui_phase == "scene_references_review":
        # T21-NEW-7 DEC-047: frontend /scenes 页面 hydrate (镜像 characters 模式)
        # 显示场景参考图卡片 (interior + exterior) + 编辑 + 重生 + 60s 倒计时
        return HydrateHints(
            endpoint=f"{base}/scene-references",
            display_field="scene_references",
            expected_data_shape="list[SceneReference]",
        )

    if ui_phase in ("shot_generating", "completed"):
        # frontend /preview 页面 hydrate
        return HydrateHints(
            endpoint=f"{base}/storyboard",
            display_field="shots",
            expected_data_shape="list[Shot]",
        )

    # input / outline_review / *_pending / storyboard_running 阶段
    # frontend 等 stage 推进，无需 hydrate 内容数据
    return None


def serialize_chapter_response(chapter: Chapter, project_uuid: str) -> ChapterResponse:
    return ChapterResponse(
        id=chapter.uuid,
        project_id=project_uuid,
        chapter_number=chapter.chapter_number,
        status=chapter.status,
        created_at=chapter.created_at,
        updated_at=chapter.updated_at,
    )


# Pydantic models for image generation
class ImageGenerationResponse(BaseModel):
    """图像生成启动响应"""
    job_id: str
    status: str
    message: str
    total_scenes: int


class ChapterImagesResponse(BaseModel):
    """章节图像列表响应"""
    images: list
    total: int
    completed: int
    failed: int


class RegenerateRequest(BaseModel):
    """重新生成请求"""
    prompt_override: Optional[str] = None


@router.get("/", response_model=list[ChapterResponse])
async def list_chapters(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chapters for a project"""
    try:
        # Verify project ownership
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == project.id)
            .order_by(Chapter.chapter_number)
        )
        chapters = result.scalars().all()
        return [serialize_chapter_response(c, project.uuid) for c in chapters]
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/list] unhandled error project={project_id}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}/status", response_model=ChapterStatus)
async def get_generation_status(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Query generation status (for frontend polling)
    """
    try:
        # Verify project ownership
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # Get chapter
        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id,
                Chapter.chapter_number == chapter_number,
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # Get latest job
        job_result = await db.execute(
            select(GenerationJob)
            .where(GenerationJob.chapter_id == chapter.id)
            .order_by(GenerationJob.created_at.desc())
            .limit(1)
        )
        job = job_result.scalar_one_or_none()

        if not job:
            # Wave 9 / DEC-030: 即使无 job 也派生 ui_phase（input / outline_review）
            _no_job_ui_phase = _derive_ui_phase(None, project, chapter)
            _no_job_hints = _build_hydrate_hints(_no_job_ui_phase, chapter_number)
            return ChapterStatus(
                status=chapter.status,
                stage=None,
                progress=0,
                estimated_remaining_seconds=None,
                message="暂无生成任务",
                ui_phase=_no_job_ui_phase,
                hydrate_hints=_no_job_hints,
                characters_confirmed=bool(getattr(project, "characters_confirmed", False)),
                scenes_confirmed=bool(getattr(project, "scenes_confirmed", False)),
                # T21-NEW-7 v1.4: scene_references R4-3 字段
                scene_references_ready=bool(getattr(chapter, "scene_references_json", None)),
                scene_references_confirmed=bool(getattr(project, "scene_references_confirmed", False)),
                storyboard_ready=_is_storyboard_truly_ready(chapter),
                outline_ready=bool(chapter.full_script or chapter.scenes_json),
            )

        # P1-2 + BUG-ETA-DISAPPEAR-AT-STAGE-EDGE (Wave 6 / 2026-05-11):
        # 优先使用 job.estimated_seconds（progress_callback 已写入 stage-aware ETA + 单调 guard）
        # fallback 到 calculate_eta_remaining_sec(stage, real_progress) — 用真实 global progress
        # 自动转 stage-internal progress（不再 hardcoded 0.5）
        #
        # RISK-T20-9 (2026-05-18): chapters.py fallback 原本 hardcoded `stage_progress=0.5`,
        # 但 stage 实际进度受 global progress (0-100) 控制（_ETA_STAGE_PROGRESS_BOUNDS）。
        # 改用 calculate_eta_remaining_sec() — 自动把 global progress 映射到各 stage 内部 0-1 比例,
        # universal 适配任意 progress 值, 不再"卡死在 stage 中点估算".
        #
        # Round 2 (2026-05-13): fallback 路径真正传入 actual_shot_count / unique_location_count /
        # max_concurrent，不再使用 default 值（default 等于静态 ETA，dynamic 完全失效）。
        actual_shot_count: int = 18           # default fallback
        unique_location_count: int = 2         # default fallback
        try:
            if chapter.storyboard_json:
                _sb = json.loads(chapter.storyboard_json)
                _shots = _sb.get("shots", [])
                if _shots:
                    actual_shot_count = len(_shots)
        except Exception:
            pass  # fallback 到 18

        try:
            # 优先用 confirmed_outline，fallback 到 raw_outline
            _outline_json = getattr(project, "confirmed_outline_json", None) or \
                            getattr(project, "raw_outline_json", None)
            if _outline_json:
                _outline = json.loads(_outline_json)
                _locs = _outline.get("unique_locations", [])
                if _locs:
                    unique_location_count = len(_locs)
        except Exception:
            pass  # fallback 到 2

        try:
            from app.config import settings as _settings
            max_concurrent = _settings.IMAGE_MAX_CONCURRENT
        except Exception:
            max_concurrent = 3

        if job.current_stage == "completed":
            estimated_remaining = 0
        elif job.estimated_seconds is not None and job.estimated_seconds >= 0:
            # 优先用 progress_callback 写入的最新 ETA（已含单调递减 guard）
            estimated_remaining = int(job.estimated_seconds)
        elif job.current_stage:
            # RISK-T20-9: 改用 calculate_eta_remaining_sec()，自动 global→stage-internal progress 转换
            try:
                _eta_val = _calculate_eta_with_progress(
                    stage=job.current_stage,
                    progress=int(job.progress or 0),
                    actual_shot_count=actual_shot_count,
                    unique_location_count=unique_location_count,
                    max_concurrent=max_concurrent,
                )
                # calculate_eta_remaining_sec 在 unknown stage 时返 None；兜底 estimate_remaining
                if _eta_val is not None:
                    estimated_remaining = _eta_val
                else:
                    estimated_remaining = estimate_remaining(
                        job.current_stage,
                        stage_progress=0.5,
                        actual_shot_count=actual_shot_count,
                        unique_location_count=unique_location_count,
                        max_concurrent=max_concurrent,
                    )
            except Exception as _eta_e:
                logger.warning(f"[chapters/status] T20-9 ETA fallback 计算失败: {_eta_e}")
                estimated_remaining = estimate_remaining(
                    job.current_stage,
                    stage_progress=0.5,
                    actual_shot_count=actual_shot_count,
                    unique_location_count=unique_location_count,
                    max_concurrent=max_concurrent,
                )
        else:
            estimated_remaining = None

        # Wave 9 / DEC-030: backend authoritative state 派生
        _ui_phase = _derive_ui_phase(job, project, chapter)
        _hydrate_hints = _build_hydrate_hints(_ui_phase, chapter_number)

        # Wave 11.3 / T17-5: actual_elapsed_sec — job 已运行秒数（仅 processing 状态）
        # frontend 可用于本地 countdown 修正（实际值 vs backend ETA 的偏差检测）
        _actual_elapsed: int | None = None
        if job and job.started_at and job.status == "processing":
            _actual_elapsed = int((datetime.utcnow() - job.started_at).total_seconds())

        # RISK-T20-9 (2026-05-18): 仅在真实知道 shot_count 时透传字段
        # actual_shot_count 默认 fallback 18 — 但 storyboard_json 没数据时返 null 给 frontend
        # 让 frontend 知道是真实数据 vs fallback default
        _shot_count_for_response: int | None = None
        try:
            if chapter.storyboard_json:
                _sb_resp = json.loads(chapter.storyboard_json)
                _shots_resp = _sb_resp.get("shots", [])
                if _shots_resp:
                    _shot_count_for_response = len(_shots_resp)
        except Exception:
            pass

        # RISK-T20-13 (2026-05-19): 计算 shots_total / shots_completed / shots_failed
        # 设计:
        #   shots_total      = _shot_count_for_response (= actual_shot_count, 复用)
        #   shots_failed     = job.failed_shot_count (DB 直读, T15-9 mid-stage 实时累加)
        #   shots_completed  = stage_message regex 解析 "已生成 X/Y" — pipeline_orchestrator.py
        #                      L1362/L1424 message 格式稳定; 兜底用 progress 反推
        #
        # 兜底层级 (确保始终给 frontend 真实数字, 不丢字段):
        #   1. storyboard 没生成 → 全部 null (早期 stage)
        #   2. stage="completed" → shots_completed = shots_total (all processed)
        #   3. image_generation stage + message 含"已生成 X/Y" → 解析 X
        #   4. image_generation stage 但 message 无规律 → 从 progress 反推 (P1-1 公式: 75+20*done/total)
        #   5. T20-44: bgm / 其他图后 stage → shots_completed = shots_total (保留最终值不重置为 0)
        #   6. 早期 stage (outline/character_design/screenplay/storyboard/image_preparation) → shots_completed = 0
        _shots_total: int | None = _shot_count_for_response
        _shots_failed: int | None = (
            getattr(job, "failed_shot_count", 0) or 0
        ) if _shots_total is not None else None
        _shots_completed: int | None = None
        # T20-44: stages that come AFTER image_generation — shots are all processed
        _POST_IMAGE_GEN_STAGES = {"bgm", "postprocess", "finalize", "completed"}
        # stages that come BEFORE image_generation — shots not yet processed
        _PRE_IMAGE_GEN_STAGES = {
            "outline", "character_design", "screenplay", "storyboard",
            "image_preparation", None,
        }
        if _shots_total is not None:
            if job.current_stage in _POST_IMAGE_GEN_STAGES or job.current_stage == "completed":
                # 完成或图后阶段 → 成功+失败 = total (不重置为 0, T20-44 BGM reset bug)
                _shots_completed = _shots_total
            elif job.current_stage == "image_generation":
                # 优先 regex 解析 message (pipeline_orchestrator L1362/L1424 格式稳定)
                _parsed_done: int | None = None
                _msg = job.stage_message or ""
                _match = re.search(r"已生成\s*(\d+)\s*/\s*\d+", _msg)
                if _match:
                    try:
                        _parsed_done = int(_match.group(1))
                    except ValueError:
                        _parsed_done = None
                if _parsed_done is not None:
                    _shots_completed = min(_parsed_done, _shots_total)
                else:
                    # 兜底: progress 反推 (75 + int(20 * done / total) → done = (progress-75)*total/20)
                    _prog = job.progress or 0
                    if _prog >= 75:
                        _shots_completed = max(
                            0, min(_shots_total, int((_prog - 75) * _shots_total / 20))
                        )
                    else:
                        _shots_completed = 0
            else:
                # 早期 stage (outline/character_design/screenplay/storyboard/image_preparation 等)
                # → 还没到图像生成阶段, shots_completed = 0
                _shots_completed = 0

        # ===================================================================
        # RISK-T20-9.v3 (2026-05-19): 用真实 shots 数据接管 ETA (仅 image_generation+ 阶段)
        # ===================================================================
        # 在原 estimated_remaining (job.estimated_seconds / calculate_eta_with_progress
        # / estimate_remaining 三链) 之后做一次"v3 覆盖":
        #   - image_generation: (shots_total - shots_completed) * 80 / max_concurrent + bgm + postprocess
        #   - bgm: bgm baseline (按 progress 内折扣) + postprocess
        #   - image_preparation: full image_gen budget + bgm + postprocess (保底)
        #   - 其他 stage: 走原值不动
        # 单调性 guard: v3 不能比 legacy 大很多 (内部已防 jump up)
        # 终态保底: progress >= 95% 仍显具体 ETA (Founder 反馈)
        try:
            _v3_eta = _compute_v3_eta(
                job=job,
                shots_total=_shots_total,
                shots_completed=_shots_completed,
                max_concurrent=max_concurrent,
                legacy_eta=estimated_remaining,
            )
            if _v3_eta is not None:
                estimated_remaining = _v3_eta
        except Exception as _v3_e:
            logger.warning(f"[chapters/status] T20-9.v3 ETA 计算失败 (走 legacy): {_v3_e}")

        return ChapterStatus(
            status=job.status,
            stage=job.current_stage,
            progress=job.progress,
            estimated_remaining_seconds=estimated_remaining,
            actual_elapsed_sec=_actual_elapsed,
            message=job.stage_message,
            # B46: 部分失败字段（DB 新列，getattr 兜底防旧数据 AttributeError）
            failed_shot_count=getattr(job, "failed_shot_count", 0) or 0,
            partial_failure=getattr(job, "partial_failure", False) or False,
            # RISK-T20-9: 透传动态 ETA 参数, 让 frontend 本地算 fallback 时 universal
            actual_shot_count=_shot_count_for_response,
            max_concurrent=max_concurrent,
            # RISK-T20-13: Shot 级真实计数字段（frontend 不再 regex 解析 message）
            shots_total=_shots_total,
            shots_completed=_shots_completed,
            shots_failed=_shots_failed,
            # Wave 9 / DEC-030: backend authoritative state — frontend 派生用
            ui_phase=_ui_phase,
            hydrate_hints=_hydrate_hints,
            characters_confirmed=bool(getattr(project, "characters_confirmed", False)),
            scenes_confirmed=bool(getattr(project, "scenes_confirmed", False)),
            # T21-NEW-7 v1.4 DEC-047: scene_references R4-3 配套
            scene_references_ready=bool(getattr(chapter, "scene_references_json", None)),
            scene_references_confirmed=bool(getattr(project, "scene_references_confirmed", False)),
            storyboard_ready=_is_storyboard_truly_ready(chapter),
            outline_ready=bool(chapter.full_script or chapter.scenes_json),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/status] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}/story", response_model=ChapterStory)
async def get_chapter_story(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get generated story content
    """
    try:
        # Verify project ownership
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # Get chapter
        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # RISK-T18-G fix (Wave 11.2, 2026-05-14):
        #   - 原逻辑: pending / generating_story 无数据时 → 404
        #   - 问题: frontend 在 character_ready / 早期阶段轮询 /story 产生 41 次 404 风暴
        #     → client.log [WARN] HTTP_ERROR status=404 噪音 + frontend 误判连接问题
        #   - 修复: 无数据时改返 200 + 空结构（scenes=[], characters=[]），
        #     不再产生 404。frontend 已有 empty-guard（length==0 不渲染）
        #   - 保留: project/chapter 不存在 → 404，failed → 400（真错误）
        #
        # RISK-T15-3 fix (Wave 9 / DEC-030, 2026-05-13):
        #   - R4-2 阶段 chapter.status 仍是 "generating_story" 但 scenes_json 已写入
        #     → 优先检查 scenes_json 非空，有数据则直接返 200 + scenes

        if chapter.status == "failed":
            raise HTTPException(
                status_code=400,
                detail=f"故事生成失败: {chapter.error_message or '未知错误'}",
            )

        # RISK-T15-3 + RISK-T14-7: 一旦 scenes_json 写入即可返回（Stage 3 done，无需等 Stage 5）。
        # 在 generating_story 状态检查之前判断 — 让 R4-2 阶段 frontend hydrate /story 真返回 scenes 数据。
        if not chapter.scenes_json and not chapter.full_script:
            # RISK-T18-G: 数据尚未写入 → 200 + 空结构（取代旧 404，消除 client 404 风暴）
            logger.debug(
                f"[chapters/story] T18-G: no data yet, returning empty (status={chapter.status})"
            )
            return ChapterStory(
                title="",
                summary="",
                full_script={},
                scenes=[],
                characters=[],
            )

        # Parse stored JSON
        try:
            scenes = json.loads(chapter.scenes_json) if chapter.scenes_json else []
            characters = (
                json.loads(chapter.characters_json) if chapter.characters_json else []
            )
            # full_script may not be written yet (only available after Stage 5).
            # Use a minimal stub if not available yet, with scenes embedded.
            if chapter.full_script:
                full_script = json.loads(chapter.full_script)
            else:
                # Stage 3 done but Stage 5 not yet — build minimal full_script from scenes
                full_script = {
                    "title": chapter.summary or "故事生成中",
                    "scenes": scenes,
                }
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"数据解析错误: {str(e)}")

        return ChapterStory(
            title=full_script.get("title", "未命名"),
            summary=chapter.summary or "",
            full_script=full_script,
            scenes=scenes,
            characters=characters,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/story] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Get basic chapter info"""
    try:
        # Verify project ownership
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        return serialize_chapter_response(chapter, project.uuid)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/get] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}/storyboard")
async def get_chapter_storyboard(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """BE-4: 获取章节分镜数据（storyboard_json）

    B44: 每个 shot 包含以下字段（失败 shot 才有后三个）：
      - shot_id: int
      - image_url: str | null
      - success: bool（如果 image_url 为 null 则为 False）
      - error: str（失败原因）
      - error_kind: str（如 "content_safety_failure"）
      - safety_advice: {
          suspected_terms: list[str],
          suggested_changes: [{original: str, suggestion: str}],
          user_message: str
        }

    safety_advice 由 pipeline Stage 5 SafetyAdvisor 写入 storyboard_json。
    若 storyboard_json 中某 shot 缺少 safety_advice，会从 5_image_results.json 补充（兜底）。
    """
    import os as _os
    try:
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()
        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        if not chapter.storyboard_json:
            # RISK-T18-G fix (Wave 11.2, 2026-05-14): 返 200 + 空结构，取代 404，消除 client 404 风暴。
            # frontend hydrate storyboard 有 empty guard（shots.length==0 不渲染）
            logger.debug(
                f"[chapters/storyboard] T18-G: storyboard_json empty, returning empty (status={chapter.status})"
            )
            return {"storyboard": {"shots": []}, "chapter_number": chapter_number, "project_id": project_id}

        storyboard = json.loads(chapter.storyboard_json)

        # B44: 从 5_image_results.json 补充 safety_advice（兜底 — pipeline 已写但未回写 storyboard 的旧数据）
        try:
            _results_path = _os.path.join(".", "output", project_id, "5_image_results.json")
            if _os.path.exists(_results_path):
                with open(_results_path, encoding="utf-8") as _f:
                    _image_results: list = json.load(_f)
                # 建 shot_id → result 映射
                _results_map: dict = {r.get("shot_id"): r for r in _image_results if isinstance(r, dict)}
                for shot in storyboard.get("shots", []):
                    _sid = shot.get("shot_id")
                    _ir = _results_map.get(_sid)
                    if not _ir:
                        continue
                    # 仅补充缺失字段，不覆盖已有字段
                    if "success" not in shot:
                        shot["success"] = _ir.get("success", True)
                    if "error" not in shot and _ir.get("error"):
                        shot["error"] = _ir["error"]
                    if "error_kind" not in shot and _ir.get("error_kind"):
                        shot["error_kind"] = _ir["error_kind"]
                    if "safety_advice" not in shot and _ir.get("safety_advice"):
                        shot["safety_advice"] = _ir["safety_advice"]
        except Exception as _merge_e:
            # 非阻塞：5_image_results.json 合并失败不影响主返回
            logger.warning(f"[chapters/storyboard] B44 safety_advice merge 失败（非阻塞）: {_merge_e}")

        return {"storyboard": storyboard, "chapter_number": chapter_number, "project_id": project_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/storyboard] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


# ============ Phase 2: 图像生成端点 ============

@router.post("/{chapter_number}/generate-images", response_model=ImageGenerationResponse)
async def generate_chapter_images(
    project_id: str,
    chapter_number: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    为章节生成所有分镜图像

    前置条件：章节故事已生成完成
    """
    # 1. 验证项目所有权
    project_result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
        )
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 3. 检查章节状态 - 必须有故事内容
    valid_statuses = ["generating_images", "images_ready", "completed"]
    story_ready_statuses = ["story_ready", "confirmed", "generating_images", "images_ready", "completed"]

    # 如果状态是 generating_story 或之后的状态，检查是否有故事内容
    if not chapter.scenes_json or not chapter.characters_json:
        raise HTTPException(
            status_code=400,
            detail="故事尚未生成完成，请先等待故事生成"
        )

    # 解析场景数据
    try:
        scenes = json.loads(chapter.scenes_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="场景数据解析失败")

    if not scenes:
        raise HTTPException(status_code=400, detail="没有可生成图像的场景")

    # 4. 创建图像生成任务
    job = GenerationJob(
        chapter_id=chapter.id,
        status="queued",
        current_stage="image_generation",
        progress=0,
        stage_message="图像生成任务已创建，等待开始...",
        created_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()
    job_id = job.id

    # 更新章节状态
    chapter.status = "generating_images"
    chapter.updated_at = datetime.utcnow()

    await db.commit()

    # 5. 启动后台任务
    background_tasks.add_task(
        generate_images_task,
        job_id=job_id,
        chapter_id=chapter.id,
        project_id=project.id,
        style_preset=project.style_preset
    )

    return ImageGenerationResponse(
        job_id=job.uuid,
        status="generating_images",
        message="图像生成已开始",
        total_scenes=len(scenes)
    )


@router.get("/{chapter_number}/images", response_model=ChapterImagesResponse)
async def get_chapter_images(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节的所有分镜图像
    """
    try:
        # 1. 验证项目
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取章节
        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 3. 获取所有活跃的场景图像
        images_result = await db.execute(
            select(SceneImage)
            .where(SceneImage.chapter_id == chapter.id, SceneImage.is_active == True)
            .order_by(SceneImage.scene_id)
        )
        scene_images = images_result.scalars().all()

        # 4. 构建响应
        images = []
        completed = 0
        failed = 0

        for img in scene_images:
            image_data = {
                "scene_id": img.scene_id,
                "image_url": f"/api/images/{img.image_path}" if img.image_path else None,
                "thumbnail_url": f"/api/images/{img.thumbnail_path}" if img.thumbnail_path else None,
                "prompt": img.image_prompt,
                "status": "completed" if img.image_path and not img.error_message else "failed",
                "width": img.width,
                "height": img.height,
                "aspect_ratio": img.aspect_ratio,
                "model_used": img.generation_model,
                "error": img.error_message
            }
            images.append(image_data)

            if img.image_path and not img.error_message:
                completed += 1
            elif img.error_message:
                failed += 1

        # 获取总场景数
        total_scenes = 0
        if chapter.scenes_json:
            try:
                scenes = json.loads(chapter.scenes_json)
                total_scenes = len(scenes)
            except json.JSONDecodeError:
                pass

        return ChapterImagesResponse(
            images=images,
            total=total_scenes,
            completed=completed,
            failed=failed
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/images] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.post("/{chapter_number}/images/{scene_id}/regenerate")
async def regenerate_scene_image(
    project_id: str,
    chapter_number: int,
    scene_id: int,
    background_tasks: BackgroundTasks,
    request: RegenerateRequest = None,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    重新生成单个场景的图像

    用于用户对某张图不满意时重新生成
    """
    # 1. 验证项目
    project_result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
        )
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 3. 验证场景存在
    if not chapter.scenes_json:
        raise HTTPException(status_code=400, detail="章节没有场景数据")

    try:
        scenes = json.loads(chapter.scenes_json)
        scene_exists = any(s.get("scene_id") == scene_id for s in scenes)
        if not scene_exists:
            raise HTTPException(status_code=404, detail=f"场景 {scene_id} 不存在")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="场景数据解析失败")

    # 4. 将旧图像标记为非活跃
    await db.execute(
        SceneImage.__table__.update()
        .where(SceneImage.chapter_id == chapter.id, SceneImage.scene_id == scene_id)
        .values(is_active=False)
    )
    await db.commit()

    # 5. 启动重新生成任务
    prompt_override = request.prompt_override if request else None

    background_tasks.add_task(
        regenerate_single_image_task,
        chapter_id=chapter.id,
        project_id=project.id,
        scene_id=scene_id,
        style_preset=project.style_preset,
        prompt_override=prompt_override
    )

    return {
        "status": "regenerating",
        "message": f"场景 {scene_id} 正在重新生成",
        "scene_id": scene_id
    }


# ============ 后台任务函数 ============

async def generate_images_task(
    job_id: int,
    chapter_id: int,
    project_id: int,
    style_preset: str
):
    """
    图像生成后台任务

    TASK-P0P1-LOGGING-FIX (2026-04-23):
    - asyncio.CancelledError 单独处理（用户取消不算 failed）
    - Exception 用 logger.exception 输出完整 traceback 到日志
    - 错误信息写入 job.stage_message + chapter.error_message（含 traceback 摘要）
    """
    from app.database import async_session_maker
    from app.services.storyboard_service import StoryboardService
    from app.services.image_generator import ImageGenerator, CharacterConsistencyManager
    from app.services.image_storage import ImageStorageService
    from app.config import settings

    async with async_session_maker() as db:
        try:
            # 1. 更新状态
            job = await db.get(GenerationJob, job_id)
            if job:
                job.status = "processing"
                job.progress = 5
                job.stage_message = "正在加载章节数据..."
                job.started_at = datetime.utcnow()
                await db.commit()

            # 2. 加载章节数据
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                raise Exception("章节不存在")

            scenes = json.loads(chapter.scenes_json)
            characters = json.loads(chapter.characters_json)

            # 3. 生成分镜决策
            if job:
                job.progress = 10
                job.stage_message = "正在生成分镜决策..."
                await db.commit()

            storyboard_service = StoryboardService()
            storyboard = await storyboard_service.generate_storyboard(
                scenes=scenes,
                characters=characters,
                style_preset=style_preset
            )

            # 4. 初始化图像生成器和存储
            image_generator = ImageGenerator()
            storage = ImageStorageService(settings.IMAGE_STORAGE_PATH)

            # 5. 生成角色参考图（可选，用于一致性）
            if job:
                job.progress = 15
                job.stage_message = "正在准备角色参考..."
                await db.commit()

            # consistency_manager = CharacterConsistencyManager(image_generator, storage)
            # char_references = await consistency_manager.get_character_references(
            #     project_id=project_id,
            #     characters=characters,
            #     style_preset=style_preset
            # )

            # 6. 逐个生成场景图像
            total_scenes = len(storyboard)
            for i, scene_board in enumerate(storyboard):
                progress = 20 + int((i / total_scenes) * 75)

                if job:
                    job.progress = progress
                    job.stage_message = f"正在生成第 {i+1}/{total_scenes} 张图片..."
                    await db.commit()

                # 生成图像
                result = await image_generator.generate_image(
                    prompt=scene_board["image_prompt"],
                    negative_prompt=scene_board.get("negative_prompt", ""),
                    aspect_ratio=scene_board.get("aspect_ratio", "2:3"),
                    # reference_images=list(char_references.values()) if char_references else None,
                    style_preset=style_preset
                )

                # 保存结果
                if result["success"]:
                    # 保存图像文件
                    saved = await storage.save_image(
                        image_data=result["image_data"],
                        project_id=project_id,
                        chapter_id=chapter_id,
                        scene_id=scene_board["scene_id"]
                    )

                    # 保存到数据库
                    scene_image = SceneImage(
                        chapter_id=chapter_id,
                        scene_id=scene_board["scene_id"],
                        image_prompt=scene_board["image_prompt"],
                        style_prompt=scene_board.get("style_prompt", ""),
                        negative_prompt=scene_board.get("negative_prompt", ""),
                        image_path=saved["image_path"],
                        thumbnail_path=saved["thumbnail_path"],
                        width=saved["width"],
                        height=saved["height"],
                        aspect_ratio=scene_board.get("aspect_ratio", "2:3"),
                        generation_model=result.get("model_used", ""),
                        generation_time_seconds=int(result.get("generation_time_seconds", 0)),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                else:
                    # 记录失败
                    scene_image = SceneImage(
                        chapter_id=chapter_id,
                        scene_id=scene_board["scene_id"],
                        image_prompt=scene_board["image_prompt"],
                        image_path="",
                        error_message=result.get("error", "Unknown error"),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )

                db.add(scene_image)
                await db.commit()

            # 7. 完成
            if job:
                job.status = "completed"
                job.progress = 100
                job.stage_message = "图像生成完成！"
                job.completed_at = datetime.utcnow()
                await db.commit()

            # 更新章节状态
            chapter.status = "images_ready"
            chapter.updated_at = datetime.utcnow()
            await db.commit()

        except asyncio.CancelledError:
            # 用户主动取消，不算错误；让协程正常终止
            logger.info(
                f"[generate_images_task] task cancelled job_id={job_id} chapter_id={chapter_id}"
            )
            raise
        except Exception as e:
            import traceback as _tb
            error_tb = _tb.format_exc()
            logger.exception(
                f"[generate_images_task] 后台任务异常 job_id={job_id} chapter_id={chapter_id}: {e}"
            )
            if job:
                job.status = "failed"
                job.stage_message = f"图像生成失败: {type(e).__name__}: {str(e)[:400]}"
                job.completed_at = datetime.utcnow()
                await db.commit()

            chapter = await db.get(Chapter, chapter_id)
            if chapter:
                chapter.error_message = error_tb[:10000]
                chapter.status = "failed"
                await db.commit()


async def regenerate_single_image_task(
    chapter_id: int,
    project_id: int,
    scene_id: int,
    style_preset: str,
    prompt_override: str = None
):
    """
    重新生成单个场景图像的后台任务
    """
    from app.database import async_session_maker
    from app.services.storyboard_service import StoryboardService
    from app.services.image_generator import ImageGenerator
    from app.services.image_storage import ImageStorageService
    from app.config import settings

    async with async_session_maker() as db:
        try:
            # 1. 加载章节数据
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                return

            scenes = json.loads(chapter.scenes_json)
            characters = json.loads(chapter.characters_json)

            # 找到目标场景
            target_scene = None
            for scene in scenes:
                if scene.get("scene_id") == scene_id:
                    target_scene = scene
                    break

            if not target_scene:
                return

            # 2. 生成prompt
            if prompt_override:
                image_prompt = prompt_override
                negative_prompt = ""
                aspect_ratio = "2:3"
            else:
                storyboard_service = StoryboardService()
                storyboard = await storyboard_service.generate_storyboard(
                    scenes=[target_scene],
                    characters=characters,
                    style_preset=style_preset
                )
                scene_board = storyboard[0]
                image_prompt = scene_board["image_prompt"]
                negative_prompt = scene_board.get("negative_prompt", "")
                aspect_ratio = scene_board.get("aspect_ratio", "2:3")

            # 3. 生成图像
            image_generator = ImageGenerator()
            result = await image_generator.generate_image(
                prompt=image_prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                style_preset=style_preset
            )

            # 4. 保存结果
            storage = ImageStorageService(settings.IMAGE_STORAGE_PATH)
            if result["success"]:
                saved = await storage.save_image(
                    image_data=result["image_data"],
                    project_id=project_id,
                    chapter_id=chapter_id,
                    scene_id=scene_id
                )
                scene_image = SceneImage(
                    chapter_id=chapter_id,
                    scene_id=scene_id,
                    image_prompt=image_prompt,
                    negative_prompt=negative_prompt,
                    image_path=saved["image_path"],
                    thumbnail_path=saved["thumbnail_path"],
                    width=saved["width"],
                    height=saved["height"],
                    aspect_ratio=aspect_ratio,
                    generation_model=result.get("model_used", ""),
                    generation_time_seconds=int(result.get("generation_time_seconds", 0)),
                    is_active=True,
                    created_at=datetime.utcnow()
                )
            else:
                scene_image = SceneImage(
                    chapter_id=chapter_id,
                    scene_id=scene_id,
                    image_prompt=image_prompt,
                    image_path="",
                    error_message=result.get("error", "Unknown error"),
                    is_active=True,
                    created_at=datetime.utcnow()
                )

            db.add(scene_image)
            await db.commit()

        except asyncio.CancelledError:
            logger.info(
                f"[regenerate_single_image_task] task cancelled chapter_id={chapter_id} scene_id={scene_id}"
            )
            raise
        except Exception as e:
            logger.exception(
                f"[regenerate_single_image_task] 后台任务异常 "
                f"chapter_id={chapter_id} scene_id={scene_id}: {e}"
            )
            # 写一个失败记录到 DB，让 GET /images 能看到 error
            try:
                failed_image = SceneImage(
                    chapter_id=chapter_id,
                    scene_id=scene_id,
                    image_prompt="",
                    image_path="",
                    error_message=f"{type(e).__name__}: {str(e)[:500]}",
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(failed_image)
                await db.commit()
            except Exception as db_e:
                logger.exception(
                    f"[regenerate_single_image_task] failed 记录写 DB 也失败: {db_e}"
                )


# ============ Phase 3: 音频生成和对齐端点 ============

class AudioGenerationRequest(BaseModel):
    """音频生成请求"""
    voice_preset: str = "zh_female_shuangkuai"
    speed_ratio: float = 1.0


class AudioGenerationResponse(BaseModel):
    """音频生成响应"""
    job_id: str
    status: str
    message: str


class ChapterTimelineResponse(BaseModel):
    """章节时间轴响应"""
    timeline: list
    audio_url: Optional[str]
    audio_duration_seconds: Optional[float]
    voice_preset: Optional[str]


@router.post("/{chapter_number}/generate-audio", response_model=AudioGenerationResponse)
async def generate_chapter_audio(
    project_id: str,
    chapter_number: int,
    request: AudioGenerationRequest,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    为章节生成旁白音频并执行音画对齐

    前置条件：
    - 章节故事已生成完成
    - 章节图像已生成完成（可选，但建议有）

    流程：
    1. 提取所有场景的narration文本
    2. 调用TTS合成音频
    3. 调用Whisper获取时间戳
    4. 如果有图像，进行图文匹配
    5. 生成时间轴映射
    """
    # 1. 验证项目所有权
    project_result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
        )
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # 3. 检查章节状态 - 必须有故事内容
    if not chapter.scenes_json:
        raise HTTPException(
            status_code=400,
            detail="故事尚未生成完成，请先等待故事生成"
        )

    # 解析场景数据检查是否有旁白
    try:
        scenes = json.loads(chapter.scenes_json)
        narrations = [s.get("narration", "") for s in scenes if s.get("narration")]
        if not narrations:
            raise HTTPException(status_code=400, detail="场景中没有旁白内容")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="场景数据解析失败")

    # 4. 创建音频生成任务
    job = GenerationJob(
        chapter_id=chapter.id,
        status="queued",
        current_stage="audio_generation",
        progress=0,
        stage_message="音频生成任务已创建，等待开始...",
        created_at=datetime.utcnow(),
    )
    db.add(job)
    await db.flush()
    job_id = job.id

    # 更新章节状态
    chapter.status = "generating_audio"
    chapter.voice_preset = request.voice_preset
    chapter.updated_at = datetime.utcnow()

    await db.commit()

    # 5. 启动后台任务
    background_tasks.add_task(
        generate_audio_and_align_task,
        job_id=job_id,
        chapter_id=chapter.id,
        project_id=project.id,
        voice_preset=request.voice_preset,
        speed_ratio=request.speed_ratio
    )

    return AudioGenerationResponse(
        job_id=job.uuid,
        status="generating_audio",
        message="音频生成已开始"
    )


@router.get("/{chapter_number}/timeline", response_model=ChapterTimelineResponse)
async def get_chapter_timeline(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节的音画时间轴

    返回每个场景对应的时间段和图片
    """
    try:
        # 1. 验证项目
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取章节
        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 3. 检查是否有时间轴数据
        if not chapter.timeline_json:
            raise HTTPException(status_code=400, detail="时间轴尚未生成，请先生成音频")

        # 4. 解析时间轴
        try:
            timeline = json.loads(chapter.timeline_json)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="时间轴数据解析失败")

        # 5. 获取图像信息并补充到时间轴
        images_result = await db.execute(
            select(SceneImage)
            .where(SceneImage.chapter_id == chapter.id, SceneImage.is_active == True)
        )
        scene_images = {img.scene_id: img for img in images_result.scalars().all()}

        for item in timeline:
            scene_id = item.get("scene_id")
            if scene_id in scene_images:
                img = scene_images[scene_id]
                item["image_url"] = f"/api/images/{img.image_path}" if img.image_path else None
                item["thumbnail_url"] = f"/api/images/{img.thumbnail_path}" if img.thumbnail_path else None

        # 6. 构建音频URL
        audio_url = None
        if chapter.audio_path:
            audio_url = f"/api/audio/{project_id}/{chapter.id}/narration.mp3"

        return ChapterTimelineResponse(
            timeline=timeline,
            audio_url=audio_url,
            audio_duration_seconds=chapter.audio_duration_seconds,
            voice_preset=chapter.voice_preset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/timeline] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}/audio")
async def get_chapter_audio_info(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节音频信息
    """
    try:
        # 1. 验证项目
        project_result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 2. 获取章节
        chapter_result = await db.execute(
            select(Chapter).where(
                Chapter.project_id == project.id, Chapter.chapter_number == chapter_number
            )
        )
        chapter = chapter_result.scalar_one_or_none()

        if not chapter:
            raise HTTPException(status_code=404, detail="章节不存在")

        # 3. 返回音频信息
        has_audio = bool(chapter.audio_path)

        return {
            "has_audio": has_audio,
            "audio_url": f"/api/audio/{project_id}/{chapter.id}/narration.mp3" if has_audio else None,
            "audio_duration_seconds": chapter.audio_duration_seconds,
            "voice_preset": chapter.voice_preset,
            "has_timeline": bool(chapter.timeline_json)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/audio] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.get("/{chapter_number}/voices")
async def get_available_voices(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
):
    """
    获取可用的音色列表
    """
    try:
        from app.services.tts_service import TTSService

        tts = TTSService()
        voices = tts.get_available_voices()

        return {
            "voices": voices,
            "default": "zh_female_shuangkuai"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/voices] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


# ============ Phase 3 后台任务 ============

async def generate_audio_and_align_task(
    job_id: int,
    chapter_id: int,
    project_id: int,
    voice_preset: str,
    speed_ratio: float = 1.0
):
    """
    音频生成+对齐后台任务

    步骤：
    1. 加载章节数据
    2. 提取所有narration文本
    3. TTS合成音频
    4. Whisper获取时间戳
    5. 加载场景图片（如果有）
    6. 图文匹配（使用Gemini）
    7. 生成时间轴
    8. 保存结果
    """
    from app.database import async_session_maker
    from app.services.tts_service import TTSService
    from app.services.whisper_service import WhisperService
    from app.services.alignment_service import AlignmentService
    from app.services.audio_storage import AudioStorageService
    from app.config import settings

    async with async_session_maker() as db:
        try:
            # 1. 更新状态
            job = await db.get(GenerationJob, job_id)
            if job:
                job.status = "processing"
                job.progress = 5
                job.stage_message = "正在加载章节数据..."
                job.started_at = datetime.utcnow()
                await db.commit()

            # 2. 加载章节数据
            chapter = await db.get(Chapter, chapter_id)
            if not chapter:
                raise Exception("章节不存在")

            scenes = json.loads(chapter.scenes_json)

            # 3. 提取旁白
            if job:
                job.progress = 10
                job.stage_message = "正在提取旁白文本..."
                await db.commit()

            narrations = [scene.get("narration", "") for scene in scenes]
            narrations = [n for n in narrations if n]  # 过滤空旁白

            if not narrations:
                raise Exception("没有旁白内容")

            # 4. TTS合成
            if job:
                job.progress = 20
                job.stage_message = "正在合成语音..."
                await db.commit()

            tts = TTSService()
            audio_result = await tts.synthesize_chapter(
                narrations=narrations,
                voice_preset=voice_preset,
                speed_ratio=speed_ratio
            )

            if not audio_result["success"]:
                raise Exception(f"TTS合成失败: {audio_result.get('error')}")

            # 5. 保存音频
            if job:
                job.progress = 40
                job.stage_message = "正在保存音频文件..."
                await db.commit()

            audio_storage = AudioStorageService(settings.AUDIO_STORAGE_PATH)
            saved = await audio_storage.save_audio(
                audio_data=audio_result["audio_data"],
                project_id=project_id,
                chapter_id=chapter_id
            )

            # 6. Whisper时间戳
            if job:
                job.progress = 50
                job.stage_message = "正在分析音频时间戳..."
                await db.commit()

            whisper = WhisperService()
            transcript = await whisper.transcribe_with_timestamps(
                audio_path=saved["full_path"],
                granularity="both"
            )

            if not transcript["success"]:
                raise Exception(f"Whisper转录失败: {transcript.get('error')}")

            audio_duration = transcript.get("duration", 0)

            # 7. 加载图片信息（如果有）
            if job:
                job.progress = 60
                job.stage_message = "正在加载场景图片..."
                await db.commit()

            images_result = await db.execute(
                select(SceneImage)
                .where(SceneImage.chapter_id == chapter_id, SceneImage.is_active == True)
                .order_by(SceneImage.scene_id)
            )
            scene_images = images_result.scalars().all()

            # 构建图片信息列表
            images_for_alignment = []
            for img in scene_images:
                if img.image_path:
                    full_path = f"{settings.IMAGE_STORAGE_PATH}/{img.image_path}"
                    images_for_alignment.append({
                        "scene_id": img.scene_id,
                        "path": full_path,
                        "visual_description": img.image_prompt or ""
                    })

            # 8. 图文匹配和对齐
            if job:
                job.progress = 70
                job.stage_message = "正在进行音画对齐..."
                await db.commit()

            alignment = AlignmentService()

            # 获取segments
            segments = transcript.get("segments", [])

            if images_for_alignment:
                # 有图片，使用智能对齐
                timeline = await alignment.align_images_to_audio(
                    images=images_for_alignment,
                    segments=segments,
                    full_text=transcript.get("text", ""),
                    audio_duration=audio_duration,
                    use_visual_matching=False  # 先用文本匹配，节省token
                )
            else:
                # 没有图片，基于场景数量均匀分配
                timeline = await alignment.quick_align(
                    scene_count=len(scenes),
                    segments=segments,
                    audio_duration=audio_duration
                )

            # 9. 保存元数据
            if job:
                job.progress = 85
                job.stage_message = "正在保存结果..."
                await db.commit()

            # 保存转录结果
            await audio_storage.save_metadata(
                project_id=project_id,
                chapter_id=chapter_id,
                metadata={
                    "text": transcript.get("text", ""),
                    "duration": audio_duration,
                    "language": transcript.get("language"),
                    "segments": segments,
                    "words": transcript.get("words", [])
                }
            )

            # 保存时间轴
            await audio_storage.save_timeline(
                project_id=project_id,
                chapter_id=chapter_id,
                timeline=timeline
            )

            # 10. 更新章节数据库记录
            if job:
                job.progress = 95
                job.stage_message = "正在更新数据库..."
                await db.commit()

            chapter.audio_path = saved["audio_path"]
            chapter.audio_url = f"/api/audio/{project_id}/{chapter_id}/narration.mp3"
            chapter.audio_duration_seconds = audio_duration
            chapter.transcript_json = json.dumps(transcript)
            chapter.timeline_json = json.dumps(timeline)
            chapter.voice_preset = voice_preset
            chapter.status = "audio_ready"
            chapter.updated_at = datetime.utcnow()

            await db.commit()

            # 完成
            if job:
                job.status = "completed"
                job.progress = 100
                job.stage_message = "音频合成和对齐完成！"
                job.completed_at = datetime.utcnow()
                await db.commit()

        except asyncio.CancelledError:
            logger.info(
                f"[generate_audio_and_align_task] task cancelled "
                f"job_id={job_id} chapter_id={chapter_id}"
            )
            raise
        except Exception as e:
            import traceback
            error_tb = traceback.format_exc()
            logger.exception(
                f"[generate_audio_and_align_task] 后台任务异常 "
                f"job_id={job_id} chapter_id={chapter_id}: {e}"
            )

            if job:
                job.status = "failed"
                job.stage_message = f"音频生成失败: {type(e).__name__}: {str(e)[:400]}"
                job.completed_at = datetime.utcnow()
                await db.commit()

            chapter = await db.get(Chapter, chapter_id)
            if chapter:
                chapter.error_message = error_tb[:10000]
                chapter.status = "failed"
                await db.commit()


# ============ Shot-level API endpoints (KI-001/002/003) ============


class ShotRegenerateRequest(BaseModel):
    """Shot 重新生成请求（可选 body）"""
    adjustment_intent: Optional[str] = None  # 用户中文修改意图，如"让她笑"


class ShotUpdateRequest(BaseModel):
    """Shot 可编辑字段更新请求"""
    narration_segment: Optional[str] = None  # 旁白文字
    chinese_text: Optional[str] = None       # 对话/气泡文字


def _find_shot_in_storyboard(storyboard_data: dict, shot_id: int) -> tuple:
    """
    在 storyboard_json 中查找指定 shot_id 的 shot。

    Returns:
        (shot_dict, shot_index) 或 (None, -1)
    """
    shots = storyboard_data.get("shots", [])
    for idx, shot in enumerate(shots):
        if shot.get("shot_id") == shot_id:
            return shot, idx
    return None, -1


async def _get_project_and_chapter(
    project_id: str,
    chapter_number: int,
    user_id: int,
    db: AsyncSession,
) -> tuple:
    """
    验证项目归属 + 获取 chapter，返回 (project, chapter)。
    任一验证失败抛 HTTPException。
    """
    project_result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project.id,
            Chapter.chapter_number == chapter_number,
        )
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    return project, chapter


@router.post("/{chapter_number}/shots/{shot_id}/regenerate")
async def regenerate_shot(
    project_id: str,
    chapter_number: int,
    shot_id: int,
    body: Optional[ShotRegenerateRequest] = None,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    重新生成单个 shot 的图片（KI-001 修复 + TASK-STAGED-V2 Haiku 集成）

    Phase 2.0 shot 级粒度，使用 generate_shot_image_phase2() + 参考图 + StyleEnforcer。

    两种模式：
    - 无 adjustment_intent：re-roll（保持原 prompt，重新生成图片）
    - 有 adjustment_intent：Haiku 4.5 修改 image_prompt 后重新生成

    当 SKIP_IMAGE_GENERATION=true 时：
    - Haiku prompt 修改照常执行（这是 LLM 调用不是生图）
    - 只有最后的 Gemini 生图被 skip，返回现有图片路径
    """
    from app.config import settings as app_settings

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 解析 storyboard_json
    if not chapter.storyboard_json:
        raise HTTPException(status_code=400, detail="章节没有分镜数据（storyboard_json 为空）")

    try:
        storyboard_data = json.loads(chapter.storyboard_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="分镜数据解析失败")

    shot, shot_idx = _find_shot_in_storyboard(storyboard_data, shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot {shot_id} 不存在")

    # 检查 shot 是否被软删除
    if shot.get("deleted"):
        raise HTTPException(status_code=400, detail=f"Shot {shot_id} 已被删除")

    # --- Haiku "调整画面" 逻辑 ---
    prompt_modified = False
    modified_prompt_preview = None
    adjustment_intent = body.adjustment_intent if body else None

    if adjustment_intent:
        original_prompt = shot.get("image_prompt", "")
        if not original_prompt:
            raise HTTPException(
                status_code=400,
                detail=f"Shot {shot_id} 没有 image_prompt，无法调整"
            )

        try:
            from app.prompts.shot_adjustment_prompt import (
                SHOT_ADJUSTMENT_SYSTEM_PROMPT,
                build_adjustment_user_prompt,
                detect_seedream_tripwire,
            )
            # T20-26 Wave 4 Backend 兜底层 (配合 AI-ML 升级的 auto Mode A/B):
            # AI-ML 升级 `build_adjustment_user_prompt(mode="auto")` 自动 detect
            # Seedream tripwires 切到 Mode B (REPLACE-AND-CLEAN). Backend 在 Haiku
            # 返回后**强制校验** + **兜底机械 strip** (Haiku 仍漏时).
            # KEY_LEARNINGS #37/#38, DEC-045.
            from app.services.shot_prompt_rewriter import (
                check_replace_effective,
                find_known_dark_terms,
                strip_known_dark_terms,
            )

            # T22-NEW-4 (2026-05-22): 三层 fallback chain (跨 provider 优先)
            from app.services.llm_fallback_chain import (
                call_llm_with_fallback as _call_llm_with_fallback,
            )

            # ---- 1) 触发词 pre-detect (日志 + metrics, AI-ML auto 内部也会 detect) ----
            tripwire = detect_seedream_tripwire(original_prompt)
            chose_mode = "B" if tripwire["has_tripwire"] else "A"

            # ---- 2) 用 AI-ML 升级的 builder (auto 模式 — 自动切 Mode A/B) ----
            # mode="auto" → AI-ML builder 内部自动 detect tripwire 切 Mode B
            #              并喂给 Haiku 完整 tripwire 命中列表 + verify 指令
            user_message = build_adjustment_user_prompt(
                original_image_prompt=original_prompt,
                user_intent_zh=adjustment_intent,
                mode="auto",
            )

            # ---- 3) 调 LLM 三层 fallback (T22-NEW-4: Haiku → Gemini → Sonnet) ----
            # Mode B 时输出可能含 verify 步骤, max_tokens 加大到 3000
            fb_result = await _call_llm_with_fallback(
                user=user_message,
                system=SHOT_ADJUSTMENT_SYSTEM_PROMPT,
                max_tokens=3000,
                operation_label="shot_adjustment",
            )
            if not fb_result.success:
                # 三层全失败 → 抛 exception 进 outer except (走 fallback to original prompt)
                raise RuntimeError(
                    f"LLM fallback chain exhausted: {fb_result.error}"
                )
            modified_prompt = fb_result.text
            logger.info(
                f"[T20-26][T22-NEW-4] Shot {shot_id} LLM ok via "
                f"{fb_result.provider_used}:{fb_result.model_used} "
                f"(chain_depth={fb_result.chain_depth})"
            )

            # ---- 4) 校验 replace 真生效 (Backend 强制兜底层) ----
            check = check_replace_effective(original_prompt, modified_prompt)
            replace_strategy = f"mode_{chose_mode}_ok"
            removed_terms: list = []

            if not check["effective"]:
                # Haiku 即便走 Mode B 仍漏 → 兜底机械 strip (KEY_LEARNINGS #38 教训)
                logger.warning(
                    f"[T20-26] Shot {shot_id} mode={chose_mode} Haiku replace 未生效: "
                    f"reason='{check['reason']}', "
                    f"orig_dark={check['original_dark_terms']}, "
                    f"new_dark={check['rewritten_dark_terms']}, "
                    f"ratio={check['length_ratio']}x. 启用机械 strip 兜底."
                )
                modified_prompt, removed_terms = strip_known_dark_terms(modified_prompt)
                replace_strategy = f"mode_{chose_mode}_with_mech_strip_fallback"
                # 兜底后再校验一次
                post = find_known_dark_terms(modified_prompt)
                if post:
                    logger.error(
                        f"[T20-26] Shot {shot_id} 兜底 strip 后仍含敏感词: {post}"
                    )

            # ---- 5) 写回 storyboard_json (持久化) ----
            shot["image_prompt"] = modified_prompt
            storyboard_data["shots"][shot_idx] = shot
            chapter.storyboard_json = json.dumps(storyboard_data, ensure_ascii=False)
            chapter.updated_at = datetime.utcnow()
            await db.commit()

            prompt_modified = True
            modified_prompt_preview = modified_prompt[:100]

            logger.info(
                f"[T20-26][Shot Regenerate] strategy={replace_strategy} "
                f"shot={shot_id} mode={chose_mode} "
                f"intent='{adjustment_intent}' "
                f"orig_len={check['original_len']} new_len={len(modified_prompt)} "
                f"ratio={check['length_ratio']}x "
                f"tripwire_hits={tripwire['matched_keywords'][:5]} "
                f"orig_dark={check['original_dark_terms']} "
                f"mech_stripped={removed_terms} "
                f"preview='{modified_prompt_preview}'"
            )

        except Exception as e:
            # Haiku 调用失败: fallback 到原始 prompt 继续 (不阻塞 re-roll)
            logger.warning(
                f"[T20-26][Shot Regenerate] Haiku adjustment failed for shot {shot_id}: {e}. "
                f"Falling back to original prompt."
            )
            prompt_modified = False
            modified_prompt_preview = None

    # SKIP_IMAGE_GENERATION 模式：Haiku 已执行完毕，只 skip 生图部分
    if app_settings.SKIP_IMAGE_GENERATION:
        existing_image_url = shot.get("image_url", "")
        logger.info(
            f"[Shot Regenerate] SKIP mode — returning existing image for shot {shot_id}: "
            f"{existing_image_url}, prompt_modified={prompt_modified}"
        )
        return {
            "status": "completed",
            "shot_id": shot_id,
            "imageUrl": existing_image_url,
            "skipped": True,
            "prompt_modified": prompt_modified,
            "modified_prompt_preview": modified_prompt_preview,
            "message": "SKIP_IMAGE_GENERATION=true, 返回现有图片"
                + (f"（prompt 已由 Haiku 修改）" if prompt_modified else ""),
        }

    # 真实生图模式
    # 实施 TODO 4 步: char_refs + scene_refs → generate_shot_image_phase2_safe → 覆盖文件 → 更新 image_url
    import os
    import time
    from PIL import Image as PilImage

    try:
        # 1. 确定 output_dir（基于 project.uuid）
        output_dir = os.path.join("./output", project.uuid)
        char_refs_dir = os.path.join(output_dir, "character_refs")
        scene_refs_dir = os.path.join(output_dir, "scene_refs")

        # 2. 从磁盘加载角色参考图（按出场角色过滤）
        # 从 characters_json 获取角色列表
        if chapter.characters_json:
            characters_list = json.loads(chapter.characters_json)
        else:
            characters_list = []
        # 构建 characters dict（与 pipeline 格式一致）
        characters_for_gen = {"characters": characters_list}

        # 确定出场角色（从 shot 数据）
        char_direction = shot.get("character_direction", {})
        chars_in_scene = char_direction.get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")

        # RISK-T18-F fix: 每个角色传 portrait + fullbody 两张（Pipeline 契约统一）
        # 原逻辑: 根据 shot_type 选择 portrait 或 fullbody 其中一张 → char_refs=1
        # 问题: 缺失另一张 ref 导致 Seedream 仅靠 prompt 文本推断全身细节，发型/服装细节不锁定
        # 修复: 只要文件存在就 portrait + fullbody 都传，让 Seedream 有完整视觉 ground truth
        char_ref_images: list[PilImage.Image] = []
        for char_id in chars_in_scene:
            portrait_path = os.path.join(char_refs_dir, f"{char_id}_portrait.png")
            fullbody_path = os.path.join(char_refs_dir, f"{char_id}_fullbody.png")

            if os.path.exists(portrait_path):
                char_ref_images.append(PilImage.open(portrait_path).convert("RGB"))
            if os.path.exists(fullbody_path):
                char_ref_images.append(PilImage.open(fullbody_path).convert("RGB"))

        # 3. 从磁盘加载场景参考图
        scene_ref_images: list[PilImage.Image] = []
        scene_id = shot.get("scene_id")
        if scene_id and os.path.exists(scene_refs_dir):
            # 尝试加载对应场景的 interior/exterior 参考图
            for suffix in ["interior", "exterior"]:
                scene_ref_path = os.path.join(scene_refs_dir, f"loc_{scene_id}_{suffix}.png")
                if os.path.exists(scene_ref_path):
                    scene_ref_images.append(PilImage.open(scene_ref_path))

            # 如果按 scene_id 没找到，扫描所有场景参考图文件名匹配
            if not scene_ref_images:
                import glob
                for f in glob.glob(os.path.join(scene_refs_dir, "*.png")):
                    fname = os.path.basename(f)
                    # 常见格式: location_id_interior.png / location_id_exterior.png
                    scene_ref_images.append(PilImage.open(f))
                    if len(scene_ref_images) >= 2:
                        break

        all_refs = char_ref_images + scene_ref_images

        # 4. 获取 style_preset 和 aspect_ratio（从 project）
        style_preset = project.style_preset or "anime"
        aspect_ratio = project.aspect_ratio or "2:3"

        # 5. 加载 storyboard（完整数据）
        storyboard = storyboard_data  # 已在函数开头解析

        # 6. 调用 generate_shot_image_phase2_safe
        from app.services.image_generator import ImageGenerator

        image_generator = ImageGenerator()

        logger.info(
            f"[Shot Regenerate] 真生图 shot {shot_id}, "
            f"char_refs={len(char_ref_images)}, scene_refs={len(scene_ref_images)}, "
            f"style={style_preset}, aspect_ratio={aspect_ratio}"
        )

        result = await image_generator.generate_shot_image_phase2_safe(
            shot=shot,
            storyboard=storyboard,
            characters=characters_for_gen,
            style_preset=style_preset,
            reference_images=all_refs if all_refs else None,
            aspect_ratio=aspect_ratio,
            project_id=project.id,  # RISK-T15-13b: 传递 project_id 给 seedream_generator.log_api_cost
        )

        if not result.get("success"):
            error_msg = result.get("error", "图像生成失败")
            logger.error(f"[Shot Regenerate] 生图失败 shot {shot_id}: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"图像重新生成失败: {error_msg}"
            )

        # 7. 保存新图片，覆盖原文件 — 支持多种 image_generator 返回格式
        pil_image = result.get("pil_image")
        image_data = result.get("image_data")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        shot_filename = f"shot_{shot_id:02d}.png"
        shot_path = os.path.join(images_dir, shot_filename)

        if pil_image and hasattr(pil_image, "save"):
            # PIL Image 直接 save
            pil_image.save(shot_path, format="PNG")
        elif isinstance(image_data, bytes):
            # bytes 直接写文件
            with open(shot_path, "wb") as f:
                f.write(image_data)
        elif isinstance(image_data, str):
            # base64 string 解码后写
            import base64
            try:
                image_bytes = base64.b64decode(image_data)
                with open(shot_path, "wb") as f:
                    f.write(image_bytes)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"base64 解码失败: {e}")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"生成图像数据格式异常: pil_image={type(pil_image)}, image_data={type(image_data)}"
            )

        logger.info(f"[Shot Regenerate] Shot {shot_id} 图片已覆盖保存: {shot_path}")

        # 8. 更新 storyboard_json 中的 image_url（带 ?v= 防 frontend cache）
        v_ts = int(time.time())
        new_image_url = (
            f"/static/outputs/{project.uuid}/images/{shot_filename}?v={v_ts}"
        )
        shot["image_url"] = new_image_url
        storyboard_data["shots"][shot_idx] = shot
        chapter.storyboard_json = json.dumps(storyboard_data, ensure_ascii=False)
        chapter.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(
            f"[Shot Regenerate] Shot {shot_id} 重新生成成功, new_url={new_image_url}"
        )

        # RISK-T15-13a: 回写 5_image_results.json，将 Shot success 改为 True
        generation_time = result.get("generation_time_seconds")
        from pathlib import Path
        results_path = Path(output_dir) / "5_image_results.json"
        if results_path.exists():
            try:
                results_data = json.loads(results_path.read_text(encoding="utf-8"))
                updated_in_results = False
                for r in results_data:
                    if r.get("shot_id") == shot_id:
                        r["success"] = True
                        r["error"] = None
                        r["error_kind"] = None
                        r["image_path"] = shot_path
                        r["image_url"] = new_image_url
                        if generation_time is not None:
                            r["generation_time_seconds"] = generation_time
                        updated_in_results = True
                        break
                results_path.write_text(
                    json.dumps(results_data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info(
                    f"[Shot Regenerate] 5_image_results.json 回写完成, "
                    f"shot_id={shot_id}, updated={updated_in_results}"
                )
            except Exception as e:
                # 回写失败非阻塞，不影响主响应
                logger.warning(
                    f"[Shot Regenerate] 5_image_results.json 回写失败（非阻塞）: {e}"
                )

        # RISK-T15-12: 更新 chapter_generation_jobs.failed_shot_count / partial_failure
        try:
            job_result = await db.execute(
                select(GenerationJob)
                .where(GenerationJob.chapter_id == chapter.id)
                .order_by(GenerationJob.created_at.desc())
                .limit(1)
            )
            latest_job = job_result.scalar_one_or_none()
            if latest_job is not None:
                latest_job.failed_shot_count = max(0, (latest_job.failed_shot_count or 0) - 1)
                latest_job.partial_failure = (latest_job.failed_shot_count > 0)
                db.add(latest_job)
                await db.commit()
                logger.info(
                    f"[Shot Regenerate] DB job 更新: "
                    f"failed_shot_count={latest_job.failed_shot_count}, "
                    f"partial_failure={latest_job.partial_failure}"
                )
        except Exception as e:
            # DB 更新失败非阻塞，不影响主响应
            logger.warning(
                f"[Shot Regenerate] job DB 更新失败（非阻塞）: {e}"
            )

        return {
            "status": "completed",
            "shot_id": shot_id,
            "imageUrl": new_image_url,
            "skipped": False,
            "prompt_modified": prompt_modified,
            "modified_prompt_preview": modified_prompt_preview,
            "message": f"[SeedreamGenerator] Shot {shot_id} 重新生成成功"
                + (f"（prompt 已由 Haiku 修改）" if prompt_modified else ""),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Shot Regenerate] 真生图异常 shot {shot_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"图像重新生成失败: {type(e).__name__}: {str(e)[:200]}"
        )


@router.patch("/{chapter_number}/shots/{shot_id}")
async def update_shot(
    project_id: str,
    chapter_number: int,
    shot_id: int,
    body: ShotUpdateRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    更新单个 shot 的可编辑字段（KI-002 修复）

    支持更新 narration_segment（旁白文字）和 chinese_text（对话/气泡文字）。
    将修改写回 chapter.storyboard_json 持久化到 DB。
    """
    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    if not chapter.storyboard_json:
        raise HTTPException(status_code=400, detail="章节没有分镜数据")

    try:
        storyboard_data = json.loads(chapter.storyboard_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="分镜数据解析失败")

    shot, shot_idx = _find_shot_in_storyboard(storyboard_data, shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot {shot_id} 不存在")

    if shot.get("deleted"):
        raise HTTPException(status_code=400, detail=f"Shot {shot_id} 已被删除，无法编辑")

    # 更新字段（只更新非 None 值）
    updated_fields = []
    if body.narration_segment is not None:
        shot["narration_segment"] = body.narration_segment
        updated_fields.append("narration_segment")

    if body.chinese_text is not None:
        # chinese_text 存在 text_overlay 子结构中
        if "text_overlay" not in shot:
            shot["text_overlay"] = {}
        shot["text_overlay"]["chinese_text"] = body.chinese_text
        updated_fields.append("chinese_text")

    if not updated_fields:
        raise HTTPException(status_code=400, detail="没有提供要更新的字段")

    # 写回 storyboard_json
    storyboard_data["shots"][shot_idx] = shot
    chapter.storyboard_json = json.dumps(storyboard_data, ensure_ascii=False)
    chapter.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"[Shot Update] project={project_id} chapter={chapter_number} "
        f"shot={shot_id} updated_fields={updated_fields}"
    )

    return {
        "status": "updated",
        "shot_id": shot_id,
        "updated_fields": updated_fields,
        "shot": shot,
    }


@router.delete("/{chapter_number}/shots/{shot_id}")
async def delete_shot(
    project_id: str,
    chapter_number: int,
    shot_id: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    软删除单个 shot（KI-003 修复）

    在 storyboard_json 中标记 shot.deleted = true（不物理移除）。
    被删除的 shot 不参与后续渲染/导出，但可通过恢复接口取消删除。
    """
    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    if not chapter.storyboard_json:
        raise HTTPException(status_code=400, detail="章节没有分镜数据")

    try:
        storyboard_data = json.loads(chapter.storyboard_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="分镜数据解析失败")

    shot, shot_idx = _find_shot_in_storyboard(storyboard_data, shot_id)
    if shot is None:
        raise HTTPException(status_code=404, detail=f"Shot {shot_id} 不存在")

    if shot.get("deleted"):
        return {"status": "already_deleted", "shot_id": shot_id}

    # 软删除：标记 deleted: true
    shot["deleted"] = True
    storyboard_data["shots"][shot_idx] = shot
    chapter.storyboard_json = json.dumps(storyboard_data, ensure_ascii=False)
    chapter.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"[Shot Delete] project={project_id} chapter={chapter_number} "
        f"shot={shot_id} soft-deleted"
    )

    return {
        "status": "deleted",
        "shot_id": shot_id,
    }


# ============ BGM REST API endpoints (Wave 3 Step 5) ============


class VolumeUpdate(BaseModel):
    """BGM 音量更新请求"""
    volume: float  # 0.0-1.0


@router.get("/{chapter_number}/bgm")
async def get_bgm(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    获取当前 chapter 的 BGM 信息。

    Returns:
        {
            "bgm_url": str | null,      # "/static/..." 路径或 null
            "bgm_volume": float,         # 音量系数 0.0-1.0
            "meta_version": str | null,  # "mixed" | "en" | null
            "credits_used": int,         # 本 chapter 累计 BGM 消耗积分
            "bgm_exists": bool,          # bgm_url 非 null 且文件实际存在
        }
    """
    try:
        import os

        project, chapter = await _get_project_and_chapter(
            project_id, chapter_number, user_id, db
        )

        bgm_url = chapter.bgm_url
        bgm_exists = False

        if bgm_url:
            # 判断文件是否实际存在（bgm_url 可能是绝对路径或 /static/... URL）
            if bgm_url.startswith("/"):
                # 绝对本地路径 or /static/ URL — 尝试文件系统检查
                check_path = bgm_url if not bgm_url.startswith("/static/") else None
                if check_path:
                    bgm_exists = os.path.isfile(check_path)
                else:
                    bgm_exists = True  # /static/ URL 假设存在（由 static 服务托管）
            else:
                bgm_exists = os.path.isfile(bgm_url)

        return {
            "bgm_url": bgm_url,
            "bgm_volume": chapter.bgm_volume if chapter.bgm_volume is not None else 1.0,
            "meta_version": chapter.bgm_meta_version,
            "credits_used": chapter.credits_used or 0,
            "bgm_exists": bgm_exists,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[chapters/bgm GET] unhandled error project={project_id} chapter={chapter_number}: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


@router.post("/{chapter_number}/bgm/regenerate")
async def regenerate_bgm(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    重新生成 BGM（同一 meta_version，重新走 Haiku + Mureka + FFmpeg）。

    使用现有 meta_version 重跑，不切换版本（is_change_bgm=False）。
    每次调用扣 10 credits（mock）。

    B43: generate_bgm_for_chapter 已改为 async，直接 await 调用，不再需要 asyncio.to_thread。

    Returns:
        {
            "success": bool,
            "bgm_url": str,
            "meta_version": str,
            "credits_used_this_call": int,   # 本次扣点（10）
            "total_credits_used": int,        # chapter 累计总积分
        }
    """
    import os
    import json as _json

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 读取 outline（优先 confirmed，fallback raw）
    outline_raw = project.confirmed_outline_json or project.raw_outline_json
    if not outline_raw:
        raise HTTPException(status_code=400, detail="项目缺少故事大纲数据（confirmed_outline_json / raw_outline_json 均为空）")

    try:
        outline = _json.loads(outline_raw)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"故事大纲 JSON 解析失败: {e}")

    # 读取 screenplay（从 chapter.scenes_json，格式为 scenes 列表）
    screenplay: dict = {}
    if chapter.scenes_json:
        try:
            scenes_list = _json.loads(chapter.scenes_json)
            screenplay = {"scenes": scenes_list}
        except _json.JSONDecodeError:
            screenplay = {}

    # 计算输出目录（使用 chapter.storyboard_json 路径旁边，或 fallback 到临时目录）
    output_dir = _resolve_output_dir(project, chapter)

    # 确定 story_type（从 project.chapter_duration_minutes）
    story_type = _map_story_type(project.chapter_duration_minutes or 3)

    # visual_style_hint 从 style_preset 转为 music_hint 值（不是名称字符串）
    from app.models.style_config import get_music_hint
    visual_style_hint = get_music_hint(project.style_preset or "")

    # regen_count：chapter 无专用字段，用 0 保持 meta_version 稳定（is_change_bgm=False）
    regen_count = 0

    logger.info(
        f"[BGM Regenerate] project={project_id} chapter={chapter_number} "
        f"story_type={story_type} style={visual_style_hint}"
    )

    try:
        from app.services.music_generation_service import generate_bgm_for_chapter

        # B43: generate_bgm_for_chapter 已改为 async，直接 await 调用
        # Wave 7 / RISK-T14-11 / DEC-026: BGM 通用性框架 wiring — 传 project.style_preset
        result = await generate_bgm_for_chapter(
            chapter.id,
            project.id,
            outline,
            screenplay,
            output_dir,
            story_type,
            visual_style_hint,
            regen_count,
            chapter.bgm_volume if chapter.bgm_volume is not None else 1.0,
            False,  # is_change_bgm=False（重生成，不切换 meta_version）
            style_preset=project.style_preset or "",  # Wave 7 BGM 通用性框架
        )
    except Exception as e:
        logger.error(f"[BGM Regenerate] 生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"BGM 重新生成失败: {str(e)}")

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=f"BGM 重新生成失败: {result.get('error', '未知错误')}")

    # 更新 DB：bgm_url + credits_used
    credits_this_call = result.get("credits_used", 10)
    new_total_credits = (chapter.credits_used or 0) + credits_this_call

    chapter.bgm_url = result.get("bgm_url", chapter.bgm_url)
    chapter.credits_used = new_total_credits
    chapter.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"[BGM Regenerate] 完成: bgm_url={chapter.bgm_url} "
        f"credits_this_call={credits_this_call} total={new_total_credits}"
    )

    return {
        "success": True,
        "bgm_url": chapter.bgm_url,
        "meta_version": result.get("meta_version", chapter.bgm_meta_version),
        "credits_used_this_call": credits_this_call,
        "total_credits_used": new_total_credits,
    }


@router.post("/{chapter_number}/bgm/change-meta")
async def change_bgm_meta(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    切换 BGM meta-prompt 版本（mixed ↔ en）并重新生成。

    换 BGM 逻辑（基于 chapter.bgm_meta_version 当前值）：
      - 当前 "mixed" → 切到 "en"
      - 当前 "en"   → 切回 "mixed"
      - 首次（null）→ "mixed"（默认）

    每次调用扣 5 credits（mock）。

    B43: generate_bgm_for_chapter 已改为 async，直接 await 调用，不再需要 asyncio.to_thread。

    Returns:
        {
            "success": bool,
            "bgm_url": str,
            "meta_version": str,           # 新的 meta_version
            "credits_used_this_call": int,  # 本次扣点（5）
            "total_credits_used": int,
        }
    """
    import json as _json

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 计算下一个 meta_version
    current_meta = chapter.bgm_meta_version
    if current_meta == "mixed":
        next_meta = "en"
    elif current_meta == "en":
        next_meta = "mixed"
    else:
        next_meta = "mixed"  # 首次（null）→ mixed

    # 读取 outline
    outline_raw = project.confirmed_outline_json or project.raw_outline_json
    if not outline_raw:
        raise HTTPException(status_code=400, detail="项目缺少故事大纲数据")

    try:
        outline = _json.loads(outline_raw)
    except _json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"故事大纲 JSON 解析失败: {e}")

    # 读取 screenplay
    screenplay: dict = {}
    if chapter.scenes_json:
        try:
            scenes_list = _json.loads(chapter.scenes_json)
            screenplay = {"scenes": scenes_list}
        except _json.JSONDecodeError:
            screenplay = {}

    output_dir = _resolve_output_dir(project, chapter)
    story_type = _map_story_type(project.chapter_duration_minutes or 3)
    # visual_style_hint 从 style_preset 转为 music_hint 值（不是名称字符串）
    from app.models.style_config import get_music_hint
    visual_style_hint = get_music_hint(project.style_preset or "")

    # is_change_bgm=True 触发换 BGM 积分（5 points）
    # regen_count=1 使服务内部选择 "en" 版本，但我们通过 is_change_bgm=True 标记
    # 实际 meta_version 由服务内部 _select_meta_version(regen_count) 决定
    # 为确保切换到目标 meta_version，使用 regen_count 调整：
    #   next_meta="en"    → regen_count=1（_select_meta_version(1) == "en"）
    #   next_meta="mixed" → regen_count=0（_select_meta_version(0) == "mixed"）
    regen_count_for_meta = 1 if next_meta == "en" else 0

    logger.info(
        f"[BGM ChangeMeta] project={project_id} chapter={chapter_number} "
        f"current_meta={current_meta} next_meta={next_meta}"
    )

    try:
        from app.services.music_generation_service import generate_bgm_for_chapter

        # B43: generate_bgm_for_chapter 已改为 async，直接 await 调用
        # Wave 7 / RISK-T14-11 / DEC-026: BGM 通用性框架 wiring — 传 project.style_preset
        result = await generate_bgm_for_chapter(
            chapter.id,
            project.id,
            outline,
            screenplay,
            output_dir,
            story_type,
            visual_style_hint,
            regen_count_for_meta,
            chapter.bgm_volume if chapter.bgm_volume is not None else 1.0,
            True,  # is_change_bgm=True（触发换 BGM 积分计算）
        )
    except Exception as e:
        logger.error(f"[BGM ChangeMeta] 生成失败: {e}")
        raise HTTPException(status_code=500, detail=f"BGM 切换版本失败: {str(e)}")

    if not result.get("success"):
        raise HTTPException(status_code=500, detail=f"BGM 切换版本失败: {result.get('error', '未知错误')}")

    # 更新 DB：bgm_url + bgm_meta_version + credits_used
    credits_this_call = result.get("credits_used", 5)
    new_total_credits = (chapter.credits_used or 0) + credits_this_call
    actual_meta_version = result.get("meta_version", next_meta)

    chapter.bgm_url = result.get("bgm_url", chapter.bgm_url)
    chapter.bgm_meta_version = actual_meta_version
    chapter.credits_used = new_total_credits
    chapter.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"[BGM ChangeMeta] 完成: meta_version={actual_meta_version} "
        f"credits_this_call={credits_this_call} total={new_total_credits}"
    )

    return {
        "success": True,
        "bgm_url": chapter.bgm_url,
        "meta_version": actual_meta_version,
        "credits_used_this_call": credits_this_call,
        "total_credits_used": new_total_credits,
    }


@router.patch("/{chapter_number}/bgm/volume")
async def update_bgm_volume(
    project_id: str,
    chapter_number: int,
    body: VolumeUpdate,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    调节 BGM 音量系数（0.0-1.0），仅更新 DB，不触发 FFmpeg 重渲染。

    FFmpeg 重渲染发生在 Stage E 视频合成时，届时读取 bgm_volume 字段应用。
    此接口为非破坏性操作。

    Args:
        body.volume: 新音量系数，必须在 0.0-1.0 之间

    Returns:
        {"success": bool, "bgm_volume": float}
    """
    if body.volume < 0.0 or body.volume > 1.0:
        raise HTTPException(
            status_code=400,
            detail=f"volume 必须在 0.0-1.0 之间，收到: {body.volume}",
        )

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    chapter.bgm_volume = body.volume
    chapter.updated_at = datetime.utcnow()
    await db.commit()

    logger.info(
        f"[BGM Volume] project={project_id} chapter={chapter_number} "
        f"volume={body.volume}"
    )

    return {
        "success": True,
        "bgm_volume": chapter.bgm_volume,
    }


# ============ BGM 辅助函数 ============

def _map_story_type(chapter_duration_minutes: int) -> str:
    """
    将 chapter_duration_minutes 映射为 story_type 字符串。

    规则（与 pipeline_orchestrator.py Stage 6 一致）：
      <= 1 分钟 → 快闪
      <= 2 分钟 → 短篇
      > 2 分钟  → 中篇
    """
    if chapter_duration_minutes <= 1:
        return "快闪"
    elif chapter_duration_minutes <= 2:
        return "短篇"
    else:
        return "中篇"


def _resolve_output_dir(project, chapter) -> str:
    """
    解析 BGM 输出目录。

    策略：
    1. 如果 chapter.bgm_url 是已存在的本地路径，取其父目录
    2. 否则 fallback 到 /tmp/bgm_{project.id}_{chapter.id}/
    """
    import os
    import tempfile

    if chapter.bgm_url and not chapter.bgm_url.startswith("/static/"):
        parent = os.path.dirname(chapter.bgm_url)
        if parent and os.path.isdir(parent):
            return parent

    # Fallback：临时目录（确保存在）
    fallback = os.path.join(tempfile.gettempdir(), f"bgm_{project.id}_{chapter.id}")
    os.makedirs(fallback, exist_ok=True)
    return fallback


# ===========================================================================
# RISK-T17-8 (Wave 12): Pipeline 失败原地重启从指定 Stage
# ===========================================================================

def _parse_failed_stage_number(error_message: str | None) -> int:
    """从 chapter.error_message 或 job.stage_message 解析失败的 Stage 编号。

    pipeline_orchestrator.py 在 except 时记录 self.current_stage（如 "Stage 4: StoryboardDirector"）。
    job_manager.py 的 error_message 格式为 "[Stage X] ..."。

    Returns:
        失败的 Stage 编号（1-6），解析失败时返回 4（最常见失败点）。
    """
    if not error_message:
        return 4  # 默认从 Stage 4 重试

    import re
    # 匹配 "[Stage X]" 或 "Stage X:" 或 "Stage X :"
    m = re.search(r'Stage\s+(\d+)', error_message, re.IGNORECASE)
    if m:
        stage_num = int(m.group(1))
        # Stage 编号合理范围 1-6
        if 1 <= stage_num <= 6:
            return stage_num
    return 4  # fallback


@router.post("/{chapter_number}/restart-from-failed-stage")
async def restart_from_failed_stage(
    project_id: str,
    chapter_number: int,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RISK-T17-8 (Wave 12): Pipeline 失败后原地重启，从失败 Stage 重跑。

    用户故事: Pipeline failed at Stage 4 后，用户已花 25 min 工作 (Stage 1-3 完成)。
    此端点允许从失败 Stage 重跑，不浪费已有 outline/characters/screenplay。

    流程:
    1. 验证 chapter.status == "failed"（非失败状态拒绝）
    2. 解析 error_message 确定失败 Stage
    3. 验证 disk 上已有前序 Stage 结果 (1_outline.json 等)
    4. 清空失败 Stage 的 disk 文件 (e.g. 4_storyboard.json)
    5. 重置 chapter.status → "pending"，清空 error_message
    6. 新建 GenerationJob，触发 Pipeline 从 start_from_stage 重跑

    Response:
        {
          "success": true,
          "message": "Pipeline 已从 Stage 4 重启",
          "failed_stage": 4,
          "start_from_stage": 4,
          "job_id": 123
        }
    """
    import os

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 1. 验证 chapter 状态必须是 "failed"
    if chapter.status != "failed":
        raise HTTPException(
            status_code=400,
            detail=(
                f"章节状态为 '{chapter.status}'，只有 failed 状态才能原地重启。"
                f"当前状态不支持此操作。"
            ),
        )

    # 2. 从 error_message 解析失败 Stage
    failed_stage = _parse_failed_stage_number(chapter.error_message)
    start_from_stage = failed_stage  # 从失败 Stage 重跑

    # 3. 验证 disk 上已有前序 Stage 结果（至少要有 1_outline.json）
    output_dir = os.path.join("./output", project.uuid)
    outline_path = os.path.join(output_dir, "1_outline.json")
    if not os.path.exists(outline_path):
        raise HTTPException(
            status_code=422,
            detail=(
                f"找不到 {outline_path}（Stage 1 输出不存在），"
                f"无法从 Stage {failed_stage} 重启。请重新创建项目。"
            ),
        )

    # 4. 清空失败 Stage 及之后的 disk 文件，避免旧数据干扰
    _stage_files = {
        2: "2_characters.json",
        3: "3_screenplay.json",
        4: "4_storyboard.json",
        5: "5_image_results.json",
    }
    for stage_num, filename in _stage_files.items():
        if stage_num >= failed_stage:
            fpath = os.path.join(output_dir, filename)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    logger.info(f"[RestartPipeline] 清空 {filename} (stage {stage_num} >= failed_stage {failed_stage})")
                except Exception as _rm_e:
                    logger.warning(f"[RestartPipeline] 清空 {filename} 失败（非阻塞）: {_rm_e}")

    # 5. 重置 chapter.status → "pending"，清空 error_message
    chapter.status = "pending"
    chapter.error_message = None
    chapter.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(chapter)

    # 6. 读取 project 信息，构建 pipeline 所需参数
    # 从 chapter/project 读取原始参数
    confirmed_outline: dict | None = None
    if project.confirmed_outline_json:
        try:
            confirmed_outline = json.loads(project.confirmed_outline_json)
        except Exception:
            pass
    if not confirmed_outline and project.raw_outline_json:
        try:
            confirmed_outline = json.loads(project.raw_outline_json)
        except Exception:
            pass

    # 7. 新建 GenerationJob
    from app.services.job_manager import JobManager, run_story_generation_task, calculate_eta_remaining_sec as _calc_eta
    job_manager = JobManager(db)
    job = await job_manager.create_job(chapter.id)

    # T21-NEW-3 (2026-05-21): restart 后立即设置真实 progress + ETA, 防 frontend 看到 0% / 27 min
    # 真根因: job_manager.create_job() 初始化 progress=0 + estimated_seconds=None,
    # frontend 第一次 poll (~2-5s) 内只能拿到 0% + null/legacy 默认值, UX 极差.
    # 修复方案: restart 时 truly 重算 initial progress + ETA, 同步写 DB, frontend 第一次 poll 即拿到真值.
    #
    # 按 start_from_stage 映射初始 progress (跳过已完成 stages, 对齐 progress_callback 的 stage entry 值)
    _RESTART_STAGE_TO_PROGRESS = {
        1: 2,   # Stage 1: story_generation (与 RB-5 initial_message 同步)
        2: 6,   # Stage 2: character_design  (与 P1-1 entry 同步)
        3: 11,  # Stage 3: screenplay        (与 P1-1 entry 同步)
        4: 35,  # Stage 4: storyboard        (与 P1-1 entry 同步)
        5: 65,  # Stage 5: image_preparation (与 P1-1 entry 同步)
    }
    _RESTART_STAGE_TO_STAGE_NAME = {
        1: "story_generation",
        2: "character_design",
        3: "screenplay",
        4: "storyboard",
        5: "image_preparation",
    }
    _initial_progress = _RESTART_STAGE_TO_PROGRESS.get(start_from_stage, 2)
    _initial_stage_name = _RESTART_STAGE_TO_STAGE_NAME.get(start_from_stage, "story_generation")

    # T21-NEW-3: 从 chapter.storyboard_json / project outline / settings 取真实 ETA 参数
    # 当 storyboard 已生成 (Stage 4 已完成, restart from Stage 5) → 真 shot count 用于 ETA 精算
    # 当还没生成 → fallback 18 (calculate_eta_remaining_sec 内部 default 也是 18)
    _restart_actual_shot_count = 18  # default
    try:
        if chapter.storyboard_json:
            _sb = json.loads(chapter.storyboard_json)
            _shots = _sb.get("shots", [])
            if _shots:
                _restart_actual_shot_count = len(_shots)
    except Exception:
        pass

    _restart_unique_location_count = 2  # default
    try:
        _outline_for_eta = None
        if project.confirmed_outline_json:
            _outline_for_eta = json.loads(project.confirmed_outline_json)
        elif project.raw_outline_json:
            _outline_for_eta = json.loads(project.raw_outline_json)
        if _outline_for_eta:
            _locs = _outline_for_eta.get("unique_locations", [])
            if _locs:
                _restart_unique_location_count = len(_locs)
    except Exception:
        pass

    try:
        from app.config import settings as _settings
        _restart_max_concurrent = _settings.IMAGE_MAX_CONCURRENT
    except Exception:
        _restart_max_concurrent = 3

    # 真重算 ETA (传真值, 不依赖 default)
    _initial_eta = _calc_eta(
        stage=_initial_stage_name,
        progress=_initial_progress,
        actual_shot_count=_restart_actual_shot_count,
        unique_location_count=_restart_unique_location_count,
        max_concurrent=_restart_max_concurrent,
    )

    # T21-NEW-3: 更友好的 stage_message (frontend 直接 render)
    _STAGE_FRIENDLY_MESSAGE = {
        "story_generation": "从故事大纲重启中...",
        "character_design": "从角色设计重启中...",
        "screenplay": "从分场剧本重启中...",
        "storyboard": "从分镜创建重启中...",
        "image_preparation": "从画面准备重启中...",
    }
    _initial_message = _STAGE_FRIENDLY_MESSAGE.get(
        _initial_stage_name,
        f"从 Stage {start_from_stage} 重启中..."
    )

    # 立即更新到 DB, frontend 第一次 poll 就拿到真值 (progress > 0, ETA 真重算)
    job.status = "processing"
    job.current_stage = _initial_stage_name
    job.progress = _initial_progress
    job.stage_message = _initial_message
    if _initial_eta is not None:
        job.estimated_seconds = _initial_eta
    job.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(job)

    logger.info(
        f"[RestartPipeline] T21-NEW-3 project={project_id} chapter={chapter_number} "
        f"failed_stage={failed_stage} start_from_stage={start_from_stage} job_id={job.id} "
        f"initial_progress={_initial_progress}% initial_eta={_initial_eta}s "
        f"(shot_count={_restart_actual_shot_count}, location_count={_restart_unique_location_count}, "
        f"max_concurrent={_restart_max_concurrent})"
    )

    # 8. 触发后台任务（与原始 run_story_generation_task 兼容，新增 start_from_stage）
    background_tasks.add_task(
        _run_restart_pipeline_task,
        job_id=job.id,
        chapter_id=chapter.id,
        project_uuid=project.uuid,
        idea=project.original_idea or "",
        style=project.style_preset or "anime",
        duration_minutes=getattr(project, "duration_minutes", 2) or 2,
        character_count=3,
        language="zh-CN",
        confirmed_outline=confirmed_outline,
        aspect_ratio=getattr(project, "aspect_ratio", "2:3") or "2:3",
        user_selected_mood=getattr(project, "user_selected_mood", None),
        start_from_stage=start_from_stage,
    )

    return {
        "success": True,
        "message": f"Pipeline 已从 Stage {start_from_stage} 重启",
        "failed_stage": failed_stage,
        "start_from_stage": start_from_stage,
        "job_id": job.id,
        "chapter_status": "pending",
    }


async def _run_restart_pipeline_task(
    job_id: int,
    chapter_id: int,
    project_uuid: str,
    idea: str,
    style: str,
    duration_minutes: int,
    character_count: int,
    language: str,
    confirmed_outline: dict | None,
    aspect_ratio: str,
    user_selected_mood: str | None,
    start_from_stage: int,
):
    """
    RISK-T17-8: 原地重启 Pipeline 的后台任务。

    与 run_story_generation_task 逻辑类似，但:
    1. 传入 start_from_stage 给 Phase2PipelineOrchestrator.run()
    2. 直接调 Phase2PipelineOrchestrator (不经 StoryGenerator)
    3. 通过短 session 管理 DB 状态
    """
    import time
    from app.database import async_session_maker
    from sqlalchemy import select
    from app.models.job import GenerationJob
    from app.models.chapter import Chapter
    from app.models.project import Project
    from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator
    from app.services.job_manager import (
        _update_job_short_session,
        calculate_eta_remaining_sec,
    )

    task_start = time.time()
    logger.info(
        f"[RestartPipeline] ========== 原地重启 Pipeline ==========\n"
        f"  job_id={job_id}, chapter_id={chapter_id}, "
        f"  start_from_stage={start_from_stage}, style={style}"
    )

    try:
        # 更新 job → processing
        await _update_job_short_session(
            job_id,
            status="processing",
            stage="storyboard" if start_from_stage >= 4 else "screenplay",
            progress=2,
            message=f"正在从 Stage {start_from_stage} 重启...",
        )

        # progress_callback（与 run_story_generation_task 一致）
        _last_progress: list[int] = [0]
        _last_eta: list[int | None] = [None]
        _last_stage: list[str | None] = [None]
        _dyn_shot_count: list[int] = [18]
        _dyn_location_count: list[int] = [2]
        _dyn_max_concurrent: list[int] = [3]

        async def progress_callback(
            stage: str,
            progress: int,
            message: str,
            estimated_remaining_seconds: int | None = None,
            actual_shot_count: int | None = None,
            unique_location_count: int | None = None,
            max_concurrent: int | None = None,
        ):
            if actual_shot_count is not None and actual_shot_count > 0:
                _dyn_shot_count[0] = actual_shot_count
            if unique_location_count is not None and unique_location_count > 0:
                _dyn_location_count[0] = unique_location_count
            if max_concurrent is not None and max_concurrent > 0:
                _dyn_max_concurrent[0] = max_concurrent

            _stage_switched = (_last_stage[0] is not None and _last_stage[0] != stage)
            if _stage_switched:
                _last_eta[0] = None
            _last_stage[0] = stage

            _guarded_progress = max(progress, _last_progress[0])
            _last_progress[0] = _guarded_progress
            _status = "completed" if stage == "completed" else None

            _eta: int | None
            if estimated_remaining_seconds is not None and estimated_remaining_seconds >= 0:
                _eta = int(estimated_remaining_seconds)
            else:
                try:
                    _eta = calculate_eta_remaining_sec(
                        stage=stage,
                        progress=_guarded_progress,
                        actual_shot_count=_dyn_shot_count[0],
                        unique_location_count=_dyn_location_count[0],
                        max_concurrent=_dyn_max_concurrent[0],
                    ) if stage != "completed" else 0
                except Exception:
                    _eta = None

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

        # checkpoint_callback（写 chapter 中间结果）
        async def checkpoint_callback(column_name: str, data):
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
            except Exception as e:
                logger.warning(f"[RestartPipeline] checkpoint_callback {column_name} 失败（非阻塞）: {e}")

        # 运行 Pipeline（带 start_from_stage）
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
            chapter_id=chapter_id,
            aspect_ratio=aspect_ratio,
            user_selected_mood=user_selected_mood,
            job_id=job_id,
            progress_callback=progress_callback,
            checkpoint_callback=checkpoint_callback,
            start_from_stage=start_from_stage,
        )

        if not pipeline_result.get("success", True):
            error_msg = (
                f"[Stage {pipeline_result.get('failed_stage', '?')}] "
                f"{pipeline_result.get('error', 'Pipeline 运行失败')}"
            )
            logger.error(f"[RestartPipeline] ❌ 重启失败: {error_msg}")
            await _update_job_short_session(
                job_id, status="failed", progress=0, message=f"重启失败: {error_msg}"
            )
            async with async_session_maker() as short_db:
                chapter_result = await short_db.execute(
                    select(Chapter).where(Chapter.id == chapter_id)
                )
                ch = chapter_result.scalar_one_or_none()
                if ch:
                    ch.status = "failed"
                    ch.error_message = error_msg
                    await short_db.commit()
            return

        # 成功 → 更新 chapter
        story_data = pipeline_result.get("stage_results", {})
        async with async_session_maker() as short_db:
            chapter_result = await short_db.execute(
                select(Chapter).where(Chapter.id == chapter_id)
            )
            ch = chapter_result.scalar_one_or_none()
            if ch:
                ch.status = "completed"
                ch.error_message = None
                summary = pipeline_result.get("summary", {})
                if summary.get("title"):
                    ch.summary = summary["title"]
                if story_data.get("characters"):
                    ch.characters_json = json.dumps(
                        story_data["characters"].get("characters", []), ensure_ascii=False
                    )
                if story_data.get("screenplay"):
                    ch.scenes_json = json.dumps(
                        story_data["screenplay"].get("scenes", []), ensure_ascii=False
                    )
                if story_data.get("storyboard"):
                    ch.storyboard_json = json.dumps(story_data["storyboard"], ensure_ascii=False)
                await short_db.commit()

        task_elapsed = time.time() - task_start
        logger.info(f"[RestartPipeline] ✅ 重启成功 (耗时 {task_elapsed:.1f}s)")
        await _update_job_short_session(
            job_id,
            status="completed",
            stage="completed",
            progress=100,
            message="重启完成！故事生成成功。",
        )

    except Exception as e:
        task_elapsed = time.time() - task_start
        logger.error(f"[RestartPipeline] ❌ 系统异常 (耗时 {task_elapsed:.1f}s): {e}")
        await _update_job_short_session(
            job_id, status="failed", progress=0, message=f"系统错误: {str(e)}"
        )
        try:
            from app.database import async_session_maker as _asm
            from app.models.chapter import Chapter as _Ch
            async with _asm() as short_db:
                chapter_result = await short_db.execute(
                    select(_Ch).where(_Ch.id == chapter_id)
                )
                ch = chapter_result.scalar_one_or_none()
                if ch:
                    ch.status = "failed"
                    ch.error_message = str(e)
                    await short_db.commit()
        except Exception:
            pass


# ===========================================================================
# T21-NEW-7 (2026-05-21 DEC-047): 场景参考图 3 endpoint (R4-3 闸门)
# ===========================================================================
# 镜像 characters 页面对偶设计:
#   - GET  /chapters/{n}/scene-references — 返回所有场景参考图 (frontend hydrate)
#   - POST /chapters/{n}/scenes/{location_id}/regenerate-reference — 重生单个场景参考图
#   - POST /chapters/{n}/confirm-scene-references — 确认场景继续 Stage 5
# Founder 决方案 D, 2026-05-21 18:25, 60s 倒计时, DEC-014/DEC-009 场景一致性保留


@router.get("/{chapter_number}/scene-references")
async def get_scene_references(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    T21-NEW-7 DEC-047: 返回当前 chapter 的所有场景参考图.

    用于 frontend /scenes 页面真预览 (镜像 characters 页面对偶设计).

    Response:
        {
          "scene_references": [
            {
              "location_id": "virtual_call_center",
              "location_zh": "虚拟客服中心",
              "interior_url": "/static/.../scene_refs/xxx_interior_anchor.png?v=...",
              "exterior_url": "/static/.../scene_refs/xxx_exterior_anchor.png?v=...",
              "interior_description": "...",
              "exterior_description": "...",
              "description_zh": "...",
              "atmosphere": "mechanical_eerie",
              "time_of_day": "night",
              "lighting_condition": "neon_cold_blue",
              "key_visual_elements": [...]
            },
            ...
          ],
          "scene_references_ready": true,        # chapter.scene_references_json 非空
          "scene_references_confirmed": false,   # project.scene_references_confirmed
          "countdown_seconds": 60                # 镜像 characters 页面 60s 倒计时
        }
    """
    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    scene_references: list = []
    if chapter.scene_references_json:
        try:
            scene_references = json.loads(chapter.scene_references_json)
            if not isinstance(scene_references, list):
                scene_references = []
        except (json.JSONDecodeError, TypeError):
            logger.warning(
                f"[scene-references] chapter={chapter.id} scene_references_json parse 失败"
            )
            scene_references = []

    return {
        "scene_references": scene_references,
        "scene_references_ready": bool(chapter.scene_references_json),
        "scene_references_confirmed": bool(
            getattr(project, "scene_references_confirmed", False)
        ),
        "countdown_seconds": 60,
        "chapter_number": chapter_number,
        "project_id": project_id,
    }


class SceneReferenceRegenerateRequest(BaseModel):
    """T21-NEW-7 重生单个场景参考图请求"""
    ref_type: str = "both"  # "interior" | "exterior" | "both"
    user_edit: Optional[str] = None  # 用户编辑的中文场景描述, 触发重生时用


@router.post("/{chapter_number}/scenes/{location_id}/regenerate-reference")
async def regenerate_scene_reference(
    project_id: str,
    chapter_number: int,
    location_id: str,
    body: SceneReferenceRegenerateRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    T21-NEW-7 DEC-047: 重生单个场景参考图 (interior / exterior / both).

    镜像 AdjustCharacter / regenerate-portrait 模式:
    - 真生图 (SceneReferenceManager._generate_single_anchor)
    - 保存到 disk + 更新 chapter.scene_references_json
    - 返回带 cache-buster ?v={epoch} 的 URL

    支持 user_edit: 用户改场景描述 → Pipeline 用新描述生成

    Request body:
        { "ref_type": "interior" | "exterior" | "both", "user_edit": "新描述" }

    Response:
        {
          "success": true,
          "location_id": "virtual_call_center",
          "interior_url": "/static/.../?v={new_epoch}",  # ref_type 涉及 interior 才有
          "exterior_url": "/static/.../?v={new_epoch}",  # ref_type 涉及 exterior 才有
          "message": "..."
        }
    """
    import os as _os
    import time as _time
    from app.services.scene_reference_manager import SceneReferenceManager as _SRM
    from app.models.style_config import ProjectStyleConfig as _PSC
    from app.services.image_generator import ImageGenerator as _IG

    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 1. 解析 outline 找 location
    outline_json = project.confirmed_outline_json or project.raw_outline_json
    if not outline_json:
        raise HTTPException(status_code=400, detail="项目尚未生成大纲")

    try:
        outline = json.loads(outline_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="outline JSON 解析失败")

    unique_locations = outline.get("unique_locations", [])
    target_location = next(
        (loc for loc in unique_locations if loc.get("location_id") == location_id),
        None,
    )
    if not target_location:
        raise HTTPException(
            status_code=404,
            detail=f"location_id={location_id} 不存在",
        )

    # 2. 应用 user_edit (如有) — 改 unique_locations 的 description
    if body.user_edit and body.user_edit.strip():
        _edit = body.user_edit.strip()
        # T21-NEW-7: 用户编辑作为 interior/exterior description (按 ref_type 写)
        if body.ref_type in ("interior", "both"):
            target_location["interior_description"] = _edit
        if body.ref_type in ("exterior", "both"):
            target_location["exterior_description"] = _edit
        # 写回 outline
        outline["unique_locations"] = unique_locations
        if project.confirmed_outline_json:
            project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
        else:
            project.raw_outline_json = json.dumps(outline, ensure_ascii=False)
        logger.info(
            f"[ScenRefRegenerate] T21-NEW-7 location={location_id} user_edit applied "
            f"(ref_type={body.ref_type}, len={len(_edit)})"
        )

    # 3. 真生图 — 用 SceneReferenceManager._generate_single_anchor (mirror Pipeline Stage 4.5)
    _ref_manager = _SRM()
    _project_style = _PSC(style_preset=project.style_preset or "realistic")
    _image_gen = _IG()

    project_dir = _os.path.join("./output", project.uuid)
    scene_refs_dir = _os.path.join(project_dir, "scene_refs")
    _os.makedirs(scene_refs_dir, exist_ok=True)

    # 兜底: 如果 disk 已有 interior 图, 重生 exterior 时把 interior 当参考 (DEC-014/DEC-009)
    from PIL import Image as _PilImg
    existing_interior_pil = None
    _interior_key = f"{location_id}_interior_anchor"
    _interior_disk_path = _os.path.join(scene_refs_dir, f"{_interior_key}.png")
    if _os.path.exists(_interior_disk_path):
        try:
            existing_interior_pil = _PilImg.open(_interior_disk_path).convert("RGB")
        except Exception:
            existing_interior_pil = None

    # location_info 构建 (mirror Stage 4.5 _analyze_anchor_needs_from_structured)
    _display_name = target_location.get("display_name", location_id)
    _interior_desc = target_location.get("interior_description", "")
    _exterior_desc = target_location.get("exterior_description", "")
    _key_elements = target_location.get("key_visual_elements", [])
    _signage_text = target_location.get("signage_text", "")

    # 计算 location 的 character count (mirror Stage 4.5)
    location_char_count = None
    if chapter.scenes_json:
        try:
            _scenes_data = json.loads(chapter.scenes_json)
            if isinstance(_scenes_data, list):
                for sc in _scenes_data:
                    if sc.get("location_ref") == location_id:
                        location_char_count = max(
                            location_char_count or 0,
                            len(sc.get("characters_in_scene", [])),
                        )
        except Exception:
            pass

    _v_ts = int(_time.time())  # cache-buster
    interior_url_result: Optional[str] = None
    exterior_url_result: Optional[str] = None
    interior_image: Optional[_PilImg.Image] = None  # 重生 exterior 时复用

    aspect_ratio = project.aspect_ratio or "2:3"

    # 4. 真生 interior (如 ref_type 包括)
    if body.ref_type in ("interior", "both"):
        try:
            anchor_info = {
                "view_type": "interior",
                "location_id": location_id,
                "location_name": _display_name,
                "description": _interior_desc,
                "key_visual_elements": _key_elements,
                "representative_scene": {},
                "time_of_day": target_location.get("time_of_day", ""),
                "signage_text": _signage_text,
            }
            pil_image, result_dict = await _ref_manager._generate_single_anchor(
                anchor_key=f"{location_id}_interior_anchor",
                anchor_info=anchor_info,
                view_type="interior",
                project_style=_project_style,
                image_generator=_image_gen,
                reference_image=None,
                location_id=location_id,
                num_characters=location_char_count,
                aspect_ratio=aspect_ratio,
            )
            if pil_image:
                _int_path = _os.path.join(scene_refs_dir, f"{location_id}_interior_anchor.png")
                pil_image.save(_int_path)
                interior_url_result = (
                    f"/static/outputs/{project.uuid}/scene_refs/"
                    f"{location_id}_interior_anchor.png?v={_v_ts}"
                )
                interior_image = pil_image
                logger.info(
                    f"[ScenRefRegenerate] T21-NEW-7 interior 重生成功: "
                    f"location={location_id}, cache-buster v={_v_ts}"
                )
            else:
                logger.warning(
                    f"[ScenRefRegenerate] T21-NEW-7 interior 重生失败 "
                    f"(no pil_image): {result_dict.get('error', '未知')}"
                )
        except Exception as _e:
            logger.error(f"[ScenRefRegenerate] T21-NEW-7 interior 重生异常: {_e}")
            raise HTTPException(status_code=500, detail=f"interior 重生失败: {_e}")

    # 5. 真生 exterior (如 ref_type 包括) — DEC-014/DEC-009 用 interior 作参考
    if body.ref_type in ("exterior", "both"):
        try:
            anchor_info = {
                "view_type": "exterior",
                "location_id": location_id,
                "location_name": _display_name,
                "description": _exterior_desc,
                "key_visual_elements": _key_elements,
                "representative_scene": {},
                "time_of_day": target_location.get("time_of_day", ""),
                "signage_text": _signage_text,
            }
            # 用刚生成的 interior 或 disk 上的 interior 作参考 (DEC-014/DEC-009 一致性)
            _ref_for_exterior = interior_image if interior_image else existing_interior_pil
            pil_image, result_dict = await _ref_manager._generate_single_anchor(
                anchor_key=f"{location_id}_exterior_anchor",
                anchor_info=anchor_info,
                view_type="exterior",
                project_style=_project_style,
                image_generator=_image_gen,
                reference_image=_ref_for_exterior,
                location_id=location_id,
                num_characters=location_char_count,
                aspect_ratio=aspect_ratio,
            )
            if pil_image:
                _ext_path = _os.path.join(scene_refs_dir, f"{location_id}_exterior_anchor.png")
                pil_image.save(_ext_path)
                exterior_url_result = (
                    f"/static/outputs/{project.uuid}/scene_refs/"
                    f"{location_id}_exterior_anchor.png?v={_v_ts}"
                )
                logger.info(
                    f"[ScenRefRegenerate] T21-NEW-7 exterior 重生成功: "
                    f"location={location_id}, cache-buster v={_v_ts}"
                )
            else:
                logger.warning(
                    f"[ScenRefRegenerate] T21-NEW-7 exterior 重生失败: "
                    f"{result_dict.get('error', '未知')}"
                )
        except Exception as _e:
            logger.error(f"[ScenRefRegenerate] T21-NEW-7 exterior 重生异常: {_e}")
            raise HTTPException(status_code=500, detail=f"exterior 重生失败: {_e}")

    # 6. 更新 chapter.scene_references_json — 写 cache-busted URL
    if chapter.scene_references_json:
        try:
            scene_refs_list = json.loads(chapter.scene_references_json)
            if not isinstance(scene_refs_list, list):
                scene_refs_list = []
        except (json.JSONDecodeError, TypeError):
            scene_refs_list = []
    else:
        scene_refs_list = []

    # 更新对应 location 条目
    updated_in_list = False
    for entry in scene_refs_list:
        if entry.get("location_id") == location_id:
            if interior_url_result:
                entry["interior_url"] = interior_url_result
                # 如果 user_edit 改了 interior, 同步写 description
                if body.user_edit and body.ref_type in ("interior", "both"):
                    entry["interior_description"] = body.user_edit.strip()
            if exterior_url_result:
                entry["exterior_url"] = exterior_url_result
                if body.user_edit and body.ref_type in ("exterior", "both"):
                    entry["exterior_description"] = body.user_edit.strip()
            updated_in_list = True
            break
    if not updated_in_list:
        # 新增条目 (兜底)
        new_entry = {
            "location_id": location_id,
            "location_zh": _display_name,
            "interior_url": interior_url_result,
            "exterior_url": exterior_url_result,
            "interior_description": _interior_desc,
            "exterior_description": _exterior_desc,
            "description_zh": _display_name + " - " + (_interior_desc or _exterior_desc),
            "atmosphere": target_location.get("atmosphere", ""),
            "time_of_day": target_location.get("time_of_day", ""),
            "lighting_condition": target_location.get("lighting_condition", ""),
            "key_visual_elements": _key_elements,
        }
        scene_refs_list.append(new_entry)

    chapter.scene_references_json = json.dumps(scene_refs_list, ensure_ascii=False)
    chapter.updated_at = datetime.utcnow()
    db.add(chapter)
    db.add(project)
    await db.commit()

    return {
        "success": True,
        "location_id": location_id,
        "interior_url": interior_url_result,
        "exterior_url": exterior_url_result,
        "message": f"场景参考图已重新生成 (ref_type={body.ref_type})",
    }


@router.post("/{chapter_number}/confirm-scene-references")
async def confirm_scene_references(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    T21-NEW-7 DEC-047 R4-3 闸门: 用户确认场景参考图 → 解锁 Stage 5.

    与 R4-1 (/confirm-characters), R4-2 (/confirm-scenes) 对称.
    Pipeline R4-3 wait loop 轮询 project.scene_references_confirmed,
    检测到 True 跳出循环进 Stage 5 image_preparation (fullbody + shots).

    Response:
        { "success": true, "scene_references_confirmed": true, "next_stage": "image_generation" }
    """
    project, chapter = await _get_project_and_chapter(
        project_id, chapter_number, user_id, db
    )

    # 验证 scene_references_json 非空 (Stage 4.5 必须已跑完)
    if not chapter.scene_references_json:
        raise HTTPException(
            status_code=409,
            detail="场景参考图尚未生成完成，请稍候再确认 (Stage 4.5 进行中)",
        )

    # 标记确认
    project.scene_references_confirmed = True
    db.add(project)
    await db.commit()

    logger.info(
        f"[ConfirmSceneReferences] T21-NEW-7 ✅ 场景参考图已确认: "
        f"project={project_id}, chapter={chapter_number}"
    )

    return {
        "success": True,
        "scene_references_confirmed": True,
        "next_stage": "image_generation",
    }


# ===========================================================================
# T22-NEW-5 (2026-05-22): confirm-scenes endpoint — DEPRECATED NOOP
# ===========================================================================
# Founder 5/22 13:37 决策: R4-2 文字层场景确认环节砍掉，Stage 3→4 直连。
# Pipeline R4-2 wait loop 已移除 (pipeline_orchestrator.py)。
# 此 endpoint 保留为 noop，避免旧 frontend 调用 404 报错（向后兼容）。
# NOTE: projects.py 中也有同路径 endpoint 会优先处理请求（FastAPI 路由注册顺序）。
#       本 endpoint 作为防御性 noop，防止新 frontend 意外调用返 404。
# ===========================================================================

@router.post("/{chapter_number}/confirm-scenes")
async def confirm_scenes_noop(
    project_id: str,
    chapter_number: int,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """T22-NEW-5: R4-2 砍掉后的 confirm-scenes noop endpoint。

    不再更新 scenes_confirmed DB 列，不再阻塞 Pipeline。
    直接返回 200 + deprecation warning，向后兼容旧 frontend 调用。
    """
    logger.warning(
        f"[ConfirmScenes] T22-NEW-5: R4-2 wait loop 已移除, "
        f"this endpoint is no-op deprecated "
        f"(project={project_id}, chapter={chapter_number}) — "
        f"Frontend Wave 8 已砍 scene_review，请升级前端"
    )
    return {
        "success": True,
        "scenes_confirmed": True,
        "deprecated": True,
        "message": "R4-2 场景确认环节已移除，此 endpoint 为 noop，无需调用",
    }
