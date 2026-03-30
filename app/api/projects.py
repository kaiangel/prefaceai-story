"""Projects API"""

import asyncio
import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session_maker
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.job import GenerationJob
from app.models.audio_segment import AudioSegment
from app.models.scene_image import SceneImage, CharacterReference
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectDetail
from app.services.job_manager import JobManager, run_story_generation_task
from app.services.story_outline_generator import StoryOutlineGenerator
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/projects", tags=["projects"])


def serialize_project_detail(project: Project) -> ProjectDetail:
    return ProjectDetail(
        id=project.uuid,
        user_id=project.user_id,
        title=project.title,
        original_idea=project.original_idea,
        style_preset=project.style_preset,
        total_chapters=project.total_chapters,
        chapter_duration_minutes=project.chapter_duration_minutes,
        character_count=project.character_count,
        language=project.language,
        voice_preset=project.voice_preset,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def verify_user(user: User = Depends(get_current_user)) -> int:
    """Return the authenticated internal user id."""
    return user.id


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new project and start generating the first chapter
    """
    # 0. 校验: idea 和 document_text 不能同时为空
    if not project_data.original_idea.strip() and not (project_data.document_text or "").strip():
        raise HTTPException(status_code=400, detail="请输入故事创意或上传故事文档")

    # 1. Create project record
    # 埋点 6: 记录前端发来的参数
    print(f"[CreateProject] 收到参数:")
    print(f"  idea: {project_data.original_idea[:50]}{'...' if len(project_data.original_idea) > 50 else ''}")
    print(f"  document_text: {'有 (' + str(len(project_data.document_text)) + '字)' if project_data.document_text else '无'}")
    print(f"  style_preset: {project_data.style_preset}")
    print(f"  aspect_ratio: {project_data.aspect_ratio}")
    print(f"  duration: {project_data.chapter_duration_minutes}min, characters: {project_data.character_count}")
    print(f"  custom_style: {'有' if project_data.custom_style_analysis else '无'}")
    print(f"  char_refs: {len(project_data.character_refs_analysis) if project_data.character_refs_analysis else 0}个")
    print(f"  scene_refs: {len(project_data.scene_refs_analysis) if project_data.scene_refs_analysis else 0}个")

    # 如果有文档文本，拼接到 original_idea
    idea = project_data.original_idea.strip()
    if project_data.document_text:
        doc = project_data.document_text.strip()
        if idea:
            idea = f"{idea}\n\n---\n附加文档内容:\n{doc}"
        else:
            idea = doc

    project = Project(
        user_id=user_id,
        title="未命名项目",  # Will be updated after story generation
        original_idea=idea,
        style_preset=project_data.style_preset,
        total_chapters=project_data.total_chapters,
        chapter_duration_minutes=project_data.chapter_duration_minutes,
        character_count=project_data.character_count,
        language=project_data.language,
        voice_preset=project_data.voice_preset,
        aspect_ratio=project_data.aspect_ratio,
        custom_style_analysis_json=json.dumps(project_data.custom_style_analysis, ensure_ascii=False) if project_data.custom_style_analysis else None,
        character_refs_analysis_json=json.dumps(project_data.character_refs_analysis, ensure_ascii=False) if project_data.character_refs_analysis else None,
        scene_refs_analysis_json=json.dumps(project_data.scene_refs_analysis, ensure_ascii=False) if project_data.scene_refs_analysis else None,
    )
    db.add(project)
    await db.flush()
    project_id = project.id
    project_uuid = project.uuid

    # 2. Create first chapter record
    chapter = Chapter(
        project_id=project_id,
        chapter_number=1,
        status="generating_story",
    )
    db.add(chapter)
    await db.flush()
    chapter_id = chapter.id
    chapter_uuid = chapter.uuid

    # 3. Create generation job
    job = GenerationJob(
        chapter_id=chapter_id,
        status="queued",
        current_stage="story_generation",
        progress=0,
        stage_message="任务已创建，等待开始...",
    )
    db.add(job)
    await db.flush()
    job_id = job.id
    job_uuid = job.uuid

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
        project_id=project_uuid,
        chapter_id=chapter_uuid,
        job_id=job_uuid,
        status="generating_story",
        message="故事生成已开始",
    )


async def _run_generation_in_background(
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
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for current user"""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [serialize_project_detail(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Get project details"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    return serialize_project_detail(project)


@router.post("/{project_id}/generate-outline")
async def generate_outline(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate story outline for a project using Stage 1 (StoryOutlineGenerator)"""
    # 1. Verify project exists and belongs to current user
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. Map chapter_duration_minutes to character_count default
    duration = project.chapter_duration_minutes or 3
    character_count = project.character_count or 3

    # 埋点 7: 记录传给 LLM 的参数
    _char_refs = json.loads(project.character_refs_analysis_json) if project.character_refs_analysis_json else None
    _scene_refs = json.loads(project.scene_refs_analysis_json) if project.scene_refs_analysis_json else None
    _style_name = json.loads(project.custom_style_analysis_json).get("style_display_name") if project.custom_style_analysis_json else None
    print(f"[GenerateOutline] 传给 LLM:")
    print(f"  idea: {project.original_idea[:50]}...")
    print(f"  style: {project.style_preset}")
    print(f"  char_refs: {len(_char_refs) if _char_refs else 0}个")
    print(f"  scene_refs: {len(_scene_refs) if _scene_refs else 0}个")
    print(f"  custom_style: {_style_name or '无'}")

    # 3. Call StoryOutlineGenerator
    generator = StoryOutlineGenerator()
    try:
        outline = await generator.generate(
            idea=project.original_idea,
            style_preset=project.style_preset,
            target_duration_minutes=duration,
            language=project.language or "zh-CN",
            character_count=character_count,
            character_refs_analysis=json.loads(project.character_refs_analysis_json) if project.character_refs_analysis_json else None,
            scene_refs_analysis=json.loads(project.scene_refs_analysis_json) if project.scene_refs_analysis_json else None,
            custom_style_name=json.loads(project.custom_style_analysis_json).get("style_display_name") if project.custom_style_analysis_json else None,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")

    # 4. Store raw LLM outline + update project title
    project.raw_outline_json = json.dumps(outline, ensure_ascii=False)
    if outline.get("title"):
        project.title = outline["title"]
    db.add(project)
    await db.flush()

    # 5. Map snake_case → camelCase for frontend
    characters = []
    for i, char in enumerate(outline.get("characters_overview", []), 1):
        characters.append({
            "id": f"char_{i:03d}",
            "name": char.get("name_suggestion", ""),
            "nameEn": char.get("name_en", ""),
            "description": char.get("description", ""),
            "personality": char.get("personality", ""),
        })

    plot_points = []
    for i, pp in enumerate(outline.get("plot_points", []), 1):
        plot_points.append({
            "id": f"pp_{i}",
            "description": pp.get("description", "") if isinstance(pp, dict) else str(pp),
        })

    endings = []
    for i, ending in enumerate(outline.get("ending_options", []), 1):
        endings.append({
            "id": ending.get("id", f"ending_{i}"),
            "description": ending.get("description", ""),
            "isSelected": i == 1,
        })

    return {
        "title": outline.get("title", ""),
        "titleEn": outline.get("title_en", ""),
        "summary": outline.get("summary", ""),
        "characters": characters,
        "plotPoints": plot_points,
        "endings": endings,
        "mood": outline.get("mood", ""),
    }


class ConfirmOutlineRequest(BaseModel):
    """用户确认/修改后的大纲"""
    outline: dict


@router.post("/{project_id}/confirm-outline")
async def confirm_outline(
    project_id: str,
    req: ConfirmOutlineRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Store user-confirmed outline after StageB edits"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.confirmed_outline_json = json.dumps(req.outline, ensure_ascii=False)
    db.add(project)
    await db.commit()

    return {"success": True, "message": "大纲已确认"}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its chapters"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    internal_project_id = project.id
    chapter_ids_result = await db.execute(
        select(Chapter.id).where(Chapter.project_id == internal_project_id)
    )
    chapter_ids = list(chapter_ids_result.scalars().all())

    if chapter_ids:
        await db.execute(
            delete(SceneImage).where(SceneImage.chapter_id.in_(chapter_ids))
        )
        await db.execute(
            delete(AudioSegment).where(AudioSegment.chapter_id.in_(chapter_ids))
        )
        await db.execute(
            delete(GenerationJob).where(GenerationJob.chapter_id.in_(chapter_ids))
        )

    await db.execute(
        delete(CharacterReference).where(CharacterReference.project_id == internal_project_id)
    )
    await db.execute(
        delete(Chapter).where(Chapter.project_id == internal_project_id)
    )
    await db.delete(project)
    await db.commit()

    return {"success": True, "message": "项目已删除"}
