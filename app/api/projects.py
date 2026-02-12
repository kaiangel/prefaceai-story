"""Projects API"""

import asyncio
from uuid import uuid4
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session_maker
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.job import GenerationJob
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectDetail
from app.services.job_manager import JobManager, run_story_generation_task
from app.api.auth import DEMO_USERS

router = APIRouter(prefix="/api/projects", tags=["projects"])


def verify_user(x_user_id: str = Header(..., alias="X-User-ID")) -> str:
    """Verify user from header"""
    if x_user_id not in DEMO_USERS:
        raise HTTPException(status_code=401, detail="无效的用户")
    return x_user_id


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project and start generating the first chapter
    """
    # 1. Create project record
    project_id = str(uuid4())
    project = Project(
        id=project_id,
        user_id=user_id,
        title="未命名项目",  # Will be updated after story generation
        original_idea=project_data.original_idea,
        style_preset=project_data.style_preset,
        total_chapters=project_data.total_chapters,
        chapter_duration_minutes=project_data.chapter_duration_minutes,
        character_count=project_data.character_count,
        language=project_data.language,
        voice_preset=project_data.voice_preset,
    )
    db.add(project)

    # 2. Create first chapter record
    chapter_id = str(uuid4())
    chapter = Chapter(
        id=chapter_id,
        project_id=project_id,
        chapter_number=1,
        status="generating_story",
    )
    db.add(chapter)

    # 3. Create generation job
    job_id = str(uuid4())
    job = GenerationJob(
        id=job_id,
        chapter_id=chapter_id,
        status="queued",
        current_stage="story_generation",
        progress=0,
        stage_message="任务已创建，等待开始...",
    )
    db.add(job)

    await db.commit()

    # 4. Start background generation task
    asyncio.create_task(
        _run_generation_in_background(
            job_id=job_id,
            chapter_id=chapter_id,
            idea=project_data.original_idea,
            style=project_data.style_preset,
            chapter_number=1,
            total_chapters=project_data.total_chapters,
            duration_minutes=project_data.chapter_duration_minutes,
            character_count=project_data.character_count,
            language=project_data.language,
        )
    )

    return ProjectResponse(
        project_id=project_id,
        chapter_id=chapter_id,
        job_id=job_id,
        status="generating_story",
        message="故事生成已开始",
    )


async def _run_generation_in_background(
    job_id: str,
    chapter_id: str,
    idea: str,
    style: str,
    chapter_number: int,
    total_chapters: int,
    duration_minutes: int,
    character_count: int,
    language: str,
    previous_summary: str | None = None,
    characters_json: str | None = None,
):
    """Run story generation in background with new database session"""
    async with async_session_maker() as db:
        await run_story_generation_task(
            db=db,
            job_id=job_id,
            chapter_id=chapter_id,
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


@router.get("/", response_model=list[ProjectDetail])
async def list_projects(
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for current user"""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectDetail.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details"""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return ProjectDetail.model_validate(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its chapters"""
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    await db.delete(project)
    await db.commit()

    return {"success": True, "message": "项目已删除"}
