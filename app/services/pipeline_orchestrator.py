"""
Phase 2.0 Pipeline Orchestrator

整合5阶段生成流程：
Stage 1: StoryOutlineGenerator - 故事大纲
Stage 2: CharacterDesigner - 角色设计
Stage 3: ScreenplayWriter - 分场剧本
Stage 4: StoryboardDirector - 分镜脚本
Stage 5: ShotImageGenerator - 镜头图像生成

数据流：
idea → outline.json → characters.json → screenplay.json → storyboard.json → images/
"""

import glob
import json
import logging
import os
import re
import shutil
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Callable, Awaitable
from PIL import Image

logger = logging.getLogger("xuhua")

from app.config import settings
from app.services.story_outline_generator import StoryOutlineGenerator
from app.services.character_designer import CharacterDesigner
from app.services.screenplay_writer import ScreenplayWriter
from app.services.storyboard_director import StoryboardDirector
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig
from app.services.text_overlay_service import TextOverlayService
from app.services.shot_validator import ShotValidator
from app.services.pipeline_schemas import (
    validate_characters,
    validate_storyboard,
    validate_outline,
    validate_screenplay,
    PipelineSchemaError,
)


# RISK-T20-19 (2026-05-19): 单 Shot wall-clock timeout
# 设计:
#   - 720s = 12 min, 略小于 SeedreamGenerator 理论最坏 ~15 min (4 attempts × 210s + 退避 100s)
#   - 用 asyncio.wait_for 包裹 generate_shot_image_phase2_safe 调用
#   - test17 v2 实证: Shot 14 hang 12.5 min, Shot 16 hang 14.2 min — 没 timeout 会拖死整批
#   - 超时按 partial_failure 走 (Frontend "查看并重生" 可救), 不阻塞 Pipeline
#   - 不会丢图: result 标记 wall_clock_timeout, Pipeline 自愈 + Frontend 可重生
SHOT_WALL_CLOCK_TIMEOUT_SEC: int = 720


# P1-1 / P1-2 / BUG-ETA-DISAPPEAR-AT-STAGE-EDGE (Wave 6 / 2026-05-11):
# Stage durations (seconds) for backend-driven ETA — STATIC BASELINE
# RISK-T14-4 (2026-05-13): 改为 dynamic 计算，见 build_stage_durations() 和 estimate_remaining()。
# 此 dict 仅作静态基线兜底（当 actual_shot_count / unique_locations 未知时使用）。
#
# 注意: R4-1 (character_ready) 和 R4-2 (scenes_ready) 是用户等待阶段，
# 不计入 ETA（用户确认时间不是 pipeline 工作时间）。
# estimate_remaining() 会跳过这两个 stage。
#
# 必须覆盖所有 progress_callback 真用过的 stage 名:
#   story_generation / character_design / character_ready / screenplay /
#   scenes_ready (B58 新增) / storyboard / image_preparation / image_generation /
#   bgm / completed
STAGE_DURATIONS = {
    "story_generation": 150,       # Stage 1 Sonnet (~137-180s 实测)
    "character_design": 120,       # Stage 2 Sonnet + portrait 生成
    "character_ready": 0,          # R4-1 用户等待：不计入 ETA（用户时间不是工作时间）
    "screenplay": 213,             # Stage 3 ScreenplayWriter (~213s 实测)
    "scenes_ready": 0,             # R4-2 用户等待：不计入 ETA（同上）
    "storyboard": 236,             # Stage 4 StoryboardDirector (~236s 实测，并行 4 scenes）
    # T21-NEW-7 (2026-05-21 DEC-047): 新增 Stage 4.5 (scene_image_preparation)
    # 真做: 抽取 unique_locations + interior/exterior anchor 生成 (per-location 串行, 跨 location 并行)
    # 实测: 每 location interior ~45s + exterior ~45s = 90s, 4 location 并发 = ~90-180s
    "scene_image_preparation": 180,  # Stage 4.5: 场景参考图生成
    "scene_references_ready": 0,     # R4-3 用户等待: 不计入 ETA (与 character_ready/scenes_ready 一致)
    # T21-NEW-7: image_preparation 改简 (Stage 4.5 抽出场景参考图后只剩 fullbody 串行)
    # 旧: 420s (角色 × 2 + location × 2 串行) → 新: 270s (角色 × fullbody 串行, 跨角色并行)
    "image_preparation": 270,      # 5a 参考图 (fullbody 串行 portrait→fullbody)
    # DEC-028 + RISK-T14-4f: image_generation 不再写死 18 shots，
    # 改由 build_stage_durations(actual_shot_count, max_concurrent) 动态计算。
    # 此静态值作为 actual_shot_count=18 时的基线（D2：18 shots × 60s / max_concurrent=3 = 360s）
    "image_generation": 360,       # 动态算：actual_shot_count × 60 / max_concurrent
    "bgm": 120,
    "completed": 0,               # 终态，ETA=0
}


def build_stage_durations(
    actual_shot_count: int = 18,
    unique_location_count: int = 3,
    max_concurrent: int = 3,
) -> dict:
    """
    RISK-T14-4 (2026-05-13): 根据实际 shot 数、location 数、并发数动态计算 STAGE_DURATIONS。

    Args:
        actual_shot_count: 真实 shot 数（DEC-028 不截断后可能 > 18）
        unique_location_count: 场景数（影响 image_preparation 参考图串行时间）
        max_concurrent: Shot 并发数（IMAGE_MAX_CONCURRENT，默认 3）

    Returns:
        完整 stage_durations dict，与 STAGE_DURATIONS 结构相同。

    设计原则:
        - character_ready / scenes_ready: 0（用户等待不计入 ETA）
        - image_preparation: 角色参考图（portrait+fullbody 串行）+ 场景参考图（内外景串行）
        - image_generation: actual_shot_count × 60s / max_concurrent（Seedream ~23s/张 + overhead）
    """
    # Stage 1-4 参考实测数据，不依赖参数
    durations = dict(STAGE_DURATIONS)  # 从静态基线 copy

    # T21-NEW-7 (2026-05-21 DEC-047): scene_image_preparation 单独算 (与 image_preparation 分开)
    # 实测: 每 location interior ~45s + exterior ~45s = 90s, 3 path 并行
    # 旧 image_preparation 包含 location 部分, 现 Stage 4.5 抽出
    scene_prep_seconds = unique_location_count * 90  # location 串行 interior→exterior
    # 跨 location 并行最多 3 路 (与 SceneReferenceManager _loc_sem = Semaphore(3) 同步)
    scene_prep_seconds = int(scene_prep_seconds / min(unique_location_count, 3) if unique_location_count > 0 else 90)
    durations["scene_image_preparation"] = max(scene_prep_seconds, 90)  # 最少 90s

    # image_preparation (Stage 5 5a): 只剩 fullbody 串行 (portrait T20-50 信任不重生)
    # 实测: 每角色 fullbody ~45s, 跨角色最多 3 路并行
    char_count = max(1, actual_shot_count // 6)  # 粗估角色数（6 shots per char 经验值）
    char_count = min(char_count, 6)  # 最多 6 角色
    image_prep_seconds = int(char_count * 45 / min(char_count, 3))  # 3 路并行
    durations["image_preparation"] = max(image_prep_seconds, 90)  # 最少 90s

    # image_generation: shot 数 × 单张生成时间 / 并发数
    # RISK-T20-9 (2026-05-18) 修正：60 → 80 s/shot
    # 实测 test18 second run: 19 shots × 80 / 3 = 507s ≈ 8.5 min ≈ 实测 9 min (低估 ~6%)
    # 旧 60 s/shot: 19 × 60 / 3 = 380s ≈ 6.3 min ≈ 实测 9 min (低估 ~42%) → ETA "偏快 100%"
    # 80 s/shot 含 Seedream 基础 ~23s + IncompleteRead retry overhead + 长尾 shot (单 shot 可至 118s)
    # 设计取舍：稍偏保守好过让用户"已显示即将完成但还要等 5 分钟"——失信比多等几秒严重
    per_shot_seconds = 80
    image_gen_seconds = int(actual_shot_count * per_shot_seconds / max(max_concurrent, 1))
    durations["image_generation"] = max(image_gen_seconds, 60)  # 最少 1 min

    return durations


def estimate_remaining(
    current_stage: str,
    stage_progress: float = 0.0,
    actual_shot_count: int = 18,
    unique_location_count: int = 3,
    max_concurrent: int = 3,
) -> int:
    """
    P1-2 / BUG-ETA-DISAPPEAR-AT-STAGE-EDGE / RISK-T14-4 (2026-05-13):
    根据当前 stage、阶段内进度、实际 shot 数动态估算剩余工作时间。

    Args:
        current_stage: 当前 stage 名（必须是 STAGE_DURATIONS 的 key 之一）
        stage_progress: 0.0-1.0，当前 stage 已完成比例
        actual_shot_count: 真实 shot 数（动态 ETA 核心参数，DEC-028 不截断后影响 ETA）
        unique_location_count: 场景数（影响参考图时间）
        max_concurrent: 并发数（影响 image_generation 时间）

    Returns:
        剩余工作秒数（至少 5s，"completed" 返 0）。
        unknown stage 返 5 兜底，避免前端 ETA 消失。

    RISK-T14-4e 修复:
        - character_ready / scenes_ready 设为 0：ETA 不含用户等待 timeout（R4-1/R4-2）
        - 切换 stage 时 ETA 平滑：旧 stage 完成的 progress 延续到新 stage 计算

    Wave 6 修复:
        - unknown stage 返 5（兜底），completed 返 0
    """
    # 显式终态
    if current_stage == "completed":
        return 0

    # 动态计算 stage durations
    stage_durations = build_stage_durations(actual_shot_count, unique_location_count, max_concurrent)

    seq = list(stage_durations.keys())
    try:
        idx = seq.index(current_stage)
    except ValueError:
        # Unknown stage — 兜底，避免前端 ETA 消失
        logger.warning(f"[estimate_remaining] Unknown stage={current_stage!r}, fallback to 5s")
        return 5

    # stage_progress clamp 到 [0.0, 1.0]
    sp = max(0.0, min(1.0, float(stage_progress)))
    remaining = int(stage_durations[current_stage] * (1.0 - sp))
    for s in seq[idx + 1:]:
        remaining += stage_durations[s]
    # 最小 5s 兜底，避免显示 "0 秒" 然后突然不变
    return max(remaining, 5)


class PipelineCostLimitExceeded(Exception):
    """Pipeline API 成本超过单次上限时抛出"""
    pass


class PipelineCostTracker:
    """Pipeline 运行期间的 API 成本追踪

    ARCH-4 (TASK-PARALLEL-M1): 双层追踪
    - 层 1: 内存追踪（同步，快，当前 run 精确）
    - 层 2: DB 追踪（异步，查 api_cost_logs 表，跨 run 累计）
      通过 check_db_cost_limit() 在 Stage 5 开始前调用，确保 $10 熔断有真实数据支撑。
    """

    def __init__(self, cost_limit: float = 10.0, project_id: Optional[int] = None):
        self.cost_limit = cost_limit  # 单次 Pipeline 上限（默认 $10）
        self.total_cost = 0.0
        self.calls = []  # 记录每次 API 调用
        self.project_id = project_id  # 用于 DB 查询（ARCH-4）

    def add_cost(self, service: str, cost: float, detail: str = "") -> None:
        """
        记录一次 API 调用费用。

        Args:
            service: 服务名称（如 "sonnet", "gemini_nb2"）
            cost: 本次调用费用（美元）
            detail: 调用详情（如 "Stage 1", "Shot 3"）

        Raises:
            PipelineCostLimitExceeded: 累计成本超过上限时抛出
        """
        self.total_cost += cost
        self.calls.append({"service": service, "cost": cost, "detail": detail})
        if self.total_cost > self.cost_limit:
            raise PipelineCostLimitExceeded(
                f"Pipeline 成本已超过上限 ${self.cost_limit}! "
                f"当前: ${self.total_cost:.2f}, "
                f"最近调用: {detail}"
            )

    async def check_db_cost_limit(self, detail: str = "DB cost check") -> None:
        """
        ARCH-4: 查询 api_cost_logs 表获取项目历史累计成本，叠加内存追踪后检查上限。

        应在 Stage 5（高成本阶段）开始前调用一次，确保熔断判断有真实数据。
        失败时（DB 不可达等）记录 warning 但不抛异常，降级到纯内存追踪。

        Raises:
            PipelineCostLimitExceeded: 历史累计 + 当前 run 超过上限时抛出
        """
        if self.project_id is None:
            logger.debug("[CostTracker] project_id 为 None，跳过 DB 成本查询")
            return
        try:
            from sqlalchemy import select, func as sa_func
            from app.database import async_session_maker
            from app.models.api_cost_log import ApiCostLog

            async with async_session_maker() as session:
                result = await session.execute(
                    select(sa_func.coalesce(sa_func.sum(ApiCostLog.cost_usd), 0.0)).where(
                        ApiCostLog.project_id == self.project_id
                    )
                )
                db_total: float = float(result.scalar() or 0.0)

            combined_total = db_total + self.total_cost
            logger.info(
                f"[CostTracker] ARCH-4 DB 查询: project_id={self.project_id}, "
                f"db_total=${db_total:.4f}, in_memory=${self.total_cost:.4f}, "
                f"combined=${combined_total:.4f}, limit=${self.cost_limit:.2f}"
            )

            if combined_total > self.cost_limit:
                raise PipelineCostLimitExceeded(
                    f"Pipeline 累计成本（DB+本次）超过上限 ${self.cost_limit}! "
                    f"DB历史: ${db_total:.2f}, 本次: ${self.total_cost:.2f}, "
                    f"合计: ${combined_total:.2f}. detail={detail}"
                )

        except PipelineCostLimitExceeded:
            raise  # 熔断异常直接上抛
        except Exception as e:
            logger.warning(
                f"[CostTracker] ⚠️ DB 成本查询失败（降级到纯内存追踪）: "
                f"project_id={self.project_id}, error={type(e).__name__}: {e}"
            )


R8_DATA_DIR = "test_output/manualtest/e2e_regression_r8/20260316_145613/story_A/20260316_145614"


class Phase2PipelineOrchestrator:
    """
    Phase 2.0 完整生成流程编排器

    使用方法：
    ```python
    orchestrator = Phase2PipelineOrchestrator(output_dir="./output")
    result = await orchestrator.run(
        idea="雨夜公交站，错过末班车的三个人",
        style_preset="anime",
        target_duration_minutes=3
    )
    ```
    """

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir

        # 初始化各阶段服务
        self.outline_generator = StoryOutlineGenerator()
        self.character_designer = CharacterDesigner()
        self.screenplay_writer = ScreenplayWriter()
        self.storyboard_director = StoryboardDirector()
        self.image_generator = ImageGenerator()

        # T9: 文字渲染配置（与 generate_shot_image_phase2() 默认值同步）
        self.use_native_text = True
        # T17: Shot 后置视觉验证
        self.shot_validator = ShotValidator()

        # 状态跟踪
        self.current_stage = None
        self.stage_results = {}

    async def run(
        self,
        idea: str,
        style_preset: str = "anime",
        target_duration_minutes: int = 3,
        language: str = "zh-CN",
        character_count: int = 3,
        generate_images: bool = True,
        max_concurrent_images: int = 2,
        shots_limit: int = 0,
        custom_style_analysis: dict = None,
        character_seeds: dict = None,
        scene_seeds: dict = None,
        confirmed_outline: dict = None,
        project_uuid: str = None,
        chapter_id: Optional[int] = None,  # ARCH-1: 用于批量写入 chapter_scene_images
        aspect_ratio: str = "2:3",  # D.15 P0: 用户选择的画幅，传给真生图调用，不再 hardcoded
        user_selected_mood: Optional[str] = None,  # B33: Stage A 用户选的情绪基调，透传给 BGM
        job_id: Optional[int] = None,  # RISK-T15-9 (Wave 9 / DEC-030): mid-stage failed_count 实时累加用
        progress_callback: Optional[Callable[..., Awaitable]] = None,
        checkpoint_callback: Optional[Callable[..., Awaitable]] = None,
        start_from_stage: int = 1,  # RISK-T17-8: 原地重启入口，1=从头, 4=从Stage4开始（跳过1-3）
    ) -> dict:
        """
        运行完整的5阶段生成流程

        Args:
            idea: 用户创意
            style_preset: 视觉风格预设
            target_duration_minutes: 目标时长（分钟）
            language: 语言
            character_count: 角色数量
            generate_images: 是否生成图像（可设为False只生成文本）
            max_concurrent_images: 最大并发图像生成数
            shots_limit: 限制生成的shot数量（0=不限制）

        Returns:
            完整的生成结果
        """
        start_time = datetime.now()
        project_id = project_uuid or start_time.strftime("%Y%m%d_%H%M%S")
        project_dir = os.path.join(self.output_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Phase 2.0 Pipeline 开始")
        print(f"{'='*60}")
        print(f"Project ID: {project_id}")
        print(f"Idea: {idea}")
        _style_label = f"custom ({custom_style_analysis.get('style_display_name', 'custom')})" if custom_style_analysis else style_preset
        print(f"Style: {_style_label}")
        print(f"Target: {target_duration_minutes}分钟")
        print(f"{'='*60}\n")
        logger.info(f"[Pipeline] ========== Pipeline 开始 ==========")
        logger.info(f"[Pipeline] project_id={project_id}, style={_style_label}, duration={target_duration_minutes}min")
        logger.info(f"[Pipeline] idea: {idea[:100]}{'...' if len(idea) > 100 else ''}")
        logger.info(f"[Pipeline] has_confirmed_outline={'是' if confirmed_outline else '否'}, generate_images={generate_images}")

        try:
            # RISK-T17-8: 原地重启 — 从 disk 加载已完成 Stage 的结果，跳过重跑
            # start_from_stage: 1=从头（默认）, 2=跳过Stage1, 3=跳过Stage1-2, 4=跳过Stage1-3
            # 当 start_from_stage > 1 时，从 project_dir 读取已有的 JSON 文件
            if start_from_stage > 1:
                logger.info(
                    f"[Pipeline] RISK-T17-8: start_from_stage={start_from_stage}, "
                    f"从 disk 加载 Stage 1-{start_from_stage - 1} 结果"
                )
                _restart_dir = os.path.join(self.output_dir, project_uuid or project_id)
                # Stage 1: 加载 outline
                _outline_path = os.path.join(_restart_dir, "1_outline.json")
                if os.path.exists(_outline_path):
                    with open(_outline_path, encoding="utf-8") as _f:
                        _loaded_outline = json.load(_f)
                    self.stage_results["outline"] = _loaded_outline
                    logger.info(f"[Pipeline] RISK-T17-8: 已从 disk 加载 1_outline.json")
                else:
                    logger.warning(
                        f"[Pipeline] RISK-T17-8: 找不到 1_outline.json，start_from_stage 降级为 1"
                    )
                    start_from_stage = 1

            if start_from_stage > 2 and "outline" in self.stage_results:
                # Stage 2: 加载 characters
                _chars_path = os.path.join(_restart_dir, "2_characters.json")
                if os.path.exists(_chars_path):
                    with open(_chars_path, encoding="utf-8") as _f:
                        _loaded_chars = json.load(_f)
                    # 支持两种格式: list 或 {"characters": [...]}
                    if isinstance(_loaded_chars, list):
                        _loaded_chars = {"characters": _loaded_chars}
                    self.stage_results["characters"] = _loaded_chars
                    logger.info(f"[Pipeline] RISK-T17-8: 已从 disk 加载 2_characters.json")
                else:
                    logger.warning(
                        f"[Pipeline] RISK-T17-8: 找不到 2_characters.json，start_from_stage 降级为 2"
                    )
                    start_from_stage = 2

            if start_from_stage > 3 and "characters" in self.stage_results:
                # Stage 3: 加载 screenplay
                _sp_path = os.path.join(_restart_dir, "3_screenplay.json")
                if os.path.exists(_sp_path):
                    with open(_sp_path, encoding="utf-8") as _f:
                        _loaded_sp = json.load(_f)
                    self.stage_results["screenplay"] = _loaded_sp
                    logger.info(f"[Pipeline] RISK-T17-8: 已从 disk 加载 3_screenplay.json")
                else:
                    logger.warning(
                        f"[Pipeline] RISK-T17-8: 找不到 3_screenplay.json，start_from_stage 降级为 3"
                    )
                    start_from_stage = 3

            # ARCH-4 修复 + Bug 1 fix (round 3):
            # 策略: project_uuid 有值 → 查 DB；
            #        project_uuid 为 None（driver/test 模式）→ 新建临时 Project record 拿 integer id
            # 目的: 保证 api_cost_logs.project_id 永远是真实 integer，不是 None
            db_project_id: Optional[int] = None
            try:
                from app.database import async_session_maker
                from sqlalchemy import select
                from app.models.project import Project as _Project

                if project_uuid:
                    # 生产路径: FastAPI 已创建 Project record，直接查 integer id
                    async with async_session_maker() as _id_db:
                        _id_result = await _id_db.execute(
                            select(_Project.id).where(_Project.uuid == project_uuid)
                        )
                        db_project_id = _id_result.scalar_one_or_none()
                    if db_project_id:
                        logger.info(f"[Pipeline] ARCH-4: project_uuid={project_uuid} → db_project_id={db_project_id}")
                    else:
                        logger.warning(f"[Pipeline] ARCH-4: project_uuid={project_uuid} 在 DB 找不到 integer id，降级内存追踪")
                else:
                    # 测试/driver 脚本路径: project_uuid 为 None，新建临时 Project record
                    async with async_session_maker() as _id_db:
                        _tmp_project = _Project(
                            uuid=project_id,        # 用时间戳 project_id 作 uuid 占位
                            user_id=0,              # 0 = 测试模式（无真实用户）
                            title=idea[:100] if idea else "test_run",
                            original_idea=idea or "test_run",
                            style_preset=style_preset or "anime",
                        )
                        _id_db.add(_tmp_project)
                        await _id_db.commit()
                        await _id_db.refresh(_tmp_project)
                        db_project_id = _tmp_project.id
                    logger.info(
                        f"[Pipeline] ARCH-4 Bug1 fix: 无 project_uuid，新建临时 Project record "
                        f"id={db_project_id}, uuid={project_id}"
                    )
            except Exception as _e:
                logger.warning(f"[Pipeline] ARCH-4: 查询/创建 db_project_id 失败（降级内存追踪）: {_e}")

            # 成本熔断: 单次 Pipeline 成本上限（ARCH-4: 传入 db_project_id 启用跨 run DB 查询）
            cost_tracker = PipelineCostTracker(cost_limit=settings.PIPELINE_COST_LIMIT, project_id=db_project_id)

            # RB-5 + B-7: 启动空白期 — 根据是否有 confirmed_outline 调整初始消息
            if progress_callback:
                if confirmed_outline:
                    await progress_callback("character_design", 2, "大纲已确认，正在设计角色...")
                else:
                    await progress_callback("story_generation", 2, "正在构思故事大纲...")

            # ============================================================
            # Stage 1: 故事大纲生成
            # ============================================================
            self.current_stage = "Stage 1: StoryOutlineGenerator"
            print(f"\n{'='*40}")
            print(f"Stage 1: 生成故事大纲")
            print(f"{'='*40}")

            if start_from_stage > 1 and "outline" in self.stage_results:
                # RISK-T17-8: 从 disk 已加载，跳过 LLM 生成
                outline = self.stage_results["outline"]
                print(f"  [RISK-T17-8] 跳过 Stage 1（已从 disk 加载 outline）")
                logger.info(f"[Pipeline] RISK-T17-8: 跳过 Stage 1 LLM 生成，使用 disk 缓存")
            elif confirmed_outline:
                print(f"  使用用户确认后的大纲（跳过 LLM 生成）")
                outline = confirmed_outline
            else:
                outline = await self.outline_generator.generate(
                    idea=idea,
                    style_preset=style_preset,
                    target_duration_minutes=target_duration_minutes,
                    language=language,
                    character_count=character_count
                )
                # 成本计数: Stage 1 Sonnet 调用（每次 $0.05 保守估算）
                cost_tracker.add_cost("sonnet", 0.05, "Stage 1")

            self.stage_results["outline"] = outline

            # BGM-1: 注入 music_hint（风格→音乐提示映射）到 outline dict
            try:
                from app.services.style_music_hints import get_raw_hint as _get_raw_hint
                outline["music_hint"] = _get_raw_hint(style_preset)
                logger.info(f"[Pipeline] BGM-1: outline.music_hint 已注入 ({style_preset}): {outline['music_hint'][:80]}...")
            except Exception as _bm_e:
                logger.warning(f"[Pipeline] BGM-1: music_hint 注入失败（非阻塞）: {_bm_e}")

            # N13-FIX: 自动补全 spouse_of 对称关系
            family_rels = outline.get("family_relationships", [])
            for rel in list(family_rels):  # 遍历副本，避免修改遍历中的列表
                if rel.get("relationship") == "spouse_of":
                    reverse_exists = any(
                        r.get("from") == rel["to"] and r.get("to") == rel["from"]
                        for r in family_rels
                    )
                    if not reverse_exists:
                        family_rels.append({
                            "from": rel["to"],
                            "to": rel["from"],
                            "relationship": "spouse_of"
                        })
                        print(f"  [N13-FIX] 补全 spouse_of: {rel['to']} → {rel['from']}")

            self._save_json(project_dir, "1_outline.json", outline)

            # HE-BACKEND-1: Schema 验证 — Stage 1 输出（大纲完整性检查）
            validate_outline(outline, "Stage 1 -> 2")

            print(f"✅ Stage 1 完成: {outline.get('title', 'N/A')}")
            # P1-1: Stage 1 完成 → 切换到 character_design stage（entry callback）
            if progress_callback:
                await progress_callback("character_design", 5, "大纲生成完成，正在设计角色...")

            # ============================================================
            # Stage 2: 角色设计
            # ============================================================
            self.current_stage = "Stage 2: CharacterDesigner"
            print(f"\n{'='*40}")
            print(f"Stage 2: 设计角色")
            print(f"{'='*40}")

            # RISK-T14-5-v2: Stage 启动时立即 update jobs，避免进度卡死
            if progress_callback:
                try:
                    await progress_callback("character_design", 5, "正在设计角色...")
                except Exception as _cb_e:
                    logger.warning(f"[Pipeline] Stage 2 startup progress_callback 失败: {_cb_e}")

            if start_from_stage > 2 and "characters" in self.stage_results:
                # RISK-T17-8: 从 disk 已加载，跳过 LLM 生成
                characters = self.stage_results["characters"]
                print(f"  [RISK-T17-8] 跳过 Stage 2（已从 disk 加载 characters）")
                logger.info(f"[Pipeline] RISK-T17-8: 跳过 Stage 2 LLM 生成，使用 disk 缓存")
            else:
                characters = await self.character_designer.design(
                    outline,
                    style_preset=style_preset,  # T20-46: 传入风格预设，触发 STYLE_INFUSION_RULES
                )
                # 成本计数: Stage 2 Sonnet 调用
                cost_tracker.add_cost("sonnet", 0.05, "Stage 2")

                self.stage_results["characters"] = characters
                self._save_json(project_dir, "2_characters.json", characters)

                # HE-BACKEND-1: Schema 验证 — Stage 2 输出
                validate_characters(characters, "Stage 2 -> 3")

            char_names = [c.get("name", "N/A") for c in characters.get("characters", [])]
            print(f"✅ Stage 2 完成: {', '.join(char_names)}")

            # P1-5 / P1-1: LLM 角色设计完成 → 告知前端正在生成画像（portrait gen 开始前）
            if progress_callback:
                await progress_callback("character_design", 6, "角色设计完成，正在生成画像...")

            # UX-1 + UX-14: Stage 2 后立即为每个角色生成 portrait（肖像）
            # 非阻塞：失败时只记录警告，不中断 Pipeline
            # 用 generate_images 开关控制（跳图模式时跳过）
            if generate_images and not settings.SKIP_IMAGE_GENERATION:
                print("\n--- UX-1: 生成角色肖像（portrait）---")
                try:
                    _char_refs_dir = os.path.join(project_dir, "character_refs")
                    os.makedirs(_char_refs_dir, exist_ok=True)
                    _portrait_ref_manager = ReferenceImageManager()
                    _portrait_style = ProjectStyleConfig(style_preset=style_preset)
                    if custom_style_analysis:
                        from app.services.style_enforcer import StyleEnforcer as _SE
                        _portrait_style.custom_enforcement = _SE.create_custom_enforcement(custom_style_analysis)
                    _char_list = characters.get("characters", [])
                    _portrait_updated = False
                    for _char in _char_list:
                        _char_id = _char.get("id", "unknown")
                        _char_name = _char.get("name", _char_id)
                        print(f"  生成 {_char_name} 肖像...", end=" ")
                        try:
                            _portrait_result = await _portrait_ref_manager.generate_character_reference(
                                character=_char,
                                project_style=_portrait_style,
                                image_generator=self.image_generator,
                                ref_type="portrait",
                                aspect_ratio=aspect_ratio,  # B39/D.15: 透传用户选择的宽高比
                            )
                            if _portrait_result.get("success") and _portrait_result.get("pil_image"):
                                _portrait_path = os.path.join(_char_refs_dir, f"{_char_id}_portrait.png")
                                _portrait_result["pil_image"].save(_portrait_path)
                                _portrait_http_url = f"/static/outputs/{project_id}/character_refs/{_char_id}_portrait.png"
                                _char["portrait_url"] = _portrait_http_url
                                _portrait_updated = True
                                print(f"✅ ({_portrait_http_url})")
                                logger.info(f"[Pipeline] UX-1: {_char_name} portrait → {_portrait_http_url}")
                            else:
                                print(f"❌ {_portrait_result.get('error', 'unknown error')}")
                                logger.warning(f"[Pipeline] UX-1: {_char_name} portrait 生成失败: {_portrait_result.get('error')}")
                        except Exception as _pe:
                            print(f"❌ 异常: {_pe}")
                            logger.warning(f"[Pipeline] UX-1: {_char_name} portrait 生成异常: {_pe}")
                    if _portrait_updated:
                        self._save_json(project_dir, "2_characters.json", characters)
                        logger.info(f"[Pipeline] UX-14: 2_characters.json 已更新（含 portrait_url）")
                except Exception as _portrait_batch_e:
                    print(f"⚠️ UX-1 portrait 批量生成异常（非阻塞）: {_portrait_batch_e}")
                    logger.warning(f"[Pipeline] UX-1: portrait 批量生成异常（非阻塞）: {_portrait_batch_e}")

            # B-6: Stage 2 完成后存中间结果到 chapter 表（portrait_url 已写入 characters）
            if checkpoint_callback:
                await checkpoint_callback(
                    "characters_json", characters.get("characters", [])
                )
            # R4-1: Stage 2 后发 character_ready 信号，然后真正等待用户确认
            # 前端检测到 stage === "character_ready" 后弹出角色/场景确认
            # 用户点"确认" → 调 confirm-characters API → characters_confirmed = True
            # Pipeline 轮询 DB 等待确认，超时 5 分钟自动继续
            if progress_callback:
                await progress_callback("character_ready", 10, "角色设计完成，请确认角色和场景")

            # R4-1: 轮询等待用户确认角色
            # RISK-T17-8: 原地重启时跳过等待（角色已在上次运行中确认）
            max_wait = 1800  # 30 分钟超时（前端会主动调 confirm API）
            waited = 0
            confirmed = False
            if start_from_stage > 2:
                confirmed = True
                logger.info(f"[Pipeline] RISK-T17-8: start_from_stage={start_from_stage}，跳过 R4-1 等待（角色已在上次运行中确认）")
            logger.info(f"[Pipeline] R4-1: 开始等待用户确认角色 (超时 {max_wait}s)")
            if project_uuid and not confirmed:
                from app.database import async_session_maker
                from sqlalchemy import select
                from app.models.project import Project
                while waited < max_wait:
                    await asyncio.sleep(2)
                    waited += 2
                    try:
                        async with async_session_maker() as check_db:
                            result = await check_db.execute(
                                select(Project.characters_confirmed).where(Project.uuid == project_uuid)
                            )
                            row = result.scalar_one_or_none()
                            if row:
                                confirmed = True
                                print(f"  [R4-1] ✅ 用户已确认角色 (等待 {waited}s)")
                                logger.info(f"[Pipeline] R4-1: ✅ 用户已确认角色 (等待 {waited}s)")
                                break
                    except Exception as e:
                        print(f"  [R4-1] ⚠️ 查询 characters_confirmed 失败: {e}")
                        logger.warning(f"[Pipeline] R4-1: ⚠️ 查询 characters_confirmed 失败: {e}")
                    # 每 30s 打一次轮询状态日志 + update jobs 保持 ETA 刷新
                    if waited % 30 == 0:
                        logger.info(f"[Pipeline] R4-1: 仍在等待用户确认... (已等待 {waited}s)")
                        if progress_callback:
                            try:
                                await progress_callback("character_ready", 10, "等待确认角色设计...")
                            except Exception as _r41_cb_e:
                                logger.debug(f"[Pipeline] R4-1 progress_callback 失败（非阻塞）: {_r41_cb_e}")
                if not confirmed:
                    print(f"  [R4-1] ⏰ 等待超时 ({max_wait}s)，自动继续")
                    logger.warning(f"[Pipeline] R4-1: ⏰ 等待超时 ({max_wait}s)，自动继续")

                # ============================================================
                # B52-fix v3 (Wave 6 / 2026-05-11): in-memory characters 必须从 DB reload
                # ============================================================
                # 真因（Explore agent 2026-05-11 18:35 very-thorough 审计确认）:
                #   - L380 `characters = await character_designer.design(outline)` 是 Stage 2 输出
                #     这个 python in-memory dict **永不 reload**
                #   - 用户在 R4-1 期间通过 /adjust 改了 DB chapter.characters_json（如发色改亚麻青）
                #   - R4-1 wait loop 只读 Project.characters_confirmed 字段，**不重读 chapter.characters_json**
                #   - 结果：Stage 4 storyboard_director 拿到老黑发 characters dict，
                #     写出 image_prompt 含 "black hair / dark hair / jet-black ponytail"
                #   - Stage 5 Seedream 看 prompt 文字 > 参考图 attention → 部分 shot 漂回黑发
                # 修复：R4-1 退出后从 DB reload characters dict，让 Stage 3/4 拿到最新 adjust 后数据
                # 关键时序：此时 Stage 3/4 尚未跑 → reload 后 Stage 4 LLM 自然拿亚麻青 description，
                # 无需触发 Stage 4 重跑
                #
                # Shot 7 风险注意：本 reload 直接覆盖整个 characters dict，
                # 不做按 character_id 的字段级合并 — chapter.characters_json 是 adjust API 改完
                # 重新写入的完整快照，对未被 adjust 的角色（如 char_003 王阿姨黑发）保留原值，
                # 不会误改其他角色。
                if confirmed:
                    try:
                        from app.models.chapter import Chapter as _Chapter

                        async with async_session_maker() as _reload_db:
                            # 一次查询：用 project_uuid 通过 join 拿到 chapter
                            _proj_result = await _reload_db.execute(
                                select(Project.id).where(Project.uuid == project_uuid)
                            )
                            _proj_id = _proj_result.scalar_one_or_none()
                            if _proj_id is None:
                                logger.warning(
                                    f"[Pipeline] B52-fix v3: project_uuid={project_uuid} 未找到，跳过 reload"
                                )
                            else:
                                _ch_result = await _reload_db.execute(
                                    select(_Chapter).where(
                                        _Chapter.project_id == _proj_id,
                                        _Chapter.chapter_number == 1,
                                    )
                                )
                                _chapter = _ch_result.scalar_one_or_none()
                                if _chapter and _chapter.characters_json:
                                    _raw = _chapter.characters_json
                                    _parsed = json.loads(_raw) if isinstance(_raw, str) else _raw
                                    # chapter.characters_json 通常是 List[character_dict]
                                    # in-memory characters 是 {"characters": [...]} 格式
                                    if isinstance(_parsed, list):
                                        characters = {"characters": _parsed}
                                    elif isinstance(_parsed, dict) and "characters" in _parsed:
                                        characters = _parsed
                                    else:
                                        # 极端兜底（不应触发）
                                        logger.warning(
                                            f"[Pipeline] B52-fix v3: 未知 characters_json 格式: {type(_parsed)}"
                                        )
                                        characters = {"characters": []}
                                    self.stage_results["characters"] = characters
                                    _char_count = len(characters.get("characters", []))
                                    print(f"  [B52-fix v3] ✅ characters reloaded from DB (count={_char_count})")
                                    logger.info(
                                        f"[Pipeline] B52-fix v3: characters reloaded from DB "
                                        f"after R4-1 confirm, count={_char_count}"
                                    )
                                    # 同步落盘 2_characters.json 仅作调试可见（不影响生图，已 grep 验证 services/*.py 无人读此文件）
                                    try:
                                        self._save_json(project_dir, "2_characters.json", characters)
                                    except Exception as _save_e:
                                        logger.debug(
                                            f"[Pipeline] B52-fix v3: 2_characters.json 落盘失败（非阻塞）: {_save_e}"
                                        )
                                else:
                                    logger.warning(
                                        f"[Pipeline] B52-fix v3: chapter.characters_json 为空，"
                                        f"保留 in-memory Stage 2 输出"
                                    )
                    except Exception as _reload_e:
                        logger.warning(
                            f"[Pipeline] B52-fix v3: characters reload 失败（非阻塞）: {_reload_e}"
                        )
            else:
                # 无 project_uuid（手动测试模式）— 直接继续
                print(f"  [R4-1] 无 project_uuid，跳过等待确认")
                logger.info(f"[Pipeline] R4-1: 无 project_uuid，跳过等待确认")

            # ============================================================
            # Stage 3: 分场剧本
            # ============================================================
            self.current_stage = "Stage 3: ScreenplayWriter"
            print(f"\n{'='*40}")
            print(f"Stage 3: 编写分场剧本")
            print(f"{'='*40}")

            # RISK-T14-5-v2: Stage 启动时立即 update jobs，避免进度卡死
            if progress_callback:
                try:
                    await progress_callback("screenplay", 11, "正在编写分场剧本...")
                except Exception as _cb_e:
                    logger.warning(f"[Pipeline] Stage 3 startup progress_callback 失败: {_cb_e}")

            if start_from_stage > 3 and "screenplay" in self.stage_results:
                # RISK-T17-8: 从 disk 已加载，跳过 LLM 生成
                screenplay = self.stage_results["screenplay"]
                print(f"  [RISK-T17-8] 跳过 Stage 3（已从 disk 加载 screenplay）")
                logger.info(f"[Pipeline] RISK-T17-8: 跳过 Stage 3 LLM 生成，使用 disk 缓存")
                scene_count = len(screenplay.get("scenes", []))
                beat_count = screenplay.get("total_action_beats", 0)
                print(f"✅ Stage 3 (缓存): {scene_count}场戏, {beat_count}个动作节拍")
            else:
                screenplay = await self.screenplay_writer.write(
                    outline, characters,
                    family_relationships=outline.get("family_relationships", []),
                    progress_callback=progress_callback,
                )
                # 成本计数: Stage 3 Sonnet 调用
                cost_tracker.add_cost("sonnet", 0.05, "Stage 3")

                self.stage_results["screenplay"] = screenplay
                self._save_json(project_dir, "3_screenplay.json", screenplay)

                # HE-BACKEND-1: Schema 验证 — Stage 3 输出（剧本完整性检查）
                validate_screenplay(screenplay, "Stage 3 -> 4")

                # B-6: Stage 3 完成后存中间结果到 chapter 表
                if checkpoint_callback:
                    await checkpoint_callback("scenes_json", screenplay.get("scenes", []))

                scene_count = len(screenplay.get("scenes", []))
                beat_count = screenplay.get("total_action_beats", 0)
                print(f"✅ Stage 3 完成: {scene_count}场戏, {beat_count}个动作节拍")

            # ============================================================
            # T22-NEW-5 (2026-05-22): R4-2 wait loop 已移除
            # ============================================================
            # Founder 5/22 13:37 决策: "/scenes 文字层场景确认页可以跳过，不需要用户去修改确认了"
            # Stage 3 完成后直接进 Stage 4 (storyboard), 无需等用户确认
            #
            # 保留: R4-1 (character_review) + R4-3 (scene_references_review) 仍然有效
            # 废弃: scenes_confirmed DB 列保留 (向后兼容), 运行时不再使用
            logger.info("[Pipeline] T22-NEW-5: Stage 3 完成，直接进 Stage 4 (R4-2 wait loop 已移除)")

            # P1-1: Stage 3 完成 → 立即切换到 storyboard stage（无 R4-2 等待）
            if progress_callback:
                await progress_callback("storyboard", 35, "剧本编写完成，正在创建分镜...")

            # ============================================================
            # Stage 4: 分镜脚本
            # ============================================================
            self.current_stage = "Stage 4: StoryboardDirector"
            print(f"\n{'='*40}")
            print(f"Stage 4: 创建分镜脚本")
            print(f"{'='*40}")

            visual_tone = outline.get("visual_tone", {})
            storyboard = await self.storyboard_director.direct(
                screenplay=screenplay,
                characters=characters,
                visual_tone=visual_tone,
                style_preset=style_preset,
                characters_overview=outline.get("characters_overview", []),
                family_relationships=outline.get("family_relationships", []),
                progress_callback=progress_callback,
                chapter_duration_minutes=target_duration_minutes,  # O-2: 传入时长用于 shot cap
            )
            # 成本计数: Stage 4 Sonnet 调用
            cost_tracker.add_cost("sonnet", 0.05, "Stage 4")

            self.stage_results["storyboard"] = storyboard
            self._save_json(project_dir, "4_storyboard.json", storyboard)

            # HE-BACKEND-1: Schema 验证 — Stage 4 输出 (特别是 image_prompt 纯英文)
            validate_storyboard(storyboard, "Stage 4 -> 5")

            # T20-27 (2026-05-19): text_overlay fallback — LLM 偶有遗漏时用 narration_segment 填充
            # 仅对有出场角色且 text_overlay.chinese_text 为空的 shot 触发
            for _shot in storyboard.get("shots", []):
                _overlay = _shot.get("text_overlay") or {}
                _chinese_text = _overlay.get("chinese_text")
                _is_empty = (
                    not _chinese_text
                    or (isinstance(_chinese_text, str) and not _chinese_text.strip())
                    or (isinstance(_chinese_text, list) and not any(s.strip() for s in _chinese_text if isinstance(s, str)))
                )
                if _shot.get("characters_in_scene") and _is_empty:
                    _narration = (_shot.get("narration_segment") or "")[:25]
                    if _narration:
                        _shot["text_overlay"] = {
                            "text_type": "narration",
                            "chinese_text": _narration,
                            "speaker_position": "bottom",
                        }
                        logger.warning(
                            f"[T20-27] shot {_shot.get('shot_id')} fallback overlay from narration: {repr(_narration[:20])}"
                        )

            # 保存prompt质量报告
            self._save_prompt_quality_report(storyboard, project_dir)

            # B-6: Stage 4 完成后存中间结果到 chapter 表
            if checkpoint_callback:
                await checkpoint_callback("storyboard_json", storyboard)

            shot_count = len(storyboard.get("shots", []))
            print(f"✅ Stage 4 完成: {shot_count}个镜头")

            # ============================================================
            # T21-NEW-7 DEC-047 (2026-05-21): Stage 4.5 场景参考图生成 + R4-3 用户确认
            # ============================================================
            # 真改动: 把场景参考图生成 (interior + exterior anchor) 从 Stage 5 内部 (5a.5)
            # 抽出, 做成独立 Stage 4.5 scene_image_preparation. 完成后进 R4-3 等用户确认,
            # 用户在 frontend /scenes 页面真预览 + 编辑 + 重生 + 60s 倒计时 (镜像 characters 对偶设计).
            #
            # 用户旅程:
            #   Stage 4 → Stage 4.5 生成场景参考图 → R4-3 等用户确认 → Stage 5 fullbody+shots
            # 用户体验:
            #   "情节确认" (R4-2 scenes_review) ≠ "场景视觉确认" (R4-3 scene_references_review)
            #   两者真不同概念, 都给用户停留点 (Founder 决方案 D, 2026-05-21 18:25)
            unique_locations = outline.get("unique_locations", [])  # 上提到 Stage 4 后, Stage 5 5a.5 也用
            _unique_loc_count = len(unique_locations)
            scene_ref_manager = None  # 上提作用域, Stage 5 后续使用

            if generate_images and not settings.SKIP_IMAGE_GENERATION and unique_locations:
                self.current_stage = "Stage 4.5: SceneImagePreparation"
                print(f"\n{'='*40}")
                print(f"Stage 4.5: 生成场景参考图")
                print(f"{'='*40}")

                # 进入 Stage 4.5
                if progress_callback:
                    await progress_callback(
                        "scene_image_preparation",
                        60,
                        f"正在生成场景参考图 ({len(unique_locations)} 个场景)...",
                        actual_shot_count=shot_count,
                        unique_location_count=max(_unique_loc_count, 1),
                        max_concurrent=settings.IMAGE_MAX_CONCURRENT,
                    )

                # 初始化 scene_ref_manager
                scene_ref_manager = SceneReferenceManager()

                # 项目风格 (与 Stage 5 一致, 这里也需要)
                project_style_45 = ProjectStyleConfig(style_preset=style_preset)
                if custom_style_analysis:
                    from app.services.style_enforcer import StyleEnforcer
                    custom_enforcement = StyleEnforcer.create_custom_enforcement(custom_style_analysis)
                    project_style_45.custom_enforcement = custom_enforcement

                # 计算 location_char_counts (与 Stage 5 5a.5 一致)
                location_char_counts_45 = {}
                for sc in screenplay.get("scenes", []):
                    loc_ref = sc.get("location_ref", "")
                    chars = sc.get("characters_in_scene", [])
                    if loc_ref and chars:
                        location_char_counts_45[loc_ref] = max(
                            location_char_counts_45.get(loc_ref, 0), len(chars)
                        )

                # 真生成所有 anchor (interior + exterior per location, DEC-014/DEC-009 关联保留)
                scene_refs_dir = os.path.join(project_dir, "scene_refs")
                os.makedirs(scene_refs_dir, exist_ok=True)

                try:
                    scene_anchors = await scene_ref_manager.generate_anchor_images(
                        scenes=[],
                        project_style=project_style_45,
                        image_generator=self.image_generator,
                        unique_locations=unique_locations,
                        delay=3.0,
                        location_character_counts=location_char_counts_45,
                        seed_images=scene_seeds,
                        aspect_ratio=aspect_ratio,
                        # T21-NEW-6: sub-stage progress 细化让 frontend stage_message 真动
                        sub_progress_callback=progress_callback,
                        sub_progress_stage_name="scene_image_preparation",
                        sub_progress_base_pct=60,
                        sub_progress_max_pct=63,
                    )

                    # 保存图片到 disk
                    for anchor_key, anchor_data in scene_anchors.items():
                        img = anchor_data.get('image')
                        if img:
                            img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))

                    cost_tracker.add_cost(
                        "gemini_nb2", 0.067 * len(scene_anchors),
                        f"Stage 4.5 scene refs {len(scene_anchors)} images"
                    )

                    # T21-NEW-7: 构建 scene_references_json (写 chapter 表, frontend GET /scene-references 用)
                    scene_references_list = []
                    import time as _t45
                    _v45 = int(_t45.time())  # cache-buster
                    for loc in unique_locations:
                        loc_id = loc.get('location_id', '')
                        if not loc_id:
                            continue
                        _loc_zh = loc.get('display_name') or loc.get('location_id', '')
                        _interior_key = f"{loc_id}_interior_anchor"
                        _exterior_key = f"{loc_id}_exterior_anchor"
                        _interior_path_disk = os.path.join(scene_refs_dir, f"{_interior_key}.png")
                        _exterior_path_disk = os.path.join(scene_refs_dir, f"{_exterior_key}.png")
                        _interior_url = (
                            f"/static/outputs/{project_id}/scene_refs/{_interior_key}.png?v={_v45}"
                            if os.path.exists(_interior_path_disk) else None
                        )
                        _exterior_url = (
                            f"/static/outputs/{project_id}/scene_refs/{_exterior_key}.png?v={_v45}"
                            if os.path.exists(_exterior_path_disk) else None
                        )
                        scene_references_list.append({
                            "location_id": loc_id,
                            "location_zh": _loc_zh,
                            "interior_url": _interior_url,
                            "exterior_url": _exterior_url,
                            "interior_description": loc.get('interior_description', ''),
                            "exterior_description": loc.get('exterior_description', ''),
                            "description_zh": loc.get('display_name', '') + ' - ' + (
                                loc.get('interior_description', '') or loc.get('exterior_description', '')
                            ),
                            "atmosphere": loc.get('atmosphere', ''),
                            "time_of_day": loc.get('time_of_day', ''),
                            "lighting_condition": loc.get('lighting_condition', ''),
                            "key_visual_elements": loc.get('key_visual_elements', []),
                        })

                    # 写 chapter.scene_references_json
                    if checkpoint_callback:
                        try:
                            await checkpoint_callback("scene_references_json", scene_references_list)
                            logger.info(
                                f"[Pipeline] T21-NEW-7: scene_references_json checkpoint OK "
                                f"({len(scene_references_list)} locations)"
                            )
                        except Exception as _cb_e:
                            logger.warning(
                                f"[Pipeline] T21-NEW-7: scene_references_json checkpoint 失败（非阻塞）: {_cb_e}"
                            )

                    print(f"✅ Stage 4.5 完成: {len(scene_anchors)}张场景参考图")
                except Exception as e:
                    print(f"⚠️ Stage 4.5 场景参考图生成失败: {e}")
                    logger.warning(f"[Pipeline] Stage 4.5 失败: {e}")
                    scene_ref_manager = None

                # T21-NEW-7 R4-3: 等用户确认场景参考图 (镜像 R4-2 wait loop)
                # ============================================================
                if progress_callback:
                    await progress_callback(
                        "scene_references_ready",
                        63,
                        "场景参考图生成完成, 等待用户确认...",
                    )

                scene_refs_confirmed_flag = False
                # RISK-T17-8 镜像: 原地重启时跳过 R4-3 (场景参考图已在上次确认)
                if start_from_stage > 4:
                    scene_refs_confirmed_flag = True
                    logger.info(
                        f"[Pipeline] T21-NEW-7 R4-3: start_from_stage={start_from_stage}, "
                        f"跳过场景参考图确认等待"
                    )
                if project_uuid and not scene_refs_confirmed_flag:
                    r43_max_wait = 1800  # 30 min, 与 R4-1/R4-2 一致
                    r43_waited = 0
                    logger.info(f"[Pipeline] T21-NEW-7 R4-3: 开始等待用户确认场景参考图 (超时 {r43_max_wait}s)")
                    while r43_waited < r43_max_wait:
                        await asyncio.sleep(2)
                        r43_waited += 2
                        try:
                            async with async_session_maker() as r43_db:
                                r43_result = await r43_db.execute(
                                    select(Project.scene_references_confirmed).where(
                                        Project.uuid == project_uuid
                                    )
                                )
                                r43_row = r43_result.scalar_one_or_none()
                                if r43_row:
                                    scene_refs_confirmed_flag = True
                                    print(f"  [R4-3] ✅ 用户已确认场景参考图 (等待 {r43_waited}s)")
                                    logger.info(
                                        f"[Pipeline] T21-NEW-7 R4-3: ✅ 用户已确认场景参考图 "
                                        f"(等待 {r43_waited}s)"
                                    )
                                    break
                        except Exception as r43_e:
                            print(f"  [R4-3] ⚠️ 查询 scene_references_confirmed 失败: {r43_e}")
                            logger.warning(
                                f"[Pipeline] T21-NEW-7 R4-3: 查询失败: {r43_e}"
                            )
                        # 每 30s 一次日志 + ETA 刷新
                        if r43_waited % 30 == 0:
                            logger.info(
                                f"[Pipeline] T21-NEW-7 R4-3: 仍在等待用户确认场景参考图... "
                                f"(已等待 {r43_waited}s)"
                            )
                            if progress_callback:
                                try:
                                    await progress_callback(
                                        "scene_references_ready",
                                        63,
                                        "等待确认场景参考图...",
                                    )
                                except Exception as _cb43_e:
                                    logger.debug(
                                        f"[Pipeline] R4-3 progress_callback 失败（非阻塞）: {_cb43_e}"
                                    )
                    if not scene_refs_confirmed_flag:
                        print(f"  [R4-3] ⏰ 等待超时 ({r43_max_wait}s)，自动继续")
                        logger.warning(
                            f"[Pipeline] T21-NEW-7 R4-3: ⏰ 等待超时 ({r43_max_wait}s)，自动继续"
                        )

                    # T21-NEW-7: 用户可能改了 scene_references → 从 DB reload 最新版本
                    # 用户编辑 → POST /regenerate-reference → 重生 anchor + scene_ref_manager 重 set_reference
                    # 但 Pipeline 内 scene_ref_manager 实例是 in-memory, 用户重生不影响这边
                    # 修复: 从 disk reload (重生时也存 disk 同样路径) 重建 scene_ref_manager.scene_references
                    if scene_ref_manager:
                        try:
                            from PIL import Image as _PilImg45
                            _scene_refs_dir_reload = os.path.join(project_dir, "scene_refs")
                            for loc in unique_locations:
                                _loc_id = loc.get('location_id', '')
                                if not _loc_id:
                                    continue
                                for _view in ('interior', 'exterior'):
                                    _anchor_key = f"{_loc_id}_{_view}_anchor"
                                    _disk_path = os.path.join(_scene_refs_dir_reload, f"{_anchor_key}.png")
                                    if os.path.exists(_disk_path):
                                        _img_reload = _PilImg45.open(_disk_path).convert("RGB")
                                        scene_ref_manager.set_reference(_loc_id, _view, _img_reload)
                            logger.info(
                                f"[Pipeline] T21-NEW-7: scene_references reloaded from disk "
                                f"(已重建 scene_ref_manager 内存状态, 反映用户编辑)"
                            )
                        except Exception as _reload_e:
                            logger.warning(
                                f"[Pipeline] T21-NEW-7: scene_references reload 失败（非阻塞）: {_reload_e}"
                            )
                else:
                    if not project_uuid:
                        print(f"  [R4-3] 无 project_uuid, 跳过等待场景参考图确认")
                        logger.info(f"[Pipeline] T21-NEW-7 R4-3: 无 project_uuid, 跳过等待")

            # ============================================================
            # 切换到 image_preparation stage (Stage 5 entry callback)
            # T21-NEW-7: Stage 4.5 完成后才进 Stage 5 (不再含场景参考图生成)
            # ============================================================
            if progress_callback:
                await progress_callback(
                    "image_preparation",
                    65,
                    "场景已确认，正在准备角色画面...",
                    actual_shot_count=shot_count,
                    unique_location_count=max(_unique_loc_count, 1),
                    max_concurrent=settings.IMAGE_MAX_CONCURRENT,
                )

            # ============================================================
            # Stage 5: 图像生成（可选）
            # ============================================================
            # Stage 5 跳过模式: 用 R8 测试图片代替生图
            if generate_images and settings.SKIP_IMAGE_GENERATION:
                self.current_stage = "Stage 5: ShotImageGenerator"
                print(f"\n{'='*40}")
                print(f"Stage 5: 生成镜头图像 (跳过模式)")
                print(f"{'='*40}")
                print("⚠️ SKIP_IMAGE_GENERATION=true — 使用 R8 测试数据代替生图")
                image_results = await self._run_stage5_skip_mode(
                    project_dir, storyboard, characters, progress_callback,
                    project_id=project_id,
                )
                self.stage_results["images"] = image_results
                self._save_json(project_dir, "5_image_results.json", image_results)
                # storyboard.shots[*].image_url 已在 _run_stage5_skip_mode 内写回，
                # 重新持久化 4_storyboard.json + 回写 chapter.storyboard_json
                self._save_json(project_dir, "4_storyboard.json", storyboard)
                if checkpoint_callback:
                    try:
                        await checkpoint_callback("storyboard_json", storyboard)
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] Stage 5 SKIP checkpoint_callback(storyboard_json) 失败（非阻塞）: {_cb_e}")
                print(f"\n✅ Stage 5 完成 (跳过模式): {len(image_results)} 图像已复制，image_url 已写回 storyboard")
                generate_images = False  # 跳过下方正常 Stage 5

            if generate_images:
                self.current_stage = "Stage 5: ShotImageGenerator"
                print(f"\n{'='*40}")
                print(f"Stage 5: 生成镜头图像")
                print(f"{'='*40}")

                images_dir = os.path.join(project_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                # T22: with_text_dir 仅在 TextOverlay 备用通道时创建
                with_text_dir = None
                if not self.use_native_text:
                    with_text_dir = os.path.join(project_dir, "with_text_images")
                    os.makedirs(with_text_dir, exist_ok=True)

                # TextOverlay 服务初始化
                text_overlay_service = TextOverlayService()

                # 5a. 生成角色参考图
                # T21-NEW-6 (2026-05-21): sub-stage stage_message 细化让 frontend 真见进度
                print("\n--- 5a. 生成角色参考图 ---")
                if progress_callback:
                    try:
                        await progress_callback(
                            "image_preparation",
                            67,
                            "准备角色全身参考图..."
                        )
                    except Exception:
                        pass
                ref_manager = ReferenceImageManager()

                # 创建风格配置（自定义风格优先）
                project_style = ProjectStyleConfig(style_preset=style_preset)
                if custom_style_analysis:
                    from app.services.style_enforcer import StyleEnforcer
                    custom_enforcement = StyleEnforcer.create_custom_enforcement(custom_style_analysis)
                    project_style.custom_enforcement = custom_enforcement

                # 为每个角色生成参考图
                # RISK-T14-10 (DEC-029): 跨角色并行生成参考图（Semaphore 3 路并发）
                # 同一角色内 portrait → fullbody 仍串行（由 generate_character_multi_refs 保证）
                char_list = characters.get("characters", [])
                _char_refs_dir_stage5 = os.path.join(project_dir, "character_refs")
                _char_ref_sem = asyncio.Semaphore(3)  # 最多 3 路并行角色
                _completed_char_count = [0]  # mutable counter for progress

                async def _gen_one_char_ref(char, char_idx: int):
                    """单角色参考图生成（portrait→fullbody 串行）"""
                    char_id = char.get("id", "unknown")
                    char_name = char.get("name", char_id)
                    seed = (character_seeds or {}).get(char_id)

                    # T20-50 方案 A: 文件存在即信任，永不覆盖 (KEY_LEARNINGS #46)
                    # 用户在 /characters 页操作的产物 = 真相，Pipeline 不准二次裁判。
                    # 旧 freshness check 算法 (_portrait_fresh = mtime > updated_at + 30) 已完全移除。
                    # 根因: RegeneratePortrait 端点 (B57) 在 T₀ 同时生成 portrait (mtime=T₀) +
                    #       更新 DB updated_at=T₀, 所以 T₀ > T₀+30 = False → 算"陈旧" → Pipeline 重新覆盖。
                    # 修复: 只在文件不存在时才生成，文件存在则直接复用。
                    _portrait_seed_local: "Image.Image | None" = None
                    _skip_portrait_local = False
                    _portrait_path = os.path.join(_char_refs_dir_stage5, f"{char_id}_portrait.png")
                    if os.path.exists(_portrait_path):
                        try:
                            from PIL import Image as _PilImage
                            _portrait_seed_local = _PilImage.open(_portrait_path).convert("RGB")
                            _skip_portrait_local = True
                            logger.info(
                                f"[Pipeline] {char_name} portrait 已存在, 信任用户操作 "
                                f"(no regen, T20-50 KEY_LEARNINGS #46)"
                            )
                            print(f"  [T20-50] {char_name} 肖像已存在，信任用户操作，直接生成全身图")
                        except Exception as _fe:
                            logger.warning(
                                f"[Pipeline] T20-50: 读取 {char_id} portrait 失败，重新生成: {_fe}"
                            )
                            _portrait_seed_local = None
                            _skip_portrait_local = False

                    if seed:
                        print(f"  生成 {char_name} 参考图（使用用户 seed 图）...", end=" ")
                    elif _skip_portrait_local:
                        print(f"  生成 {char_name} 参考图（复用新鲜肖像，只生成全身图）...", end=" ")
                    else:
                        print(f"  生成 {char_name} 参考图...", end=" ")

                    async with _char_ref_sem:
                        try:
                            await ref_manager.generate_character_multi_refs(
                                character=char,
                                project_style=project_style,
                                image_generator=self.image_generator,
                                seed_image=seed or _portrait_seed_local,
                                skip_portrait=_skip_portrait_local and not seed,
                                aspect_ratio=aspect_ratio,
                            )
                            _ref_count = 1 if (_skip_portrait_local and not seed) else 2
                            cost_tracker.add_cost("gemini_nb2", 0.067 * _ref_count, f"Ref {char_id} {'fullbody' if _ref_count == 1 else 'portrait+fullbody'}")
                            print(f"  ✅ {char_name} 参考图完成")
                        except Exception as e:
                            print(f"  ❌ {char_name} 参考图失败: {e}")

                    # RISK-T14-5-v2: 每个角色参考图完成后 update jobs
                    # T21-NEW-5 (2026-05-21): 文案 "角色参考图" → "全身参考图"
                    # 真根因: Stage 5 image_preparation 真做的是 fullbody (portrait 已 T20-50 信任),
                    # 用"角色参考图"模糊文案让 Founder 警觉是不是 Pipeline 二次裁判 portrait,
                    # 违反 KEY_LEARNINGS #46 "用户操作=真相" 设计铁律. 改"全身参考图"明确语义.
                    _completed_char_count[0] += 1
                    if progress_callback:
                        try:
                            _char_total = len(char_list)
                            _prep_pct = 65 + int(5 * _completed_char_count[0] / max(_char_total, 1))
                            await progress_callback(
                                "image_preparation", _prep_pct,
                                f"全身参考图 {_completed_char_count[0]}/{_char_total} 完成 ({char_name})"
                            )
                        except Exception as _ref_cb_e:
                            logger.debug(f"[Pipeline] ref progress_callback 失败（非阻塞）: {_ref_cb_e}")

                # 并行执行所有角色参考图生成（角色内部 portrait→fullbody 串行由 generate_character_multi_refs 保证）
                await asyncio.gather(
                    *[_gen_one_char_ref(char, i) for i, char in enumerate(char_list)],
                    return_exceptions=True,
                )

                print(f"✅ 角色参考图生成完成")

                # 保存角色参考图
                char_refs_dir = os.path.join(project_dir, "character_refs")
                os.makedirs(char_refs_dir, exist_ok=True)
                ref_manager.save_all_references(char_refs_dir)

                # T21-NEW-7 (2026-05-21 DEC-047): 场景参考图已在 Stage 4.5 生成 + R4-3 用户确认
                # 此处不再生成, 仅 ensure scene_ref_manager 实例就绪 (上方 Stage 4.5 已初始化)
                # 兜底: 如果 Stage 4.5 未跑 (老 project / 无 unique_locations / 异常), 此处重新生成
                # ----------------------------------------------------------
                print("\n--- 5a.5. 场景参考图 (Stage 4.5 已生成, 此处复用) ---")
                if scene_ref_manager is not None:
                    # T21-NEW-7: 复用 Stage 4.5 生成 + 用户编辑后 reload 的 scene_ref_manager
                    _existing_loc_count = len(getattr(scene_ref_manager, 'scene_references', {}))
                    print(f"  ✅ 复用 Stage 4.5 场景参考图 ({_existing_loc_count} 个 location)")
                    logger.info(
                        f"[Pipeline] T21-NEW-7: Stage 5 复用 Stage 4.5 scene_ref_manager "
                        f"({_existing_loc_count} location)"
                    )
                elif unique_locations:
                    # 兜底路径: Stage 4.5 未跑 (异常 / 老代码), 走原 Stage 5 5a.5 逻辑
                    print(f"  ⚠️ Stage 4.5 未生成场景参考图, 走兜底路径重新生成")
                    logger.warning(
                        f"[Pipeline] T21-NEW-7: Stage 4.5 未生成 scene_ref_manager, "
                        f"走 Stage 5 兜底重新生成 ({len(unique_locations)} location)"
                    )
                    scene_ref_manager = SceneReferenceManager()
                    location_char_counts = {}
                    for sc in screenplay.get("scenes", []):
                        loc_ref = sc.get("location_ref", "")
                        chars = sc.get("characters_in_scene", [])
                        if loc_ref and chars:
                            location_char_counts[loc_ref] = max(
                                location_char_counts.get(loc_ref, 0), len(chars)
                            )
                    try:
                        scene_anchors = await scene_ref_manager.generate_anchor_images(
                            scenes=[],
                            project_style=project_style,
                            image_generator=self.image_generator,
                            unique_locations=unique_locations,
                            delay=3.0,
                            location_character_counts=location_char_counts,
                            seed_images=scene_seeds,
                            aspect_ratio=aspect_ratio,
                            # T21-NEW-6: 兜底路径也细化 sub-progress (用 image_preparation stage 内部 65-67% 范围)
                            sub_progress_callback=progress_callback,
                            sub_progress_stage_name="image_preparation",
                            sub_progress_base_pct=65,
                            sub_progress_max_pct=67,
                        )
                        scene_refs_dir = os.path.join(project_dir, "scene_refs")
                        os.makedirs(scene_refs_dir, exist_ok=True)
                        for anchor_key, anchor_data in scene_anchors.items():
                            img = anchor_data.get('image')
                            if img:
                                img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))
                        cost_tracker.add_cost(
                            "gemini_nb2", 0.067 * len(scene_anchors),
                            f"Scene refs fallback {len(scene_anchors)} images"
                        )
                        print(f"✅ 场景参考图兜底生成完成: {len(scene_anchors)}张")
                    except Exception as e:
                        print(f"⚠️ 场景参考图兜底生成失败: {e}")
                        scene_ref_manager = None
                else:
                    print("⚠️ 无 unique_locations，跳过场景参考图")

                # 5b. 生成镜头图像
                print("\n--- 5b. 生成镜头图像 ---")
                shots = storyboard.get("shots", [])

                # 应用shots_limit限制
                if shots_limit > 0 and len(shots) > shots_limit:
                    print(f"  ⚠️ 限制生成前 {shots_limit} 个shots（总共 {len(shots)} 个）")
                    shots = shots[:shots_limit]

                image_results = []
                reference_images_log = []  # 记录每个shot的参考图使用情况

                # ARCH-4: Stage 5 开始前查 api_cost_logs 表做跨 run 累计熔断检查
                await cost_tracker.check_db_cost_limit(detail="Stage 5 pre-check")

                # ── TASK-PARALLEL-M1: Stage 5 串行 → 并行 ──────────────────
                # 预先构建所有 shot 的参考图上下文（仍是串行，读 ref_manager 无 API 调用）
                shot_contexts = []
                for i, shot in enumerate(shots):
                    shot_id = shot.get("shot_id", i + 1)

                    # 获取角色参考图 - SQ-2: 智能选择，每角色1张
                    char_direction = shot.get("character_direction", {})
                    chars_in_scene = char_direction.get("characters_visible", [])
                    shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
                    char_refs = ref_manager.get_smart_references_for_scene(chars_in_scene, shot_type)

                    # 获取场景参考图 - 从scene_id追溯到location_id
                    scene_refs = []
                    location_id = None
                    if scene_ref_manager:
                        scene_id = shot.get("scene_id")
                        location_id = self._get_location_id_for_scene(
                            scene_id, screenplay, unique_locations
                        )
                        if location_id:
                            scene_refs = scene_ref_manager.get_references_for_location(location_id)

                    all_refs = char_refs + scene_refs

                    # 日志输出
                    ref_info = []
                    if chars_in_scene:
                        ref_info.append(f"角色: {chars_in_scene} ({len(char_refs)}张)")
                    if location_id and scene_refs:
                        ref_info.append(f"场景: {location_id} ({len(scene_refs)}张)")
                    if ref_info:
                        logger.info(f"  Shot {shot_id} refs: {', '.join(ref_info)}")

                    # 记录参考图使用情况
                    reference_images_log.append({
                        "shot_id": shot_id,
                        "characters_in_scene": chars_in_scene,
                        "char_refs_count": len(char_refs),
                        "location_id": location_id,
                        "scene_refs_count": len(scene_refs),
                        "total_refs": len(all_refs)
                    })

                    # T-I: Prompt Pre-Check (v1 log-only, 不阻断不修改 prompt)
                    pre_check_warnings = self._pre_check_prompt(shot, characters)
                    for w in pre_check_warnings:
                        logger.info(f"    [PromptPreCheck] Shot {shot_id}: ⚠️ {w}")

                    shot_contexts.append({
                        "shot": shot,
                        "shot_id": shot_id,
                        "shot_index": i,
                        "chars_in_scene": chars_in_scene,
                        "all_refs": all_refs,
                    })

                # 并行生成：Semaphore 限流 + 每张完成后回调进度
                semaphore = asyncio.Semaphore(settings.IMAGE_MAX_CONCURRENT)
                completed_count = 0
                completed_lock = asyncio.Lock()

                async def _generate_one_shot(ctx: dict) -> dict:
                    """单张 Shot 完整生成流程（含 API 调用 + Haiku 验证），在 Semaphore 内执行。"""
                    import gc as _gc
                    nonlocal completed_count

                    shot = ctx["shot"]
                    shot_id = ctx["shot_id"]
                    shot_index = ctx["shot_index"]
                    chars_in_scene = ctx["chars_in_scene"]
                    all_refs = ctx["all_refs"]
                    text_overlay_data = shot.get("text_overlay", {})

                    # Q2 累积态兜底: 每 5 shot 触发 GC + asyncio 让权，清空事件循环积压
                    if shot_index > 0 and shot_index % 5 == 0:
                        logger.info(f"[Pipeline] Shot {shot_id}: 触发 GC 兜底（shot_index={shot_index}）")
                        _gc.collect()
                        await asyncio.sleep(0)

                    async with semaphore:
                        logger.info(f"  [Stage5] 生成 Shot {shot_id}/{len(shots)}...")

                        # T17: Shot 生成 + Haiku 视觉验证 + Auto-Retry
                        # T20-48 (2026-05-20): anatomy_issue 专用重试上限
                        # 背景: test20 Shot 16 anatomy_issue (4 hands), ShotValidator 抓到但 MAX_SHOT_RETRIES=1
                        # 只给 1 次重试，Seedream 再 hallucinate 就只有 2 次机会。
                        # 新设计: anatomy_issue 最多 2 次重试 (3 次总尝试), 其他 fail 1 次重试 (2 次总)。
                        # anatomy 第 3 次还 fail → partial_failure 标记 + log ERROR (frontend warning badge 预留)
                        MAX_SHOT_RETRIES = 1  # T-B: 默认最多 retry 1 次，共 2 次尝试
                        MAX_ANATOMY_RETRIES = 2  # T20-48: anatomy_issue 最多 retry 2 次，共 3 次尝试
                        best_result = None
                        _anatomy_regen_count = 0  # T20-48: 本 shot anatomy 重生次数追踪

                        for attempt in range(MAX_ANATOMY_RETRIES + 1):  # 最大循环次数用 anatomy 上限
                            if attempt > 0:
                                logger.info(f"    [T17] Retry {attempt}/{MAX_SHOT_RETRIES} Shot {shot_id}...")

                            # TASK-PARALLEL-M1: dispatcher provider-agnostic（不写死 provider 判断）
                            # ARCH-4: 传入 db_project_id 让 log_api_cost 真实 INSERT（NB2 路径通过 **kwargs 透传）
                            # D.15 P0: aspect_ratio 从 run() 参数读取，不再 hardcoded "2:3"
                            #
                            # RISK-T20-19 (2026-05-19): 加单 shot wall-clock timeout (720s = 12 min)
                            # DevOps 5/19 15:35 诊断: SeedreamGenerator HTTP retry 上限 3 次 × 210s +
                            # 退避 2+8+30+60s, 理论最坏 ~15 min。但 pipeline 层之前没 asyncio.wait_for,
                            # Shot 14 实测 hang 12.5 min, Shot 16 hang 14.2 min（险胜）。
                            # 720s cap 略小于理论最坏, 但合理 — 不会被单个假死 shot 拖死整批。
                            # 超时按 partial_failure 走（Frontend "查看并重生" 可救）。
                            try:
                                result = await asyncio.wait_for(
                                    self.image_generator.generate_shot_image_phase2_safe(
                                        shot=shot,
                                        storyboard=storyboard,
                                        characters=characters,
                                        style_preset=style_preset,
                                        reference_images=all_refs,
                                        screenplay=screenplay,
                                        aspect_ratio=aspect_ratio,
                                        use_native_text=self.use_native_text,
                                        project_id=db_project_id,
                                        # T22-NEW-6 (2026-05-22): 传 outline 让
                                        # _apply_identity_anchors 真注入 LOCATION
                                        # ANCHOR — 修 e2e test22 实证 21/21
                                        # location=N 真**未传** location dict bug.
                                        # 通过 kwargs 透传到 image_generator,
                                        # 0 API contract 变更.
                                        outline=outline,
                                    ),
                                    timeout=SHOT_WALL_CLOCK_TIMEOUT_SEC,
                                )
                            except asyncio.TimeoutError:
                                logger.error(
                                    f"    [T20-19] ❌ Shot {shot_id} 超过 wall-clock "
                                    f"{SHOT_WALL_CLOCK_TIMEOUT_SEC}s, 主动放弃 (attempt {attempt + 1})"
                                )
                                # 构造失败 result, 走原失败路径 (partial_failure + Frontend 可重生)
                                result = {
                                    "success": False,
                                    "error": (
                                        f"Shot wall-clock timeout {SHOT_WALL_CLOCK_TIMEOUT_SEC}s "
                                        f"exceeded (T20-19)"
                                    ),
                                    "error_kind": "wall_clock_timeout",
                                }
                                best_result = result
                                break  # 不 retry: 已经等了 12 min, 再来一次也无意义

                            if not result.get("success"):
                                best_result = result
                                break  # 生成失败不 retry（API 错误由 image_generator 内部处理）

                            best_result = result

                            # T28: 从 composition 中提取关键道具
                            key_props = []
                            composition = shot.get("composition", {})
                            if composition:
                                for field in ["foreground", "background", "key_object"]:
                                    val = composition.get(field, "")
                                    if val and isinstance(val, str) and len(val) > 2:
                                        key_props.append(val)

                            # T17+T28+T30: Haiku 视觉验证（并行 Semaphore 内执行）
                            props_log = f" + {len(key_props)} props" if key_props else ""
                            logger.info(f"    [ShotValidator] Shot {shot_id}: 开始验证 (expect {len(chars_in_scene)} chars{props_log})")
                            validation = await self.shot_validator.validate_shot(
                                pil_image=result["pil_image"],
                                expected_character_count=len(chars_in_scene),
                                text_overlay_data=text_overlay_data,
                                key_props=key_props if key_props else None,
                                shot=shot,  # T20-6 v2: 传入完整 shot dict，让 universal skip 真正生效
                            )
                            logger.info(f"    [ShotValidator] Shot {shot_id}: valid={validation['valid']}, reason={validation['reason']}")

                            if validation["valid"]:
                                if attempt > 0:
                                    logger.info(f"    [T17] ✅ Shot {shot_id} retry 后验证通过")
                                break
                            else:
                                _val_reason = validation.get("reason", "")
                                _is_anatomy_fail = "anatomy_issue" in _val_reason
                                logger.info(f"    [T17] ⚠️ Shot {shot_id} 验证失败: {_val_reason}")

                                # T20-48: anatomy_issue 专用最多 2 次重试 (3 次总尝试)
                                if _is_anatomy_fail:
                                    _anatomy_regen_count += 1
                                    if _anatomy_regen_count <= MAX_ANATOMY_RETRIES:
                                        logger.warning(
                                            f"    [T20-48] ⚠️ Shot {shot_id} anatomy_issue 触发自动重生 "
                                            f"(第 {_anatomy_regen_count}/{MAX_ANATOMY_RETRIES} 次): {_val_reason}"
                                        )
                                        continue  # 继续循环 → 重生
                                    else:
                                        # 3 次都 anatomy fail → partial_failure
                                        logger.error(
                                            f"    [T20-48] ❌ Shot {shot_id} anatomy_issue 持续 "
                                            f"{_anatomy_regen_count} 次仍不通过, 标记 partial_failure "
                                            f"(frontend warning badge 预留): {_val_reason}"
                                        )
                                        shot["_anatomy_partial_failure"] = True
                                        shot["_anatomy_issues"] = validation.get("anatomy_issues", [])
                                        break
                                elif attempt >= MAX_SHOT_RETRIES:
                                    # 非 anatomy fail: 达到普通重试上限
                                    logger.info(f"    [T17] Shot {shot_id} 已达最大重试次数，使用当前结果")

                        # 0.5s 冷却移至 Semaphore 内（保留限流语义）
                        await asyncio.sleep(0.5)

                    # Semaphore 释放后处理结果（图像保存等 IO 不占并发槽位）
                    result = best_result
                    if result and result.get("success"):
                        # 成本计数: 根据 provider 计费（NB2 $0.067 / Seedream $0.030）
                        provider = getattr(settings, "IMAGE_GEN_PROVIDER", "nb2")
                        unit_cost = 0.030 if provider == "seedream" else 0.067
                        service_key = "seedream" if provider == "seedream" else "gemini_nb2"
                        cost_tracker.add_cost(service_key, unit_cost, f"Shot {shot_id}")

                        # 保存无文字版图像
                        image_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                        result["pil_image"].save(image_path)

                        # TextOverlay: 生成带文字版本
                        with_text_path = None
                        text_type = text_overlay_data.get("text_type", "none") if text_overlay_data else "none"
                        _use_native_text = self.use_native_text
                        if text_type != "none":
                            if _use_native_text:
                                with_text_path = image_path
                            else:
                                try:
                                    with_text_image = text_overlay_service.process_shot(
                                        result["pil_image"].copy(), text_overlay_data
                                    )
                                    with_text_path = os.path.join(with_text_dir, f"shot_{shot_id:02d}.png")
                                    with_text_image.save(with_text_path)
                                    logger.info(f"    ✅ TextOverlay: {with_text_path}")
                                except Exception as te:
                                    logger.warning(f"    ⚠️ TextOverlay失败: {te}")

                        logger.info(f"    ✅ Shot {shot_id} 保存: {image_path}")

                        # BE-3: 将 HTTP URL 写回 shot dict（让前端预览页能正确加载）
                        _image_http_url = f"/static/outputs/{project_id}/images/shot_{shot_id:02d}.png"
                        shot["image_url"] = _image_http_url

                        # 每张完成后回调进度
                        # RISK-T18-A (Wave 11.4): per-shot 增量
                        # 公式: 75 + int(20 * done / total)
                        #   - 与 P1-1 entry callback (75%) 对齐
                        #   - 29 shots: 每 shot +0.69% (75%→95% 平滑)
                        #   - 对齐 job_manager._ETA_STAGE_PROGRESS_BOUNDS["image_generation"] = (70, 92)
                        async with completed_lock:
                            completed_count += 1
                            _done = completed_count
                        if progress_callback:
                            try:
                                _total_shots = max(len(shots), 1)
                                _pct = 75 + int(20 * _done / _total_shots)
                                await progress_callback(
                                    "image_generation", _pct,
                                    f"已生成 {_done}/{len(shots)} 张图像..."
                                )
                            except Exception as _cb_e:
                                logger.warning(f"[Pipeline] progress_callback 失败: {_cb_e}")

                        return {
                            "shot_id": shot_id,
                            "success": True,
                            "image_path": image_path,
                            "image_url": _image_http_url,
                            "with_text_path": with_text_path,
                            "generation_time": result.get("generation_time_seconds", 0)
                        }
                    else:
                        err = (result.get("error", "Unknown error") if result else "No result returned")
                        error_kind = result.get("error_kind", "") if result else ""
                        logger.error(f"    ❌ Shot {shot_id} 失败: {err}")

                        # RISK-T15-9 (Wave 9 / DEC-030): mid-stage failed_shot_count 实时累加
                        # 不再等 Pipeline finalize 才汇总 — 单 shot 失败立即写 DB，
                        # frontend status response 中途即可看到 partial_failure=True
                        if job_id is not None:
                            try:
                                from app.services.job_manager import increment_failed_shot_count
                                await increment_failed_shot_count(job_id)
                            except Exception as _inc_e:
                                logger.warning(
                                    f"    [T15-9] Shot {shot_id} increment_failed_shot_count 失败"
                                    f"（非阻塞）: {_inc_e}"
                                )

                        # D.17: content_safety_failure → Haiku 智能分析，写回 shot dict
                        safety_advice: dict | None = None
                        if error_kind == "content_safety_failure":
                            try:
                                from app.services.prompt_safety_advisor import analyze_safety_failure
                                failed_prompt = result.get("failed_prompt", "") if result else ""
                                safety_advice = await analyze_safety_failure(
                                    failed_prompt=failed_prompt,
                                    reason=error_kind,
                                )
                                shot["error_message"] = safety_advice.get("user_message", "")
                                shot["safety_advice"] = safety_advice
                                shot["image_url"] = None
                                logger.info(
                                    f"    [SafetyAdvisor] Shot {shot_id} 安全提示已写回: "
                                    f"{len(safety_advice.get('suspected_terms', []))} suspected terms"
                                )
                            except Exception as _sa_exc:
                                logger.warning(f"    [SafetyAdvisor] Shot {shot_id} 分析失败（非阻塞）: {_sa_exc}")

                        async with completed_lock:
                            completed_count += 1
                        if progress_callback:
                            try:
                                async with completed_lock:
                                    _done = completed_count
                                # RISK-T18-A (Wave 11.4): per-shot 增量 (failure path)
                                _total_shots = max(len(shots), 1)
                                _pct = 75 + int(20 * _done / _total_shots)
                                await progress_callback(
                                    "image_generation", _pct,
                                    f"已生成 {_done}/{len(shots)} 张图像（含失败）..."
                                )
                            except Exception:
                                pass

                        return {
                            "shot_id": shot_id,
                            "success": False,
                            "error": err,
                            "error_kind": error_kind,
                            "image_path": None,
                            "with_text_path": None,
                            "safety_advice": safety_advice,
                        }

                logger.info(
                    f"\n[Pipeline] Stage 5 并行生成开始: "
                    f"{len(shot_contexts)} shots, max_concurrent={settings.IMAGE_MAX_CONCURRENT}"
                )
                print(f"\n  Stage 5 并行生成: {len(shot_contexts)} shots, 并发={settings.IMAGE_MAX_CONCURRENT}")

                # T21-NEW-6: 调度 Shot 生成前细化 stage_message
                if progress_callback:
                    try:
                        await progress_callback(
                            "image_preparation",
                            69,
                            f"准备分镜参考映射 + 调度 Shot 生成 ({len(shot_contexts)} 张)..."
                        )
                    except Exception:
                        pass

                # P1-1: 进入真生图阶段 → 切换到 image_generation stage（entry callback）
                # Round 2: 再次确认 dynamic params（防止 image_preparation 回调被跳过的情况）
                if progress_callback:
                    try:
                        await progress_callback(
                            "image_generation",
                            75,
                            f"开始绘制画面 (0/{len(shot_contexts)})...",
                            actual_shot_count=shot_count,
                            unique_location_count=max(_unique_loc_count, 1),
                            max_concurrent=settings.IMAGE_MAX_CONCURRENT,
                        )
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] P1-1 progress_callback(image_generation) 失败: {_cb_e}")

                # asyncio.gather 并发所有 shot（Semaphore 控流，return_exceptions 防止单张失败阻断全批）
                raw_results = await asyncio.gather(
                    *[_generate_one_shot(ctx) for ctx in shot_contexts],
                    return_exceptions=True,
                )

                # 处理异常（return_exceptions=True 时异常会作为返回值）
                for i, raw in enumerate(raw_results):
                    if isinstance(raw, Exception):
                        _sid = shot_contexts[i]["shot_id"]
                        logger.error(f"[Pipeline] Shot {_sid} gather 异常: {type(raw).__name__}: {raw}")
                        # RISK-T15-9 (Wave 9 / DEC-030): gather 内异常也算 mid-stage 失败
                        if job_id is not None:
                            try:
                                from app.services.job_manager import increment_failed_shot_count
                                await increment_failed_shot_count(job_id)
                            except Exception as _inc_e:
                                logger.warning(
                                    f"[Pipeline] T15-9 gather exception Shot {_sid} "
                                    f"increment_failed_shot_count 失败（非阻塞）: {_inc_e}"
                                )
                        image_results.append({
                            "shot_id": _sid,
                            "success": False,
                            "error": f"{type(raw).__name__}: {raw}",
                            "image_path": None,
                            "with_text_path": None,
                        })
                    else:
                        image_results.append(raw)

                # 保持 shot_id 顺序
                image_results.sort(key=lambda r: r.get("shot_id", 0))

                self.stage_results["images"] = image_results
                self._save_json(project_dir, "5_image_results.json", image_results)

                # 保存参考图使用日志
                self._save_json(project_dir, "reference_images_log.json", reference_images_log)
                print(f"  参考图使用日志已保存: reference_images_log.json")

                success_count = sum(1 for r in image_results if r.get("success"))
                print(f"\n✅ Stage 5 完成: {success_count}/{len(shots)} 图像生成成功")

                # BE-3: 重新持久化 4_storyboard.json（已含 image_url）+ 回写 chapter.storyboard_json
                self._save_json(project_dir, "4_storyboard.json", storyboard)
                if checkpoint_callback:
                    try:
                        await checkpoint_callback("storyboard_json", storyboard)
                        logger.info("[Pipeline] BE-3: storyboard_json checkpoint 成功（含 image_url）")
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] BE-3: checkpoint(storyboard_json) 失败（非阻塞）: {_cb_e}")

                # ARCH-1: 批量写入 chapter_scene_images 表（让单 shot 重生成 / 局部编辑功能生效）
                # 在 storyboard.shots[*].image_url 全部写回完成后才执行，确保顺序正确。
                # 失败不阻塞 pipeline（非阻塞，log warning 即可）。
                if chapter_id:
                    try:
                        from app.database import async_session_maker
                        from app.models.scene_image import SceneImage
                        from sqlalchemy import delete as sa_delete
                        # D.18: model-aware 尺寸查询（NB2 vs Seedream 实际分辨率不同）
                        from app.services.seedream_generator import get_size_for_model as _get_size
                        _current_provider = getattr(settings, "IMAGE_GEN_PROVIDER", "nb2")
                        _ar_width, _ar_height = _get_size(_current_provider, aspect_ratio)

                        async with async_session_maker() as arch1_db:
                            # 先 DELETE 该 chapter 下所有既有 SceneImage 记录（防止重复写入）
                            # 适用场景：pipeline 重跑、重生成后再跑整批等情况
                            await arch1_db.execute(
                                sa_delete(SceneImage).where(SceneImage.chapter_id == chapter_id)
                            )

                            # 批量 INSERT 成功的 shots（image_url 不为空）
                            inserted_count = 0
                            for shot_idx, shot in enumerate(shots):
                                _image_url = shot.get("image_url")
                                if not _image_url:
                                    # 失败的 shot（image_url 为 null）跳过
                                    continue

                                _shot_id = shot.get("shot_id", shot_idx + 1)
                                _image_path = os.path.join(
                                    project_dir, "images", f"shot_{_shot_id:02d}.png"
                                )

                                si = SceneImage(
                                    chapter_id=chapter_id,
                                    scene_id=_shot_id,          # scene_id 存 shot_id，与 regenerate 端点查询对应
                                    image_prompt=shot.get("image_prompt", ""),
                                    image_path=_image_path,     # 本地绝对路径
                                    image_url=_image_url,       # HTTP URL /static/outputs/...
                                    width=_ar_width,            # D.18: model-aware 真实宽度（NB2/Seedream 不同）
                                    height=_ar_height,          # D.18: model-aware 真实高度
                                    aspect_ratio=aspect_ratio,  # D.15 P0: 真实比例，从 run() 参数读取
                                    is_active=True,
                                )
                                arch1_db.add(si)
                                inserted_count += 1

                            await arch1_db.commit()
                            logger.info(
                                f"[Pipeline] ARCH-1: chapter_scene_images 批量写入完成 "
                                f"chapter_id={chapter_id}, inserted={inserted_count}/{len(shots)}"
                            )
                            print(f"  [ARCH-1] ✅ chapter_scene_images 写入 {inserted_count} 条")
                    except Exception as _arch1_e:
                        logger.warning(
                            f"[Pipeline] ARCH-1: chapter_scene_images 写入失败（非阻塞）: {_arch1_e}"
                        )
                        print(f"  [ARCH-1] ⚠️ chapter_scene_images 写入失败（非阻塞）: {_arch1_e}")
                else:
                    logger.info("[Pipeline] ARCH-1: chapter_id 为 None（测试模式），跳过 chapter_scene_images 写入")

            # ============================================================
            # Stage 6: BGM 生成（Wave 2 Pipeline Integration）
            # 非阻塞：失败时只记录警告，不中断 Pipeline。
            # ============================================================
            print(f"\n{'='*40}")
            print(f"Stage 6: BGM 音乐生成")
            print(f"{'='*40}")
            bgm_result = None
            # UX-10: BGM 开始前发送进度回调
            if progress_callback:
                try:
                    await progress_callback("bgm", 92, "正在生成配乐...")
                except Exception as _cb_e:
                    logger.warning(f"[Pipeline] UX-10 progress_callback(bgm) 失败: {_cb_e}")
            try:
                from app.services.music_generation_service import generate_bgm_for_chapter
                # story_type 根据 target_duration_minutes 映射
                if target_duration_minutes <= 1:
                    _story_type = "快闪"
                elif target_duration_minutes <= 2:
                    _story_type = "短篇"
                else:
                    _story_type = "中篇"

                # BGM-1: 优先用 outline.music_hint（已在 Stage 1 后注入），降级到 style_preset
                _visual_style_hint = outline.get("music_hint") or style_preset

                bgm_result = await generate_bgm_for_chapter(
                    chapter_id=0,          # 手动测试模式无真实 chapter_id，用 0
                    project_id=0,          # 手动测试模式无真实 project_id，用 0
                    outline=outline,
                    screenplay=screenplay,
                    output_dir=project_dir,
                    story_type=_story_type,
                    visual_style_hint=_visual_style_hint,
                    regen_count=0,
                    bgm_volume=1.0,
                    style_preset=style_preset,  # Wave 7 / RISK-T14-11 / DEC-026: BGM 通用性框架 wiring
                    is_change_bgm=False,
                    user_selected_mood=user_selected_mood,  # B33: Stage A 情绪基調
                )
                self.stage_results["bgm"] = bgm_result

                # BE-5: 将本地 bgm 文件路径转换为 HTTP URL（/static/outputs/{uuid}/bgm_chapterN.mp3）
                _bgm_local_path = bgm_result.get("bgm_url", "")
                _bgm_http_url = _bgm_local_path  # 默认原样保留（兜底）
                if _bgm_local_path and project_uuid:
                    # 取文件名，组装 HTTP URL
                    _bgm_filename = os.path.basename(_bgm_local_path)
                    _bgm_http_url = f"/static/outputs/{project_uuid}/{_bgm_filename}"
                    bgm_result["bgm_url"] = _bgm_http_url
                    logger.info(f"[Pipeline] BE-5: bgm_url 转换: {_bgm_local_path} → {_bgm_http_url}")

                print(f"✅ Stage 6 完成: BGM 生成成功")
                print(f"   bgm_url: {bgm_result.get('bgm_url', 'N/A')}")
                print(f"   meta_version: {bgm_result.get('meta_version', 'N/A')}")
                logger.info(
                    f"[Pipeline] Stage 6 BGM 生成成功: "
                    f"bgm_url={bgm_result.get('bgm_url')}, "
                    f"meta_version={bgm_result.get('meta_version')}"
                )

                # 如果有 checkpoint_callback（DB 写入），写 bgm_url + bgm_meta_version + credits_used
                if checkpoint_callback and bgm_result.get("bgm_url"):
                    try:
                        await checkpoint_callback("bgm_url", bgm_result["bgm_url"])
                        await checkpoint_callback("bgm_meta_version", bgm_result.get("meta_version", ""))
                        await checkpoint_callback("credits_used", bgm_result.get("credits_used", 0))
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] Stage 6 checkpoint_callback 失败（非阻塞）: {_cb_e}")

                # UX-11: BGM 完成后发送 completed 回调
                if progress_callback:
                    try:
                        await progress_callback("completed", 100, "故事生成完成")
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] UX-11 progress_callback(completed) 失败: {_cb_e}")

            except Exception as bgm_e:
                print(f"⚠️ Stage 6 BGM 生成失败（非阻塞，不影响 Pipeline 结果）: {bgm_e}")
                logger.warning(f"[Pipeline] Stage 6 BGM 生成失败（非阻塞）: {bgm_e}")
                # UX-11: BGM 失败时仍发送 completed（Pipeline 成功，BGM 只是可选项）
                if progress_callback:
                    try:
                        await progress_callback("completed", 100, "故事生成完成")
                    except Exception as _cb_e:
                        logger.warning(f"[Pipeline] UX-11 progress_callback(completed/bgm_fail) 失败: {_cb_e}")

            # ============================================================
            # 完成
            # ============================================================
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = {
                "project_id": project_id,
                "project_dir": project_dir,
                "idea": idea,
                "style_preset": style_preset,
                "target_duration_minutes": target_duration_minutes,
                "title": outline.get("title", ""),
                "total_characters": len(characters.get("characters", [])),
                "total_scenes": len(screenplay.get("scenes", [])),
                "total_shots": len(storyboard.get("shots", [])),
                "images_generated": generate_images,
                "bgm_url": bgm_result.get("bgm_url") if bgm_result else None,
                "bgm_meta_version": bgm_result.get("meta_version") if bgm_result else None,
                "pipeline_duration_seconds": round(duration, 2),
                "stages_completed": list(self.stage_results.keys()),
                "timestamp": end_time.isoformat()
            }

            self._save_json(project_dir, "summary.json", summary)

            print(f"\n{'='*60}")
            print(f"Phase 2.0 Pipeline 完成!")
            print(f"{'='*60}")
            print(f"项目目录: {project_dir}")
            print(f"总耗时: {duration:.1f}秒")
            print(f"故事标题: {summary['title']}")
            print(f"角色数: {summary['total_characters']}")
            print(f"场景数: {summary['total_scenes']}")
            print(f"镜头数: {summary['total_shots']}")
            print(f"{'='*60}\n")
            logger.info(f"[Pipeline] ========== Pipeline 完成 ==========")
            logger.info(f"[Pipeline] ✅ 总耗时: {duration:.1f}s, 标题: {summary['title']}")
            logger.info(f"[Pipeline] 角色: {summary['total_characters']}, 场景: {summary['total_scenes']}, 镜头: {summary['total_shots']}")

            return {
                "success": True,
                "summary": summary,
                "stage_results": self.stage_results
            }

        except Exception as e:
            print(f"\n❌ Pipeline 失败于 {self.current_stage}: {e}")
            logger.error(f"[Pipeline] ❌ Pipeline 失败于 {self.current_stage}: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "failed_stage": self.current_stage,
                "stage_results": self.stage_results
            }

    def _pre_check_prompt(self, shot: dict, characters: dict) -> list:
        """
        T-I: Prompt Pre-Check — v1 仅日志，不阻断不修改 prompt

        4 个预检维度:
        - P1: characters_visible 数量 vs prompt 中 "EXACTLY N"
        - P2: 画外角色物理接触描述
        - P3: 空间矛盾（v2 预留）
        - P4: dialogue embed + native text 对同一 speaker 重复指令
        """
        warnings = []
        image_prompt = shot.get("image_prompt", "")
        char_direction = shot.get("character_direction", {})
        chars_visible = char_direction.get("characters_visible", [])
        text_overlay = shot.get("text_overlay", {})

        # P1: characters_visible count vs prompt "EXACTLY N"
        match = re.search(r'EXACTLY\s+(\d+)\s+characters?', image_prompt, re.IGNORECASE)
        if match:
            prompt_count = int(match.group(1))
            actual_count = len(chars_visible)
            if prompt_count != actual_count:
                warnings.append(
                    f"P1 — prompt 指定 EXACTLY {prompt_count} 角色，"
                    f"但 characters_visible 有 {actual_count} 人"
                )

        # P2: off-screen physical contact keywords
        prompt_lower = image_prompt.lower()
        offscreen_kws = ["off-screen", "off screen", "outside the frame", "beyond the frame"]
        contact_kws = [
            "grip", "pull", "pulled", "hold", "holding", "held",
            "embrace", "embracing", "grab", "grabbing", "drag", "dragging",
            "tug", "tugging", "clutch", "clutching"
        ]
        has_offscreen = any(kw in prompt_lower for kw in offscreen_kws)
        has_contact = any(kw in prompt_lower for kw in contact_kws)
        if has_offscreen and has_contact:
            warnings.append("P2 — 检测到画外角色物理接触描述（off-screen + 物理接触关键词）")

        # P3: spatial contradiction — reserved for v2

        # P4: off_screen_speaker=True 但 speaker 在 characters_visible 中
        if text_overlay and text_overlay.get("off_screen_speaker"):
            text_type = text_overlay.get("text_type", "")
            chinese_text = text_overlay.get("chinese_text", "")
            if text_type in ("dialogue", "dialogue_with_thought",
                             "dialogue_with_narration", "narration_with_dialogue"):
                # 提取 speaker 名
                speaker_names = set()
                texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
                for txt in texts:
                    if isinstance(txt, str):
                        m = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', txt)
                        if m:
                            speaker_names.add(m.group(1))

                # 构建 name→id 映射
                char_name_to_id = {}
                for c in characters.get("characters", []):
                    cid = c.get("id", "")
                    cname = c.get("name", "")
                    if cid and cname:
                        char_name_to_id[cname] = cid

                for speaker in speaker_names:
                    char_id = char_name_to_id.get(speaker)
                    if not char_id:
                        for name, cid in char_name_to_id.items():
                            if speaker in name or name in speaker:
                                char_id = cid
                                break
                    if char_id and char_id in chars_visible:
                        warnings.append(
                            f"P4 — speaker '{speaker}' 同时出现在 "
                            f"off_screen dialogue 和 characters_visible 中"
                        )

        return warnings

    async def _run_stage5_skip_mode(
        self, project_dir: str, storyboard: dict, characters: dict,
        progress_callback=None, project_id: Optional[str] = None,
    ) -> list:
        """Stage 5 跳过模式: 从 R8 测试数据复制图片，不调 Gemini/NB2

        副作用: 将 image_url (/static/outputs/{project_id}/images/shot_NN.png) 写回
        storyboard.shots[*].image_url，让前端预览页能正确加载图片。
        """
        # 5a: 角色参考图
        char_refs_dir = os.path.join(project_dir, "character_refs")
        os.makedirs(char_refs_dir, exist_ok=True)
        r8_char_files = sorted(glob.glob(os.path.join(R8_DATA_DIR, "character_refs", "char_*")))
        r8_char_ids = sorted(set(
            "_".join(os.path.basename(f).split("_")[:2]) for f in r8_char_files
        ))  # ["char_001", "char_002", ...]
        r8_char_count = len(r8_char_ids)

        char_list = characters.get("characters", [])
        for i, char in enumerate(char_list):
            char_id = char.get("id", f"char_{i+1:03d}")
            # 循环复用 R8 角色
            r8_idx = i % r8_char_count if r8_char_count > 0 else 0
            r8_id = r8_char_ids[r8_idx] if r8_char_ids else "char_001"
            for suffix in ["portrait", "fullbody"]:
                src = os.path.join(R8_DATA_DIR, "character_refs", f"{r8_id}_{suffix}.png")
                dst = os.path.join(char_refs_dir, f"{char_id}_{suffix}.png")
                if os.path.exists(src):
                    shutil.copy2(src, dst)
            print(f"  ✅ {char_id} 参考图已复制 (from {r8_id})")

        # B-5: Stage 5 = 65→100%
        if progress_callback:
            await progress_callback("image_generation", 75, "角色参考图就绪...")

        # 5a.5: 场景参考图
        scene_refs_dir = os.path.join(project_dir, "scene_refs")
        os.makedirs(scene_refs_dir, exist_ok=True)
        r8_scene_files = glob.glob(os.path.join(R8_DATA_DIR, "scene_refs", "*.png"))
        for f in r8_scene_files:
            shutil.copy2(f, os.path.join(scene_refs_dir, os.path.basename(f)))
        print(f"  ✅ 场景参考图已复制: {len(r8_scene_files)} 张")

        if progress_callback:
            await progress_callback("image_generation", 80, "场景参考图就绪，正在准备 Shot 图...")

        # 5b: Shot 图
        images_dir = os.path.join(project_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        r8_shots = sorted(glob.glob(os.path.join(R8_DATA_DIR, "images", "shot_*.png")))
        r8_shot_count = len(r8_shots)

        shots = storyboard.get("shots", [])
        image_results = []
        # 用 project_id 作为静态 URL 的前缀段（前端访问 /static/outputs/{project_id}/images/shot_NN.png）
        _url_project_id = project_id or os.path.basename(os.path.normpath(project_dir))
        for i, shot in enumerate(shots):
            shot_id = shot.get("shot_id", i + 1)
            # 循环复用 R8 shot 图
            r8_idx = i % r8_shot_count if r8_shot_count > 0 else 0
            src = r8_shots[r8_idx] if r8_shots else None
            dst_name = f"shot_{shot_id:02d}.png"
            dst = os.path.join(images_dir, dst_name)
            if src and os.path.exists(src):
                shutil.copy2(src, dst)
                image_url = f"/static/outputs/{_url_project_id}/images/{dst_name}"
                # 写回 storyboard shot dict（前端预览依赖）
                shot["image_url"] = image_url
                image_results.append({
                    "shot_id": shot_id,
                    "success": True,
                    "image_path": dst,
                    "image_url": image_url,
                })
            else:
                image_results.append({"shot_id": shot_id, "success": False, "error": "R8 source missing"})
            print(f"    Shot {shot_id}: 复制 {os.path.basename(src) if src else 'N/A'} → {dst_name}")

        if progress_callback:
            await progress_callback("image_generation", 90, f"Shot 图就绪 ({len(image_results)} 张)...")

        return image_results

    def _save_json(self, directory: str, filename: str, data: dict) -> str:
        """保存JSON文件"""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def _get_location_id_for_scene(
        self,
        scene_id: int,
        screenplay: dict,
        unique_locations: Optional[List[dict]] = None
    ) -> Optional[str]:
        """
        从scene_id获取对应的location_id

        注意：screenplay中的location_id可能与outline的unique_locations不一致
        此方法会尝试从unique_locations中找到最匹配的location_id

        Args:
            scene_id: 场景ID（对应storyboard中的scene_id）
            screenplay: 分场剧本数据
            unique_locations: outline中的unique_locations列表

        Returns:
            location_id 或 None（如果找不到）
        """
        if not scene_id or not screenplay:
            return None

        # 获取screenplay中该scene的location_id
        screenplay_location_id = None
        for scene in screenplay.get("scenes", []):
            if scene.get("scene_id") == scene_id:
                screenplay_location_id = scene.get("location_id")
                break

        if not screenplay_location_id:
            return None

        # 如果没有unique_locations，直接返回screenplay的location_id
        if not unique_locations:
            return screenplay_location_id

        # 尝试精确匹配
        for loc in unique_locations:
            if loc.get("location_id") == screenplay_location_id:
                return screenplay_location_id

        # 精确匹配失败，使用第一个unique_location作为fallback
        # 这是因为LLM可能生成了不同的location_id
        if unique_locations:
            fallback_id = unique_locations[0].get("location_id")
            print(f"  ⚠️ location_id不匹配: screenplay用'{screenplay_location_id}', fallback到'{fallback_id}'")
            return fallback_id

        return screenplay_location_id

    def _save_prompt_quality_report(self, storyboard: dict, output_dir: str) -> None:
        """保存image_prompt质量报告"""
        report_lines = ["# Image Prompt 质量报告\n\n"]

        total_prompts = 0
        total_chars = 0
        quality_issues = 0

        for shot in storyboard.get("shots", []):
            shot_id = shot.get("shot_id")
            prompt = shot.get("image_prompt", "")
            total_prompts += 1
            total_chars += len(prompt)

            report_lines.append(f"## Shot {shot_id}\n")
            report_lines.append(f"**字符数**: {len(prompt)}\n")
            report_lines.append(f"**Prompt内容**:\n```\n{prompt}\n```\n")

            # T-D: 扩展关键词（复用 storyboard_director.py _check_prompt_quality 的 ~90 关键词列表）
            prompt_lower = prompt.lower()
            checks = {
                "镜头信息 (camera/framing)": any(k in prompt_lower for k in [
                    "shot", "close-up", "closeup", "wide", "medium", "extreme", "full",
                    "establishing", "insert", "cutaway", "pov", "over-the-shoulder",
                    "angle", "high angle", "low angle", "eye level", "dutch", "bird's eye",
                    "overhead", "tilted", "lens", "focus", "depth of field", "bokeh",
                    "35mm", "50mm", "telephoto", "wide-angle",
                    "composition", "framing", "foreground", "background", "midground",
                    "rule of thirds", "centered", "negative space", "symmetry",
                ]),
                "光线描述 (lighting/mood)": any(k in prompt_lower for k in [
                    "light", "lighting", "sunlight", "moonlight", "neon", "streetlight",
                    "ambient", "backlight", "rim light", "fill light", "key light",
                    "shadow", "shadows", "silhouette", "highlight", "contrast",
                    "glow", "reflection", "mood", "moody", "atmosphere", "atmospheric",
                    "dramatic", "cinematic", "ethereal", "dreamy", "gritty", "noir",
                    "warm", "cold", "cool", "golden hour", "blue hour",
                    "foggy", "misty", "hazy", "diffused", "harsh", "soft light",
                ]),
                "角色外观 (appearance/clothing)": any(k in prompt_lower for k in [
                    "expression", "face", "facial", "eyes", "gaze", "look", "stare",
                    "smile", "frown", "tears", "crying", "laughing",
                    "posture", "pose", "stance", "standing", "sitting", "leaning",
                    "gesture", "reaching", "holding", "gripping", "pointing", "walking",
                    "wearing", "dressed", "outfit", "clothes", "clothing",
                    " in a ", " in an ", " in his ", " in her ",
                    "shirt", "pants", "dress", "jacket", "coat", "sweater",
                    "glasses", "watch", "bag", "hat", "scarf", "hair",
                ]),
            }

            report_lines.append("**质量检查**:\n")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                report_lines.append(f"- {status} {check_name}\n")
                if not passed:
                    quality_issues += 1

            report_lines.append("\n")

        # 添加汇总
        avg_chars = total_chars / total_prompts if total_prompts > 0 else 0
        report_lines.insert(1, f"**汇总**: {total_prompts}个shots, 平均{avg_chars:.0f}字符/prompt, {quality_issues}个质量问题\n\n")

        # 保存报告
        report_path = os.path.join(output_dir, "prompt_quality_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(report_lines))

        # 同时保存到forclaudeweb
        try:
            with open("forclaudeweb/prompt_quality_report.md", "w", encoding="utf-8") as f:
                f.write("".join(report_lines))
        except Exception as e:
            logger.exception(
                f"[PipelineOrchestrator] 未预期异常 at forclaudeweb/prompt_quality_report.md 写入"
                f"（可能 forclaudeweb/ 目录不存在或权限不足）: {e}"
            )
            # 保留原逻辑：原来 pass 吞掉，继续 pass（不阻塞主流程）
            pass

    def _convert_characters_for_ref_manager(self, characters: dict) -> List[dict]:
        """
        转换角色数据格式，适配ReferenceImageManager

        Phase 2.0 characters 格式 → ReferenceImageManager 格式

        DEC-043 RISK-T20-10 (2026-05-19):
        - human → 原 physical hair/skin/face/clothing 字段拼接路径 (不动, 100% 一致性已验证)
        - 非 human → dispatch CharacterPromptBuilder.build_character_prompt()
          解决 anthropomorphic_animal / animal / robot 等被
          强行写为 "female, adult, hair, eyes, skin, face" 的 hardcoded 误描述

        同时修正：result dict 透传 `character_type` 字段 (ReferenceImageManager
        从 `character_type` 而非 `type` 读取角色类型, 见 reference_image_manager.py L658)。
        旧代码漏传 character_type → ReferenceImageManager 收到 'unknown' → 走通用兜底。
        """
        from app.services.character_prompt_builder import CharacterPromptBuilder
        builder = CharacterPromptBuilder()

        result = []
        for char in characters.get("characters", []):
            physical = char.get("physical", {})
            if not isinstance(physical, dict):
                physical = {}
            clothing = char.get("clothing", {})
            if not isinstance(clothing, dict):
                clothing = {}

            gender = char.get("gender", "")
            age = char.get("age_appearance", "adult")
            # T20-10: character_type 是 ReferenceImageManager 必读字段
            char_type = (char.get("character_type") or char.get("type") or "human")

            # 构建 description: human 走原路径, 非 human 走 CharacterPromptBuilder
            ct_lower = (char_type or "").strip().lower()
            if ct_lower and ct_lower != "human":
                try:
                    description = builder.build_character_prompt(char)
                except Exception:
                    description = char.get("description", "") or f"a {ct_lower} character"
            else:
                desc_parts = []
                if gender:
                    desc_parts.append(f"{gender}, {age}")

                if physical:
                    hair = f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}".strip()
                    if hair:
                        desc_parts.append(f"{hair} hair")

                    eye = physical.get('eye_color', '')
                    if eye:
                        desc_parts.append(f"{eye} eyes")

                    skin = physical.get('skin_tone', '')
                    if skin:
                        desc_parts.append(f"{skin} skin")

                    face = physical.get('face_shape', '')
                    if face:
                        desc_parts.append(f"{face} face")

                if clothing:
                    top = clothing.get('top', '')
                    if top:
                        desc_parts.append(f"wearing {top}")

                    bottom = clothing.get('bottom', '')
                    if bottom:
                        desc_parts.append(bottom)

                description = ", ".join(desc_parts) if desc_parts else "character"

            result.append({
                "id": char.get("id", ""),
                "name": char.get("name", ""),
                "name_en": char.get("name_en", ""),
                "description": description,
                "character_type": char_type,  # T20-10: ReferenceImageManager 必读
                "type": char_type,            # backward-compat: 旧 consumers 用 type
                "gender": gender,
                "age_appearance": age,
                "physical": physical,
                "clothing": clothing,
                # T20-10: 透传非 human 类型的 nested fields (animal/robot/etc.)
                # 这些字段在 CharacterPromptBuilder 中被读取，必须保留
                "animal": char.get("animal", {}),
                "fantasy_creature": char.get("fantasy_creature", {}),
                "robot": char.get("robot", {}),
                "object_personified": char.get("object_personified", {}),
                "hybrid": char.get("hybrid", {}),
                "insect": char.get("insect", {}),
                "aquatic": char.get("aquatic", {}),
                "plant": char.get("plant", {}),
                "mythological": char.get("mythological", {}),
                "supernatural": char.get("supernatural", {}),
                "undead": char.get("undead", {}),
                "elemental": char.get("elemental", {}),
                "alien": char.get("alien", {}),
                "vehicle_character": char.get("vehicle_character", {}),
                "digital_virtual": char.get("digital_virtual", {}),
                "concept_personified": char.get("concept_personified", {}),
                "miniature": char.get("miniature", {}),
                "giant": char.get("giant", {}),
                "human": char.get("human", {}),
                # 透传辅助字段
                "default_expression": char.get("default_expression", ""),
                "personality": char.get("personality", {}),
                "character_specific_directions": char.get("character_specific_directions", {}),
                "description_raw": char.get("description", ""),
            })

        return result


# 便捷函数
async def run_phase2_pipeline(
    idea: str,
    style_preset: str = "anime",
    target_duration_minutes: int = 3,
    output_dir: str = "./test_output/manualtest/phase2",
    generate_images: bool = True
) -> dict:
    """
    便捷函数：运行Phase 2.0完整流程

    Args:
        idea: 用户创意
        style_preset: 风格预设
        target_duration_minutes: 目标时长
        output_dir: 输出目录
        generate_images: 是否生成图像

    Returns:
        生成结果
    """
    orchestrator = Phase2PipelineOrchestrator(output_dir=output_dir)
    return await orchestrator.run(
        idea=idea,
        style_preset=style_preset,
        target_duration_minutes=target_duration_minutes,
        generate_images=generate_images
    )
