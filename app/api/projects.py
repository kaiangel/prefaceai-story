"""Projects API"""

import asyncio
import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("xuhua")
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
    logger.info("[CreateProject] 收到参数:")
    logger.info(f"  idea: {project_data.original_idea[:50]}{'...' if len(project_data.original_idea) > 50 else ''}")
    logger.info(f"  document_text: {'有 (' + str(len(project_data.document_text)) + '字)' if project_data.document_text else '无'}")
    logger.info(f"  style_preset: {project_data.style_preset}")
    logger.info(f"  aspect_ratio: {project_data.aspect_ratio}")
    logger.info(f"  duration: {project_data.chapter_duration_minutes}min, characters: {project_data.character_count}")
    logger.info(f"  custom_style: {'有' if project_data.custom_style_analysis else '无'}")
    logger.info(f"  char_refs: {len(project_data.character_refs_analysis) if project_data.character_refs_analysis else 0}个")
    logger.info(f"  scene_refs: {len(project_data.scene_refs_analysis) if project_data.scene_refs_analysis else 0}个")

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
    try:
        await db.flush()
    except Exception as e:
        logger.error(f"[CreateProject] ❌ DB 写入失败: {e}")
        raise
    project_uuid = project.uuid
    logger.info(f"[CreateProject] ✅ 项目创建成功: id={project.id}")

    await db.commit()

    # 仅创建项目，不启动 pipeline（等 StageB confirm → start-generation）
    return ProjectResponse(
        project_id=project_uuid,
        chapter_id="",
        job_id="",
        status="created",
        message="项目创建成功",
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
    confirmed_outline: dict | None = None,
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
            confirmed_outline=confirmed_outline,
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
    logger.info("[GenerateOutline] 传给 LLM:")
    logger.info(f"  idea: {project.original_idea[:50]}...")
    logger.info(f"  style: {project.style_preset}")
    logger.info(f"  char_refs: {len(_char_refs) if _char_refs else 0}个")
    logger.info(f"  scene_refs: {len(_scene_refs) if _scene_refs else 0}个")
    logger.info(f"  custom_style: {_style_name or '无'}")

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
        logger.error(f"[GenerateOutline] ❌ 失败: {e}")
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
    """Store user-confirmed outline after StageB edits — 合并 raw + 用户编辑"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 读取 raw_outline（LLM 完整输出）
    raw = json.loads(project.raw_outline_json) if project.raw_outline_json else {}
    user = req.outline

    # 用户编辑覆盖
    if user.get("title"):
        raw["title"] = user["title"]
    if user.get("title_en"):
        raw["title_en"] = user["title_en"]
    if user.get("summary"):
        raw["summary"] = user["summary"]
        raw["logline"] = user["summary"]   # 同步更新 logline（Stage 2 CharacterDesigner 读这个）

    # 角色: 按索引匹配，更新名字/描述/性格
    if user.get("characters"):
        for i, uc in enumerate(user["characters"]):
            if i < len(raw.get("characters_overview", [])):
                raw["characters_overview"][i]["name_suggestion"] = uc.get("name", "")
                raw["characters_overview"][i]["name_en"] = uc.get("name_en", "")
                raw["characters_overview"][i]["description"] = uc.get("description", "")
                raw["characters_overview"][i]["personality"] = uc.get("personality", "")

    # 情节: 按 original_index 整体移动 dict（元数据跟随排序）
    if user.get("plot_points"):
        original = raw.get("plot_points", [])
        reordered = []
        for item in user["plot_points"]:
            if isinstance(item, dict):
                idx = item.get("original_index", 0)
                desc = item.get("description", "")
                if idx < len(original):
                    entry = original[idx].copy() if isinstance(original[idx], dict) else {"description": original[idx]}
                    entry["description"] = desc
                    reordered.append(entry)
            else:
                # 向后兼容: 纯字符串（旧前端）
                reordered.append({"description": item})
        if reordered:
            raw["plot_points"] = reordered

    # 结局选择
    if user.get("selected_ending"):
        raw["selected_ending"] = user["selected_ending"]
        # 方案 C: 用用户选的结局替换 plot_points 最后一条的 description
        if raw.get("plot_points"):
            last = raw["plot_points"][-1]
            if isinstance(last, dict):
                last["description"] = user["selected_ending"]
                last["user_selected_ending"] = True   # 标记，方便后续追溯

    # 情绪
    if user.get("mood"):
        if "visual_tone" not in raw:
            raw["visual_tone"] = {}
        raw["visual_tone"]["overall_mood"] = user["mood"]

    project.confirmed_outline_json = json.dumps(raw, ensure_ascii=False)
    if user.get("title"):
        project.title = user["title"]
    db.add(project)
    await db.commit()

    return {"success": True, "message": "大纲已确认"}


@router.post("/{project_id}/start-generation")
async def start_generation(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Start pipeline generation using confirmed (or raw) outline"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 读取确认后的大纲（优先），否则用原始大纲
    outline_json = project.confirmed_outline_json or project.raw_outline_json
    confirmed_outline = json.loads(outline_json) if outline_json else None

    # 创建 Chapter + GenerationJob
    chapter = Chapter(
        project_id=project.id,
        chapter_number=1,
        status="generating_story",
    )
    db.add(chapter)
    await db.flush()

    job = GenerationJob(
        chapter_id=chapter.id,
        status="queued",
        current_stage="story_generation",
        progress=0,
        stage_message="任务已创建，等待开始...",
    )
    db.add(job)
    await db.flush()

    await db.commit()

    # 启动 pipeline，传入 confirmed_outline
    asyncio.create_task(
        _run_generation_in_background(
            job_id=job.id,
            chapter_id=chapter.id,
            idea=project.original_idea,
            style=project.style_preset,
            chapter_number=1,
            total_chapters=project.total_chapters,
            duration_minutes=project.chapter_duration_minutes,
            character_count=project.character_count,
            language=project.language,
            confirmed_outline=confirmed_outline,
        )
    )

    logger.info(f"[StartGeneration] ✅ Pipeline 启动: project={project_id}, has_confirmed={'是' if project.confirmed_outline_json else '否'}")

    return ProjectResponse(
        project_id=project.uuid,
        chapter_id=chapter.uuid,
        job_id=job.uuid,
        status="generating_story",
        message="故事生成已开始",
    )


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
