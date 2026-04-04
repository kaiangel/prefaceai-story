"""Job management service for async task tracking"""

import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job import GenerationJob
from app.models.chapter import Chapter
from app.models.project import Project
from app.services.story_generator import StoryGenerator


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
):
    """
    Background task to generate story

    This function runs the story generation and updates the database
    """
    job_manager = JobManager(db)
    generator = StoryGenerator()

    try:
        # Update job status to processing
        await job_manager.update_job_status(
            job_id,
            status="processing",
            stage="story_generation",
            progress=10,
            message="正在生成故事剧本...",
            estimated_seconds=60,
        )

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
                generate_images=False,  # 先只生成文本，图像后续阶段处理
                confirmed_outline=confirmed_outline,
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
            # Update job as failed
            await job_manager.update_job_status(
                job_id,
                status="failed",
                progress=0,
                message=f"生成失败: {result.get('error', '未知错误')}",
            )
            # Update chapter status
            chapter_result = await db.execute(
                select(Chapter).where(Chapter.id == chapter_id)
            )
            chapter = chapter_result.scalar_one()
            chapter.status = "failed"
            chapter.error_message = result.get("error", "未知错误")
            await db.commit()
            return

        # Update chapter with generated story
        story_data = result["data"]
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one()

        chapter.status = "generating_images"  # Ready for next phase
        chapter.full_script = json.dumps(story_data, ensure_ascii=False)
        chapter.summary = story_data.get("summary", "")
        chapter.characters_json = json.dumps(
            story_data.get("characters", []), ensure_ascii=False
        )
        chapter.scenes_json = json.dumps(
            story_data.get("scenes", []), ensure_ascii=False
        )

        # Update project title if first chapter
        if chapter_number == 1 and story_data.get("title"):
            project_result = await db.execute(
                select(Project).where(Project.id == chapter.project_id)
            )
            project = project_result.scalar_one()
            if project.title == "未命名项目":
                project.title = story_data["title"]

        await db.commit()

        # Update job as completed
        await job_manager.update_job_status(
            job_id,
            status="completed",
            stage="story_generation",
            progress=100,
            message="故事生成完成！",
        )

    except Exception as e:
        # Handle unexpected errors
        await job_manager.update_job_status(
            job_id,
            status="failed",
            progress=0,
            message=f"系统错误: {str(e)}",
        )
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        if chapter:
            chapter.status = "failed"
            chapter.error_message = str(e)
            await db.commit()
