"""Job management service for async task tracking"""

import json
import logging
import time
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session_maker
from app.models.job import GenerationJob
from app.models.chapter import Chapter
from app.models.project import Project
from app.services.story_generator import StoryGenerator

logger = logging.getLogger("xuhua")


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
):
    """B-1: 使用短生命周期 session 更新 job 状态，避免长 pipeline 运行中 MySQL 连接超时"""
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

        await db.commit()


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
        async def progress_callback(stage: str, progress: int, message: str):
            await _update_job_short_session(
                job_id, stage=stage, progress=progress, message=message
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
                        setattr(chapter, column_name, json.dumps(data, ensure_ascii=False))
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
                progress_callback=progress_callback,
                checkpoint_callback=checkpoint_callback,
            )
            result = {"success": True, "data": pipeline_result}
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
        task_elapsed = time.time() - task_start
        logger.info(f"[JobManager] ✅ 生成任务完成 (总耗时 {task_elapsed:.1f}s)")
        await _update_job_short_session(
            job_id,
            status="completed",
            stage="story_generation",
            progress=100,
            message="故事生成完成！",
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
