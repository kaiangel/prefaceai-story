"""Projects API"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
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


def _to_utc_iso(dt: datetime | None) -> str:
    """Convert naive UTC datetime (from DB) to ISO 8601 string with 'Z' suffix.

    DB stores datetime.utcnow() which has no tzinfo.
    Adding timezone.utc + isoformat() + 'Z' gives '2026-04-28T15:38:00+00:00Z'
    which is redundant, so we use replace(tzinfo=timezone.utc).isoformat() to get
    '2026-04-28T15:38:00+00:00', then replace '+00:00' → 'Z' for compactness.
    """
    if dt is None:
        return ""
    if dt.tzinfo is None:
        # Naive datetime from DB — treat as UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def _parse_storyboard_cover_and_count(storyboard_json_str: str | None) -> tuple[str | None, int]:
    """Parse storyboard_json to extract cover_image_url (shots[0].image_url) and shot_count.

    Handles two formats:
      - list of shots (legacy): [{shot_id, image_url, ...}, ...]
      - dict with shots key: {"shots": [...], ...}

    Returns (cover_image_url, shot_count).
    cover_image_url is None if no shots or shots[0] has no image_url.
    """
    if not storyboard_json_str:
        return None, 0
    try:
        sb = json.loads(storyboard_json_str)
    except (json.JSONDecodeError, TypeError):
        return None, 0

    # Normalise to list of shots
    if isinstance(sb, list):
        shots = sb
    elif isinstance(sb, dict):
        shots = sb.get("shots", [])
        if not isinstance(shots, list):
            shots = []
    else:
        return None, 0

    shot_count = len(shots)
    cover_image_url: str | None = None
    if shots:
        first = shots[0]
        if isinstance(first, dict):
            url = first.get("image_url")
            if url and isinstance(url, str):
                cover_image_url = url

    return cover_image_url, shot_count


def _parse_mood(confirmed_outline_json_str: str | None) -> str | None:
    """Parse confirmed_outline_json and return user_selected_mood → mood → None (3-level fallback)."""
    if not confirmed_outline_json_str:
        return None
    try:
        outline = json.loads(confirmed_outline_json_str)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(outline, dict):
        return None
    # 3-layer fallback: user_selected_mood → mood → None
    return outline.get("user_selected_mood") or outline.get("mood") or None


def serialize_project_detail(project: Project, chapter: "Chapter | None" = None) -> ProjectDetail:
    """Serialize a Project ORM object to ProjectDetail schema.

    Args:
        project: Project ORM instance.
        chapter: Optional chapter_number=1 Chapter ORM instance for list-endpoint
                 enrichment (cover_image_url, shot_count, mood). If None,
                 those fields default to null/0.
    """
    confirmed_outline = None
    if project.confirmed_outline_json:
        try:
            confirmed_outline = json.loads(project.confirmed_outline_json)
        except json.JSONDecodeError:
            confirmed_outline = None

    # R7-1: Extract cover + shot_count from chapter storyboard; mood from outline
    storyboard_json_str = chapter.storyboard_json if chapter else None
    cover_image_url, shot_count = _parse_storyboard_cover_and_count(storyboard_json_str)
    mood = _parse_mood(project.confirmed_outline_json)

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
        created_at=_to_utc_iso(project.created_at),     # R7-1: ISO 8601 with Z
        updated_at=_to_utc_iso(project.updated_at),     # R7-1: ISO 8601 with Z
        aspect_ratio=project.aspect_ratio,              # R6: 透传画面比例
        confirmed_outline=confirmed_outline,            # R6: 解析后的大纲（含 summary/mood/user_selected_mood）
        cover_image_url=cover_image_url,                # R7-1: storyboard shots[0].image_url
        shot_count=shot_count,                          # R7-1: storyboard shots 数组长度
        mood=mood,                                      # R7-1: user_selected_mood ?? mood ?? None
        is_favorite=bool(project.is_favorite),          # R7-2: null 老数据视为 False
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
    project_uuid: str | None = None,
    aspect_ratio: str = "2:3",  # D.15 P0: 用户选择的画幅，默认 "2:3" 兼容旧调用
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
            project_uuid=project_uuid,
            aspect_ratio=aspect_ratio,  # D.15 P0: 透传用户选择的画幅
        )


@router.get("/", response_model=list[ProjectDetail])
async def list_projects(
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for current user.

    R7-1: Returns cover_image_url + shot_count + mood + ISO time fields.
    Uses a single additional query for chapter_number=1 rows to avoid N+1.
    """
    # 1. Fetch all projects for this user
    result = await db.execute(
        select(Project)
        .where(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()

    if not projects:
        return []

    # 2. Batch-fetch chapter_number=1 for all projects in ONE query (avoid N+1)
    project_ids = [p.id for p in projects]
    ch_result = await db.execute(
        select(Chapter)
        .where(
            Chapter.project_id.in_(project_ids),
            Chapter.chapter_number == 1,
        )
    )
    chapters_by_project_id: dict[int, Chapter] = {
        ch.project_id: ch for ch in ch_result.scalars().all()
    }

    # 3. Serialize each project with its chapter-1 (or None if not yet created)
    return [
        serialize_project_detail(p, chapters_by_project_id.get(p.id))
        for p in projects
    ]


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

    # 场景数据（从 unique_locations 映射）
    scenes = []
    for i, loc in enumerate(outline.get("unique_locations", [])):
        scene_data = {
            "id": f"scene_{i+1}",
            "name": loc.get("display_name", f"场景{i+1}"),
            "description": loc.get("interior_description", "") or loc.get("exterior_description", ""),
            "locationType": loc.get("location_type", "interior"),
        }
        # F-3: Pass through description_zh (Chinese scene description from Stage 1 LLM) if available
        if loc.get("description_zh"):
            scene_data["description_zh"] = loc["description_zh"]
        scenes.append(scene_data)

    return {
        "title": outline.get("title", ""),
        "titleEn": outline.get("title_en", ""),
        "summary": outline.get("summary", ""),
        "characters": characters,
        "plotPoints": plot_points,
        "endings": endings,
        "mood": outline.get("mood", ""),
        "scenes": scenes,
    }


class ConfirmOutlineRequest(BaseModel):
    """用户确认/修改后的大纲"""
    outline: dict
    user_selected_mood: str | None = None  # OBS-4: 顶层情绪选择（可选，也可在 outline.mood 中传）


@router.post("/{project_id}/confirm-outline")
async def confirm_outline(
    project_id: str,
    req: ConfirmOutlineRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Store user-confirmed outline after StageB edits — 合并 raw + 用户编辑"""
    logger.info(f"[ConfirmOutline] 收到确认请求: project={project_id}")
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
                    # R6-2 fix: 前端追加的新 plot_point（如 selected_ending），idx 越界，直接用 description
                    reordered.append({"description": desc})
            else:
                # 向后兼容: 纯字符串（旧前端）
                reordered.append({"description": item})
        if reordered:
            raw["plot_points"] = reordered

    # 结局选择
    if user.get("selected_ending"):
        raw["selected_ending"] = user["selected_ending"]
        # 前端 R6-2 已改为把 selected_ending 追加到 plot_points 末尾，后端不再替换

    # 情绪 — 优先级: user_selected_mood (顶层) > outline.mood (嵌套)
    # OBS-4: 同时支持 req.user_selected_mood（新增顶层字段）和 req.outline.mood（旧方式）
    _effective_mood = req.user_selected_mood or user.get("mood") or ""
    if _effective_mood:
        if "visual_tone" not in raw:
            raw["visual_tone"] = {}
        raw["visual_tone"]["overall_mood"] = _effective_mood
        raw["mood"] = _effective_mood  # R6-1b: 同步更新顶层 mood，Pipeline 读的是这个字段
        raw["user_selected_mood"] = _effective_mood  # OBS-4: 明确标记为用户选择的情绪
        logger.info(f"[ConfirmOutline] OBS-4: user_selected_mood={_effective_mood!r}")

    project.confirmed_outline_json = json.dumps(raw, ensure_ascii=False)
    if user.get("title"):
        project.title = user["title"]
    db.add(project)
    await db.commit()

    # UX-2 (A2): Sonnet 4.6 大纲一致性检查（非阻塞，失败时不影响确认流程）
    warnings: list[str] = []
    has_inconsistency = False
    try:
        from app.config import settings as _settings
        import anthropic as _anthropic
        _claude = _anthropic.AsyncAnthropic(api_key=_settings.ANTHROPIC_API_KEY)
        _outline_summary = json.dumps({
            "title": raw.get("title", ""),
            "mood": raw.get("mood", ""),
            "characters_overview": raw.get("characters_overview", [])[:5],
            "plot_points": raw.get("plot_points", [])[:6],
            "selected_ending": raw.get("selected_ending", ""),
        }, ensure_ascii=False)
        _check_prompt = f"""你是一个故事大纲质量检查员。请检查以下大纲的内在一致性：
- 角色设定是否与情节节拍相符？
- 情绪基调（mood）是否与故事走向一致？
- 是否有明显矛盾或不合逻辑之处？

大纲摘要：
{_outline_summary}

请输出 JSON，格式：{{"warnings": ["问题描述1", "问题描述2"], "has_inconsistency": true/false}}
如果无问题，warnings 为空数组，has_inconsistency 为 false。只输出 JSON，不要其他文字。"""
        _resp = await _claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": _check_prompt}],
        )
        _check_text = _resp.content[0].text.strip()
        # 解析 JSON（可能带 markdown 代码块）
        if "```" in _check_text:
            _check_text = _check_text.split("```")[1]
            if _check_text.startswith("json"):
                _check_text = _check_text[4:]
        _check_result = json.loads(_check_text.strip())
        warnings = _check_result.get("warnings", [])
        has_inconsistency = _check_result.get("has_inconsistency", False)
        logger.info(f"[ConfirmOutline] UX-2: 一致性检查完成, has_inconsistency={has_inconsistency}, warnings={len(warnings)}")
    except Exception as _ux2_e:
        logger.warning(f"[ConfirmOutline] UX-2: 一致性检查失败（非阻塞）: {_ux2_e}")

    logger.info(f"[ConfirmOutline] ✅ 大纲已确认: project={project_id}")
    return {"success": True, "message": "大纲已确认", "warnings": warnings, "has_inconsistency": has_inconsistency}


@router.post("/{project_id}/confirm-characters")
async def confirm_characters(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """R4-1: 用户确认角色设计 — pipeline 轮询此字段后继续 Stage 3"""
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    project.characters_confirmed = True
    db.add(project)
    await db.flush()

    logger.info(f"[ConfirmCharacters] ✅ 角色已确认: project={project_id}")
    return {"success": True}


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

    # R4-1: 每次启动 pipeline 时重置 characters_confirmed
    project.characters_confirmed = False
    db.add(project)
    await db.flush()

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
    # D.15 P0: 传入 project.aspect_ratio，确保用户选择的画幅真正生效
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
            project_uuid=project.uuid,
            aspect_ratio=project.aspect_ratio or "2:3",  # D.15 P0: 真实画幅，None 兜底 "2:3"
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


@router.get("/{project_id}/generation-result")
async def get_generation_result(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Get pipeline generation result (storyboard + image URLs) for StageD"""
    logger.info(f"[GenerationResult] 请求: project={project_id}")
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取第一个 chapter
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.project_id == project.id).order_by(Chapter.chapter_number).limit(1)
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="暂无生成数据")

    # 获取 job 状态
    job_result = await db.execute(
        select(GenerationJob).where(GenerationJob.chapter_id == chapter.id)
        .order_by(GenerationJob.created_at.desc()).limit(1)
    )
    job = job_result.scalar_one_or_none()
    job_status = job.status if job else "unknown"

    if job_status not in ("completed",):
        return {"status": job_status, "storyboard": None, "characters": [], "totalShots": 0}

    # 从 storyboard_json 读取 shots
    storyboard = json.loads(chapter.storyboard_json) if chapter.storyboard_json else {}
    characters_data = json.loads(chapter.characters_json) if chapter.characters_json else []

    shots = []
    for shot in storyboard.get("shots", []):
        if shot.get("deleted"):
            continue  # 跳过已软删除的 shot (KI-003)
        shot_id = shot.get("shot_id", 0)
        narration = shot.get("narration_segment", "")
        text_overlay = shot.get("text_overlay", {})
        shots.append({
            "shotId": shot_id,
            "imageUrl": f"/api/projects/{project_id}/images/shot_{shot_id:02d}.png",
            "narration": narration,
            "textOverlay": {
                "type": text_overlay.get("text_type", "none"),
                "text": " ".join(text_overlay.get("chinese_text", [])) if text_overlay.get("chinese_text") else "",
            } if text_overlay else None,
        })

    logger.info(f"[GenerationResult] ✅ 返回: project={project_id}, shots={len(shots)}")
    return {
        "status": "completed",
        "storyboard": {"shots": shots},
        "characters": characters_data,
        "totalShots": len(shots),
    }


@router.get("/{project_id}/images/{filename}")
async def serve_project_image(
    project_id: str,
    filename: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Serve generated images from pipeline output directory"""
    from fastapi.responses import FileResponse

    # 验证项目归属
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 构建文件路径: ./output/{project_uuid}/images/{filename}
    image_path = os.path.join("output", project_id, "images", filename)

    # 安全检查: 防止路径遍历
    abs_path = os.path.abspath(image_path)
    abs_base = os.path.abspath(os.path.join("output", project_id, "images"))
    if not abs_path.startswith(abs_base):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    content_type = "image/png"
    if filename.lower().endswith((".jpg", ".jpeg")):
        content_type = "image/jpeg"

    return FileResponse(image_path, media_type=content_type, filename=filename)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project and all its chapters"""
    logger.info(f"[DeleteProject] 请求删除: project={project_id}")
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

    logger.info(f"[DeleteProject] ✅ 项目已删除: project={project_id}")
    return {"success": True, "message": "项目已删除"}


# ============ RB-7: 角色调整 API ============


class CharacterAdjustRequest(BaseModel):
    """角色调整请求"""
    adjustment: str  # 用户自然语言调整指令，如 "想让他胖一点"


@router.post("/{project_id}/characters/{char_id}/adjust")
async def adjust_character(
    project_id: str,
    char_id: str,
    req: CharacterAdjustRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    RB-7: 角色调整 API — 用 Haiku 4.5 重写角色描述

    请求体: { "adjustment": "想让他胖一点" }
    返回: 更新后的角色数据（含新的 description、physical、clothing）
    同时更新 chapter 表的 characters_json
    """
    import anthropic as anthropic_module

    # 1. 验证项目归属
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 读取大纲中的角色数据（从 confirmed_outline 或 raw_outline）
    outline_json = project.confirmed_outline_json or project.raw_outline_json
    if not outline_json:
        raise HTTPException(status_code=400, detail="项目尚未生成大纲")

    outline = json.loads(outline_json)
    characters_overview = outline.get("characters_overview", [])

    # 3. 查找指定角色
    # char_id 格式: "char_001" → 按索引匹配 characters_overview
    target_char = None
    char_index = None
    try:
        idx = int(char_id.replace("char_", "")) - 1
        if 0 <= idx < len(characters_overview):
            target_char = characters_overview[idx]
            char_index = idx
    except (ValueError, IndexError):
        pass

    if target_char is None:
        raise HTTPException(status_code=404, detail=f"角色 {char_id} 不存在")

    # 4. 调用 Haiku 4.5 重写角色描述
    from app.config import settings as app_settings
    if not app_settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY 未配置")

    client = anthropic_module.Anthropic(api_key=app_settings.ANTHROPIC_API_KEY)

    prompt = f"""你是一个专业的角色设计师。请根据用户的调整指令，修改角色的外观描述。

## 当前角色数据
```json
{json.dumps(target_char, ensure_ascii=False, indent=2)}
```

## 用户调整指令
{req.adjustment}

## 要求
1. 根据用户指令修改相应的 physical 和/或 clothing 字段
2. 同步更新 description 字段使其与修改一致
3. 保持未被调整指令提到的字段不变
4. physical 字段的值必须全英文（用于图像生成 prompt）
5. clothing 字段的值必须全英文
6. description 字段用中文
7. 如果用户要求的改动不涉及 physical 或 clothing，只更新 description

直接输出修改后的完整角色 JSON 对象（不要 ```json``` 包裹，不要解释文字）。
保持原始 JSON 结构，所有字段都保留。"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.content[0].text.strip()

        # 解析 JSON 响应
        # 去除可能的 markdown 代码块
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)

        updated_char = json.loads(content)

    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="角色调整 LLM 返回格式异常")
    except Exception as e:
        logger.error(f"[AdjustCharacter] ❌ Haiku 调用失败: {e}")
        raise HTTPException(status_code=500, detail=f"角色调整失败: {str(e)}")

    # 5. 更新 outline 中的角色数据
    characters_overview[char_index] = updated_char
    outline["characters_overview"] = characters_overview

    # 写回 confirmed_outline（如有）或 raw_outline
    if project.confirmed_outline_json:
        project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
    else:
        project.raw_outline_json = json.dumps(outline, ensure_ascii=False)

    # 6. 同步更新 chapter 表的 characters_json（如果已存在）
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.project_id == project.id).order_by(Chapter.chapter_number).limit(1)
    )
    chapter = chapter_result.scalar_one_or_none()
    if chapter and chapter.characters_json:
        try:
            chars_list = json.loads(chapter.characters_json)
            if char_index < len(chars_list):
                # 合并更新: 只更新 physical / clothing / description
                for key in ("physical", "clothing", "description"):
                    if key in updated_char:
                        chars_list[char_index][key] = updated_char[key]
                chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
        except (json.JSONDecodeError, IndexError):
            pass

    db.add(project)
    await db.commit()

    logger.info(f"[AdjustCharacter] ✅ 角色 {char_id} 已调整: {req.adjustment[:30]}...")

    # 7. P1-3 / R7-3: 角色描述更新后立即重生成 portrait，并写入 updated_at 时间戳
    portrait_url: str | None = None
    try:
        from app.services.reference_image_manager import ReferenceImageManager as _RIM
        from app.models.style_config import ProjectStyleConfig as _PSC
        from app.services.image_generator import ImageGenerator as _IG
        import os as _os

        _ref_manager = _RIM()
        _project_style = _PSC(style_preset=project.style_preset or "realistic")
        _image_gen = _IG()

        _portrait_result = await _ref_manager.generate_character_reference(
            character=updated_char,
            project_style=_project_style,
            image_generator=_image_gen,
            ref_type="portrait",
        )
        if _portrait_result.get("success") and _portrait_result.get("pil_image"):
            # 确保 character_refs 目录存在
            _outputs_root = _os.path.abspath("output")
            _char_refs_dir = _os.path.join(_outputs_root, str(project.uuid), "character_refs")
            _os.makedirs(_char_refs_dir, exist_ok=True)
            _portrait_path = _os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
            _portrait_result["pil_image"].save(_portrait_path)
            portrait_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_portrait.png"
            logger.info(f"[AdjustCharacter] R7-3: {char_id} 肖像已重生成 → {_portrait_path}")

            # 更新 updated_at 时间戳到角色 JSON，Stage 5 freshness check 用此判断肖像是否新鲜
            from datetime import datetime as _dt
            _now_iso = _dt.utcnow().isoformat() + "Z"
            updated_char["updated_at"] = _now_iso
            characters_overview[char_index] = updated_char
            outline["characters_overview"] = characters_overview
            if project.confirmed_outline_json:
                project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
            else:
                project.raw_outline_json = json.dumps(outline, ensure_ascii=False)

            # 同步更新 characters_json 中的 portrait_url 和 updated_at
            if chapter and chapter.characters_json:
                try:
                    chars_list = json.loads(chapter.characters_json)
                    if char_index < len(chars_list):
                        chars_list[char_index]["portrait_url"] = portrait_url
                        chars_list[char_index]["updated_at"] = _now_iso
                        chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
                except (json.JSONDecodeError, IndexError):
                    pass

            db.add(project)
            await db.commit()
        else:
            logger.warning(f"[AdjustCharacter] R7-3: {char_id} 肖像重生成失败: {_portrait_result.get('error')}")
    except Exception as _pe:
        logger.warning(f"[AdjustCharacter] R7-3: 肖像重生成异常（非阻塞）: {_pe}")

    return {
        "success": True,
        "character": updated_char,
        "char_id": char_id,
        "portrait_url": portrait_url,
        "message": "角色已调整",
    }


@router.post("/{project_id}/characters/{char_id}/regenerate-portrait")
async def regenerate_portrait(
    project_id: str,
    char_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    P1-3 / R7-3: 手动重生成指定角色的 portrait。

    触发场景：用户在角色确认界面点击"重绘头像"按钮。
    - 读取项目当前角色数据
    - 调用 ReferenceImageManager.generate_character_reference()（portrait 类型）
    - 保存到 character_refs/{char_id}_portrait.png
    - 更新 characters_json 中的 portrait_url 和 updated_at
    返回: { success, portrait_url, char_id }
    """
    from app.services.reference_image_manager import ReferenceImageManager as _RIM
    from app.models.style_config import ProjectStyleConfig as _PSC
    from app.services.image_generator import ImageGenerator as _IG
    from datetime import datetime as _dt

    # 1. 验证项目归属
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 读取角色数据
    outline_json = project.confirmed_outline_json or project.raw_outline_json
    if not outline_json:
        raise HTTPException(status_code=400, detail="项目尚未生成大纲")

    outline = json.loads(outline_json)
    characters_overview = outline.get("characters_overview", [])

    target_char = None
    char_index = None
    try:
        idx = int(char_id.replace("char_", "")) - 1
        if 0 <= idx < len(characters_overview):
            target_char = characters_overview[idx]
            char_index = idx
    except (ValueError, IndexError):
        pass

    if target_char is None:
        raise HTTPException(status_code=404, detail=f"角色 {char_id} 不存在")

    # 3. 生成新 portrait
    _ref_manager = _RIM()
    _project_style = _PSC(style_preset=project.style_preset or "realistic")
    _image_gen = _IG()

    try:
        _portrait_result = await _ref_manager.generate_character_reference(
            character=target_char,
            project_style=_project_style,
            image_generator=_image_gen,
            ref_type="portrait",
        )
    except Exception as e:
        logger.error(f"[RegeneratePortrait] ❌ {char_id} 生图失败: {e}")
        raise HTTPException(status_code=500, detail=f"肖像生成失败: {str(e)}")

    if not (_portrait_result.get("success") and _portrait_result.get("pil_image")):
        raise HTTPException(status_code=500, detail=f"肖像生成失败: {_portrait_result.get('error', '未知错误')}")

    # 4. 保存图片
    _outputs_root = os.path.abspath("output")
    _char_refs_dir = os.path.join(_outputs_root, str(project.uuid), "character_refs")
    os.makedirs(_char_refs_dir, exist_ok=True)
    _portrait_path = os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
    _portrait_result["pil_image"].save(_portrait_path)
    portrait_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_portrait.png"
    logger.info(f"[RegeneratePortrait] ✅ {char_id} → {_portrait_path}")

    # 5. 更新 updated_at 时间戳（Stage 5 freshness check 依赖此字段）
    _now_iso = _dt.utcnow().isoformat() + "Z"
    target_char["updated_at"] = _now_iso
    target_char["portrait_url"] = portrait_url
    characters_overview[char_index] = target_char
    outline["characters_overview"] = characters_overview
    if project.confirmed_outline_json:
        project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
    else:
        project.raw_outline_json = json.dumps(outline, ensure_ascii=False)

    # 6. 同步更新 chapter.characters_json
    chapter_result = await db.execute(
        select(Chapter).where(Chapter.project_id == project.id).order_by(Chapter.chapter_number).limit(1)
    )
    chapter = chapter_result.scalar_one_or_none()
    if chapter and chapter.characters_json:
        try:
            chars_list = json.loads(chapter.characters_json)
            if char_index < len(chars_list):
                chars_list[char_index]["portrait_url"] = portrait_url
                chars_list[char_index]["updated_at"] = _now_iso
                chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
        except (json.JSONDecodeError, IndexError):
            pass

    db.add(project)
    await db.commit()

    return {
        "success": True,
        "char_id": char_id,
        "portrait_url": portrait_url,
        "message": "肖像已重新生成",
    }


# ---------------------------------------------------------------------------
# R7-2: 点赞 endpoint
# ---------------------------------------------------------------------------

@router.post("/{project_id}/favorite")
async def toggle_favorite(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    R7-2: toggle is_favorite 状态。
    - 每次调用取反（False → True → False ...）
    - null（老数据）视为 False，toggle 后变 True
    返回: { "success": true, "is_favorite": bool }
    """
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # null 视为 False，toggle 取反
    current = bool(project.is_favorite)
    project.is_favorite = not current
    db.add(project)
    await db.commit()

    logger.info(f"[Favorite] project={project_id} is_favorite={project.is_favorite}")
    return {"success": True, "is_favorite": project.is_favorite}


# ---------------------------------------------------------------------------
# R7-2: 分享 endpoint（生成 token）
# ---------------------------------------------------------------------------

@router.post("/{project_id}/share")
async def create_share_link(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    R7-2: 生成分享链接 token。
    - 同一 project 可重复调用（每次返回已有 token，不重复生成）
    - Token 永久有效（Founder 决策 Wave 5.1）
    返回: { "success": true, "share_url": "/s/{token}", "token": "..." }
    """
    from app.models.share import ShareToken

    # 验证项目归属
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 幂等：已有 token 直接返回
    existing = await db.execute(
        select(ShareToken).where(ShareToken.project_uuid == project_id).limit(1)
    )
    token_row = existing.scalar_one_or_none()

    if token_row is None:
        token_row = ShareToken(project_uuid=project_id)
        db.add(token_row)
        await db.commit()
        await db.refresh(token_row)
        logger.info(f"[Share] 新建 token project={project_id} token={token_row.token}")
    else:
        logger.info(f"[Share] 已有 token project={project_id} token={token_row.token}")

    return {
        "success": True,
        "share_url": f"/s/{token_row.token}",
        "token": token_row.token,
    }
