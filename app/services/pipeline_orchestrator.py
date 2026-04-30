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


# P1-1 / P1-2: Stage durations (seconds) for backend-driven ETA
STAGE_DURATIONS = {
    "story_generation": 60,
    "character_design": 90,
    "character_ready": 30,
    "screenplay": 60,
    "storyboard": 300,
    "image_preparation": 60,
    "image_generation": 300,
    "bgm": 120,
}


def estimate_remaining(current_stage: str, stage_progress: float = 0.0) -> int:
    """
    P1-2: 根据当前 stage 和阶段内进度估算剩余秒数。
    stage_progress: 0.0-1.0，当前 stage 已完成比例
    """
    seq = list(STAGE_DURATIONS.keys())
    try:
        idx = seq.index(current_stage)
    except ValueError:
        return 0
    remaining = int(STAGE_DURATIONS[current_stage] * (1.0 - stage_progress))
    for s in seq[idx + 1 :]:
        remaining += STAGE_DURATIONS[s]
    return remaining


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
        progress_callback: Optional[Callable[..., Awaitable]] = None,
        checkpoint_callback: Optional[Callable[..., Awaitable]] = None,
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

            if confirmed_outline:
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

            characters = await self.character_designer.design(outline)
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
            max_wait = 1800  # 30 分钟超时（前端会主动调 confirm API）
            waited = 0
            confirmed = False
            logger.info(f"[Pipeline] R4-1: 开始等待用户确认角色 (超时 {max_wait}s)")
            if project_uuid:
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
                    # 每 30s 打一次轮询状态日志
                    if waited % 30 == 0:
                        logger.info(f"[Pipeline] R4-1: 仍在等待用户确认... (已等待 {waited}s)")
                if not confirmed:
                    print(f"  [R4-1] ⏰ 等待超时 ({max_wait}s)，自动继续")
                    logger.warning(f"[Pipeline] R4-1: ⏰ 等待超时 ({max_wait}s)，自动继续")
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
            # P1-1: Stage 3 完成 → 切换到 storyboard stage（entry callback）
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

            # 保存prompt质量报告
            self._save_prompt_quality_report(storyboard, project_dir)

            # B-6: Stage 4 完成后存中间结果到 chapter 表
            if checkpoint_callback:
                await checkpoint_callback("storyboard_json", storyboard)

            shot_count = len(storyboard.get("shots", []))
            print(f"✅ Stage 4 完成: {shot_count}个镜头")
            # P1-1: Stage 4 完成 → 切换到 image_preparation stage（entry callback）
            if progress_callback:
                await progress_callback("image_preparation", 65, "分镜创建完成，正在准备画面...")

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
                print("\n--- 5a. 生成角色参考图 ---")
                ref_manager = ReferenceImageManager()

                # 创建风格配置（自定义风格优先）
                project_style = ProjectStyleConfig(style_preset=style_preset)
                if custom_style_analysis:
                    from app.services.style_enforcer import StyleEnforcer
                    custom_enforcement = StyleEnforcer.create_custom_enforcement(custom_style_analysis)
                    project_style.custom_enforcement = custom_enforcement

                # 为每个角色生成参考图
                char_list = characters.get("characters", [])
                _char_refs_dir_stage5 = os.path.join(project_dir, "character_refs")
                for char in char_list:
                    char_id = char.get("id", "unknown")
                    char_name = char.get("name", char_id)
                    seed = (character_seeds or {}).get(char_id)

                    # P1-3 / R7-4: freshness check — 若 Stage 2 已为该角色生成过肖像
                    # 且肖像文件 mtime >= char.updated_at（adjust_character 后会更新），
                    # 则跳过肖像重生成（skip_portrait=True），直接复用已有肖像生成全身图。
                    _portrait_seed: "Image.Image | None" = None
                    _skip_portrait = False
                    _portrait_path = os.path.join(_char_refs_dir_stage5, f"{char_id}_portrait.png")
                    if os.path.exists(_portrait_path):
                        try:
                            _portrait_mtime = os.path.getmtime(_portrait_path)
                            # char.updated_at 为字符串 ISO 格式（Stage 2 写入时来自 characters_json）
                            _char_updated_at_str = char.get("updated_at")
                            _portrait_fresh = True  # 默认认为足够新鲜
                            if _char_updated_at_str:
                                from datetime import timezone
                                _char_dt = datetime.fromisoformat(
                                    _char_updated_at_str.replace("Z", "+00:00")
                                )
                                _char_ts = _char_dt.timestamp()
                                # 肖像文件比角色最后更新时间新才算新鲜
                                _portrait_fresh = _portrait_mtime > (_char_ts + 30)  # 30s buffer 避免文件系统精度漂移
                            if _portrait_fresh:
                                from PIL import Image as _PilImage
                                _portrait_seed = _PilImage.open(_portrait_path).convert("RGB")
                                _skip_portrait = True
                                print(f"  [R7-4] {char_name} 肖像已新鲜，跳过重生成，直接生成全身图")
                        except Exception as _fe:
                            logger.warning(f"[Pipeline] R7-4: 读取 {char_id} 肖像失败，重新生成: {_fe}")
                            _portrait_seed = None
                            _skip_portrait = False

                    if seed:
                        print(f"  生成 {char_name} 参考图（使用用户 seed 图）...", end=" ")
                    elif _skip_portrait:
                        print(f"  生成 {char_name} 参考图（复用新鲜肖像，只生成全身图）...", end=" ")
                    else:
                        print(f"  生成 {char_name} 参考图...", end=" ")
                    try:
                        await ref_manager.generate_character_multi_refs(
                            character=char,
                            project_style=project_style,
                            image_generator=self.image_generator,
                            seed_image=seed or _portrait_seed,
                            skip_portrait=_skip_portrait and not seed,
                        )
                        # 成本计数: skip_portrait 时只生成 fullbody（1 张），否则 2 张
                        _ref_count = 1 if (_skip_portrait and not seed) else 2
                        cost_tracker.add_cost("gemini_nb2", 0.067 * _ref_count, f"Ref {char_id} {'fullbody' if _ref_count == 1 else 'portrait+fullbody'}")
                        print("✅")
                    except Exception as e:
                        print(f"❌ {e}")

                print(f"✅ 角色参考图生成完成")

                # 保存角色参考图
                char_refs_dir = os.path.join(project_dir, "character_refs")
                os.makedirs(char_refs_dir, exist_ok=True)
                ref_manager.save_all_references(char_refs_dir)

                # 5a.5. 生成场景参考图
                print("\n--- 5a.5. 生成场景参考图 ---")
                unique_locations = outline.get("unique_locations", [])
                scene_ref_manager = None

                if unique_locations:
                    scene_ref_manager = SceneReferenceManager()
                    print(f"  共 {len(unique_locations)} 个场景位置")

                    # T21: 计算每个 location 的最大角色数量
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
                            scenes=[],  # Phase 2.0 直接用 unique_locations
                            project_style=project_style,
                            image_generator=self.image_generator,
                            unique_locations=unique_locations,
                            delay=3.0,
                            location_character_counts=location_char_counts,  # T21
                            seed_images=scene_seeds,  # 用户上传场景 seed 图
                        )

                        # 保存场景参考图
                        scene_refs_dir = os.path.join(project_dir, "scene_refs")
                        os.makedirs(scene_refs_dir, exist_ok=True)
                        for anchor_key, anchor_data in scene_anchors.items():
                            img = anchor_data.get('image')
                            if img:
                                img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))

                        # 成本计数: 场景参考图（每张 $0.067，interior + exterior = 2 张/location）
                        cost_tracker.add_cost(
                            "gemini_nb2", 0.067 * len(scene_anchors),
                            f"Scene refs {len(scene_anchors)} images"
                        )
                        print(f"✅ 场景参考图生成完成: {len(scene_anchors)}张")
                    except Exception as e:
                        print(f"⚠️ 场景参考图生成失败: {e}")
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
                        MAX_SHOT_RETRIES = 1  # T-B: 最多 retry 1 次，共 2 次尝试
                        best_result = None

                        for attempt in range(MAX_SHOT_RETRIES + 1):
                            if attempt > 0:
                                logger.info(f"    [T17] Retry {attempt}/{MAX_SHOT_RETRIES} Shot {shot_id}...")

                            # TASK-PARALLEL-M1: dispatcher provider-agnostic（不写死 provider 判断）
                            # ARCH-4: 传入 db_project_id 让 log_api_cost 真实 INSERT（NB2 路径通过 **kwargs 透传）
                            # D.15 P0: aspect_ratio 从 run() 参数读取，不再 hardcoded "2:3"
                            result = await self.image_generator.generate_shot_image_phase2_safe(
                                shot=shot,
                                storyboard=storyboard,
                                characters=characters,
                                style_preset=style_preset,
                                reference_images=all_refs,
                                screenplay=screenplay,
                                aspect_ratio=aspect_ratio,
                                use_native_text=self.use_native_text,
                                project_id=db_project_id,
                            )

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
                                key_props=key_props if key_props else None
                            )
                            logger.info(f"    [ShotValidator] Shot {shot_id}: valid={validation['valid']}, reason={validation['reason']}")

                            if validation["valid"]:
                                if attempt > 0:
                                    logger.info(f"    [T17] ✅ Shot {shot_id} retry 后验证通过")
                                break
                            else:
                                logger.info(f"    [T17] ⚠️ Shot {shot_id} 验证失败: {validation['reason']}")
                                if attempt == MAX_SHOT_RETRIES:
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
                        async with completed_lock:
                            completed_count += 1
                            _done = completed_count
                        if progress_callback:
                            try:
                                _pct = 65 + int(30 * _done / max(len(shots), 1))
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
                                _pct = 65 + int(30 * completed_count / max(len(shots), 1))
                                await progress_callback(
                                    "image_generation", _pct,
                                    f"已生成 {completed_count}/{len(shots)} 张图像（含失败）..."
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

                # P1-1: 进入真生图阶段 → 切换到 image_generation stage（entry callback）
                if progress_callback:
                    try:
                        await progress_callback("image_generation", 75, "开始绘制画面...")
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

                bgm_result = generate_bgm_for_chapter(
                    chapter_id=0,          # 手动测试模式无真实 chapter_id，用 0
                    project_id=0,          # 手动测试模式无真实 project_id，用 0
                    outline=outline,
                    screenplay=screenplay,
                    output_dir=project_dir,
                    story_type=_story_type,
                    visual_style_hint=_visual_style_hint,
                    regen_count=0,
                    bgm_volume=1.0,
                    is_change_bgm=False,
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
        """
        result = []
        for char in characters.get("characters", []):
            # 构建description
            physical = char.get("physical", {})
            clothing = char.get("clothing", {})

            desc_parts = []

            # 基本信息
            gender = char.get("gender", "")
            age = char.get("age_appearance", "adult")
            if gender:
                desc_parts.append(f"{gender}, {age}")

            # 外貌
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

            # 服装
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
                "type": char.get("type", "human"),
                "gender": gender,
                "age_appearance": age,
                "physical": physical,
                "clothing": clothing
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
