"""Projects API"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
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


def _strip_markdown_json_fence(text: str) -> str:
    """Wave 10 / RISK-T16-8: strip ```json ... ``` fence before json.loads.

    LLM 有时返回 markdown 代码块包裹的 JSON，例如:
        ```json
        {"warnings": [...], "has_inconsistency": false}
        ```
    直接 json.loads() 会失败。本函数剥离前后 fence，让 json.loads 能直接解析。

    覆盖场景:
    - 有前后 fence ("```json...```")
    - 只有前 fence ("```json..." 无闭合)
    - 只有后 fence ("...```")
    - 无 fence（直接返回原文）
    """
    text = text.strip()
    # 剥离前置 fence（```json 或 ```）
    if text.startswith("```json"):
        text = text[7:].lstrip("\n")
    elif text.startswith("```"):
        text = text[3:].lstrip("\n")
    # 剥离后置 fence
    if text.endswith("```"):
        text = text[:-3].rstrip("\n")
    return text.strip()


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


def _map_outline_to_response(outline: dict) -> dict:
    """Map Stage 1 LLM outline (snake_case) → frontend camelCase response dict.

    Extracted from generate_outline so it can be reused by the idempotent
    fast-path (returning cached raw_outline_json without re-calling the LLM).
    """
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

    # raw_outline: Stage 1 LLM 原始输出（pre-confirm 状态，供前端 hydrate 用）
    raw_outline = None
    if project.raw_outline_json:
        try:
            raw_outline = json.loads(project.raw_outline_json)
        except json.JSONDecodeError:
            raw_outline = None

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
        raw_outline=raw_outline,                        # hotfix: Stage 1 原始输出，前端 hydrate 用
        cover_image_url=cover_image_url,                # R7-1: storyboard shots[0].image_url
        shot_count=shot_count,                          # R7-1: storyboard shots 数组长度
        mood=mood,                                      # R7-1: user_selected_mood ?? mood ?? None
        is_favorite=bool(project.is_favorite),          # R7-2: null 老数据视为 False
        user_selected_mood=project.user_selected_mood,  # B33: Stage A 用户选的情绪基调
        characters_confirmed=bool(project.characters_confirmed),  # B49: 角色确认状态
        scenes_confirmed=bool(project.scenes_confirmed),  # B58 / R4-2: 场景确认状态（Stage 3 -> Stage 4 闸门）
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
        # B33: 持久化 Stage A 用户选择的情绪基调
        user_selected_mood=project_data.user_selected_mood,
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
    user_selected_mood: str | None = None,  # B33: Stage A 用户选的情绪基调
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
            user_selected_mood=user_selected_mood,  # B33: 透传 Stage A 情绪基调
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
    force_regenerate: bool = Query(default=False, description="强制重新生成（跳过幂等缓存），用户主动重生时传 true"),
):
    """Generate story outline for a project using Stage 1 (StoryOutlineGenerator)"""
    # 1. Verify project exists and belongs to current user
    result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 1.5 幂等检查: 如果 raw_outline_json 已存且非空，直接返回缓存结果（不调 LLM）
    # 除非前端明确传 ?force_regenerate=true
    if not force_regenerate and project.raw_outline_json:
        try:
            cached = json.loads(project.raw_outline_json)
            if cached:
                logger.info(
                    f"[GenerateOutline] 幂等: project {project_id} 已有 raw_outline，"
                    f"直接返已存数据（不调 LLM）"
                )
                return _map_outline_to_response(cached)
        except json.JSONDecodeError:
            pass  # 解析失败则重新生成

    # 2. Map chapter_duration_minutes to character_count default
    duration = project.chapter_duration_minutes or 3
    character_count = project.character_count or 3

    # B33: 读取用户在 Stage A 选择的情绪基调（DB 列，最高优先级）
    user_selected_mood = project.user_selected_mood  # str | None

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
    logger.info(f"  user_selected_mood: {user_selected_mood or '无（LLM 自由决定）'}")

    # B34: 从 project 对象中提取所有需要的数据，然后提交 READ 事务，
    # 确保 LLM 调用（254s 级别）不在 DB 事务范围内持有 row-level lock。
    # MySQL autobegin: db.execute(SELECT) 会隐式开启事务，db.commit() 释放锁。
    _idea = project.original_idea
    _style_preset = project.style_preset
    _language = project.language or "zh-CN"
    _project_id_int = project.id  # 保留 id 用于后续写入（uuid 已从 URL 获取）
    _char_refs_json = project.character_refs_analysis_json
    _scene_refs_json = project.scene_refs_analysis_json
    _custom_style_json = project.custom_style_analysis_json

    # 提交 READ 事务（释放 MySQL row-level lock）
    await db.commit()
    logger.info("[GenerateOutline] B34: READ 事务已提交，释放 row lock，开始调 LLM...")

    # 3. Call StoryOutlineGenerator（不在 DB 事务内）
    generator = StoryOutlineGenerator()
    try:
        outline = await generator.generate(
            idea=_idea,
            style_preset=_style_preset,
            target_duration_minutes=duration,
            language=_language,
            character_count=character_count,
            character_refs_analysis=json.loads(_char_refs_json) if _char_refs_json else None,
            scene_refs_analysis=json.loads(_scene_refs_json) if _scene_refs_json else None,
            custom_style_name=json.loads(_custom_style_json).get("style_display_name") if _custom_style_json else None,
            user_selected_mood=user_selected_mood,  # B33: 注入用户选的情绪基调
        )
    except Exception as e:
        logger.error(f"[GenerateOutline] ❌ 失败: {e}")
        raise HTTPException(status_code=500, detail=f"大纲生成失败: {str(e)}")

    # 4. 短事务写入 raw_outline_json + title（LLM 调用完成后才开启，短暂持有锁）
    async with async_session_maker() as write_db:
        write_result = await write_db.execute(
            select(Project).where(Project.uuid == project_id)
        )
        write_project = write_result.scalar_one_or_none()
        if write_project:
            write_project.raw_outline_json = json.dumps(outline, ensure_ascii=False)
            if outline.get("title"):
                write_project.title = outline["title"]
            await write_db.commit()
            logger.info("[GenerateOutline] B34: WRITE 事务已提交（短事务，LLM 调用后）")
        else:
            logger.warning(f"[GenerateOutline] 写入 raw_outline 时找不到 project {project_id}")

    # 5. Map snake_case → camelCase for frontend (via shared helper)
    return _map_outline_to_response(outline)


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

    # B52 cascade fix: 同步 confirmed_outline.characters_overview.description → chapter.characters_json[*].description
    # 原因: confirm_outline 后 characters_overview 有 Founder 改的外貌描述 (含"红色长发")
    # 但 chapter.characters_json 在 Stage 2 生成，description 字段为空 → Stage 4 读不到改动 → cascade 黑发
    try:
        chars_overview = raw.get("characters_overview", [])
        if chars_overview:
            # 查找 chapter
            _chapter_result = await db.execute(
                select(Chapter).where(Chapter.project_id == project.id).order_by(Chapter.chapter_number).limit(1)
            )
            _chapter = _chapter_result.scalar_one_or_none()
            if _chapter and _chapter.characters_json:
                _chars_list = json.loads(_chapter.characters_json)
                _changed = False
                for i, ov_char in enumerate(chars_overview):
                    if i < len(_chars_list):
                        ov_desc = ov_char.get("description", "").strip()
                        if ov_desc:
                            _chars_list[i]["description"] = ov_desc
                            _changed = True
                            logger.info(
                                f"[ConfirmOutline] B52: char_{i+1:03d} description 同步: {ov_desc[:50]}..."
                            )
                if _changed:
                    _chapter.characters_json = json.dumps(_chars_list, ensure_ascii=False)
                    db.add(_chapter)
                    await db.commit()
                    logger.info(f"[ConfirmOutline] B52: chapter.characters_json description 同步完成")
    except Exception as _sync_e:
        logger.warning(f"[ConfirmOutline] B52: description 同步失败（非阻塞）: {_sync_e}")

    # UX-2 (A2): Sonnet 4.6 大纲一致性检查（非阻塞，失败时不影响确认流程）
    # D1 — BUG-T13-UX-2-LLM-JSON-TRUNCATED (2026-05-12):
    # 改用 _llm_helpers.extract_json_from_llm_response 通用 helper（B59-hotfix 已验证）
    # 原先自己的 JSON 解析逻辑在 Sonnet 长输出截断时（```json 未闭合）会抛 json.JSONDecodeError
    warnings: list[str] = []
    has_inconsistency = False
    try:
        from app.config import settings as _settings
        from app.services._llm_helpers import extract_json_from_llm_response as _parse_llm_json
        import anthropic as _anthropic
        _claude = _anthropic.AsyncAnthropic(api_key=_settings.ANTHROPIC_API_KEY)
        _outline_summary = json.dumps({
            "title": raw.get("title", ""),
            "mood": raw.get("mood", ""),
            "characters_overview": raw.get("characters_overview", [])[:5],
            "plot_points": raw.get("plot_points", [])[:6],
            "selected_ending": raw.get("selected_ending", ""),
        }, ensure_ascii=False)
        # RISK-T20-8 (2026-05-18): UX-2 prompt 加 R6-2 设计说明
        # R6-2 设计: 用户选的 ending 已经追加到 plot_points 末尾（projects.py:569-573 + StageB.tsx:204-208）,
        # 不在 selected_ending 字段（selected_ending 仅作"用户选了哪个"的元数据反向引用,
        # 但 plot_points[-1] 才是真正的故事结局节拍）。
        # 若不告诉 LLM 此设计, LLM 看到 selected_ending="" 就会 WARNING "大纲缺少结局节拍" — false positive。
        # universal: 任何故事 (3-5 endings, 任何 mood) 都需要这条规则。
        _check_prompt = f"""你是一个故事大纲质量检查员。请检查以下大纲的内在一致性：
- 角色设定是否与情节节拍相符？
- 情绪基调（mood）是否与故事走向一致？
- 是否有明显矛盾或不合逻辑之处？

## 重要：数据结构说明（R6-2 设计，2026-05-13）

用户在前端选好"结局选项"后，该结局已经**作为最后一个 plot_point 追加到 plot_points 末尾**，
不写入 outline.selected_ending 字段（该字段仅作元数据反向引用，可能为空字符串或缺失）。

判断"故事是否有结局"的正确方式：
- **正确**：检查 plot_points 的最后一个元素（plot_points[-1]）是否是结局性描述
- **错误**：检查 outline.selected_ending 是否为空 — selected_ending 为空是 R6-2 设计的正常状态，不是"缺少结局"

因此：**不要**因为 selected_ending 为空就报"大纲缺少结局节拍/故事在 crisis 中断"。
只有当 plot_points[-1] 仍是 crisis/中段节拍（没有 resolution/climax 性质的结尾描述）时，才能报缺结局。

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
        # Wave 10 / RISK-T16-8: 先显式剥 markdown fence，再用 _llm_helpers 通用 helper
        # （两层防御：_strip_markdown_json_fence 直接剥 fence → json.loads 可直接解析；
        # _parse_llm_json 作为第二道防线处理更复杂的格式）
        _check_text_clean = _strip_markdown_json_fence(_check_text)
        # D1: 改用 _llm_helpers 通用 helper（4 策略容错，处理未闭合 ``` 场景）
        _check_result = _parse_llm_json(_check_text_clean)
        if _check_result is not None:
            _raw_warnings = _check_result.get("warnings", [])
            has_inconsistency = _check_result.get("has_inconsistency", False)
            # RISK-T14-13-backend: 将 string warnings 转为 structured objects 返给 frontend
            # 每条 warning string → {type, message, affected_field}（frontend Banner 用 message 展示）
            for _w in _raw_warnings:
                if isinstance(_w, dict):
                    # LLM 直接输出了 object 格式
                    warnings.append(_w)
                else:
                    # LLM 输出字符串，推断 type 和 affected_field
                    _w_str = str(_w)
                    _affected = "general"
                    if any(kw in _w_str for kw in ["角色", "人物", "主角"]):
                        _affected = "characters"
                    elif any(kw in _w_str for kw in ["情节", "剧情", "故事"]):
                        _affected = "plot_points"
                    elif any(kw in _w_str for kw in ["结局", "ending"]):
                        _affected = "selected_ending"
                    elif any(kw in _w_str for kw in ["情绪", "基调", "mood"]):
                        _affected = "mood"
                    warnings.append({
                        "type": "inconsistency",
                        "message": _w_str,
                        "affected_field": _affected,
                    })
            logger.info(f"[ConfirmOutline] UX-2: 一致性检查完成, has_inconsistency={has_inconsistency}, warnings={len(warnings)}")
        else:
            logger.warning(f"[ConfirmOutline] UX-2: 一致性检查 JSON 解析失败（非阻塞），fallback OK: text={_check_text_clean[:100]}")
    except Exception as _ux2_e:
        logger.warning(f"[ConfirmOutline] UX-2: 一致性检查失败（非阻塞）: {_ux2_e}")

    logger.info(f"[ConfirmOutline] ✅ 大纲已确认: project={project_id}")
    return {
        "success": True,
        "message": "大纲已确认",
        "inconsistency_warnings": warnings,  # RISK-T14-13-backend: structured warnings for frontend
        "has_inconsistency": has_inconsistency,
        # keep legacy field for backward compat (frontend may still read 'warnings')
        "warnings": [w["message"] if isinstance(w, dict) else w for w in warnings],
    }


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


class ConfirmScenesRequest(BaseModel):
    """
    B58 / R4-2: 用户确认场景请求体

    用户可选择 携带 modified_scenes：
      - 不传：仅设 scenes_confirmed=True，保留 Stage 3 输出的 scenes_json 不变
      - 传值：用 modified_scenes 替换 chapter.scenes_json（保留用户编辑）

    modified_scenes 是用户在 ScenePreview 编辑后的 scenes 数组。
    schema 不强约束内部结构（Stage 3 输出可能演化），透传到 chapter.scenes_json。
    """
    modified_scenes: list[dict] | None = None


@router.post("/{project_id}/chapters/{chapter_number}/confirm-scenes")
async def confirm_scenes(
    project_id: str,
    chapter_number: int,
    payload: ConfirmScenesRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """B58 / R4-2: 用户确认分场剧本 — pipeline R4-2 wait loop 轮询此字段后继续 Stage 4

    流程：
      1. 验证 project 归属 + chapter 存在 + scenes_json 非空（Stage 3 必须已跑完）
      2. 若 payload.modified_scenes 非空 → 用其替换 chapter.scenes_json（保留用户编辑）
      3. project.scenes_confirmed = True
      4. 返回 200 + 最新 scenes

    与 R4-1 (/confirm-characters) 对称：
      - R4-1 等 characters_confirmed → 解锁 Stage 3
      - R4-2 等 scenes_confirmed → 解锁 Stage 4
    """
    # 1. 项目归属验证
    proj_result = await db.execute(
        select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. chapter 存在 + Stage 3 已跑完（scenes_json 非空）
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project.id,
            Chapter.chapter_number == chapter_number,
        )
    )
    chapter = chapter_result.scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    if not chapter.scenes_json:
        raise HTTPException(
            status_code=409,
            detail="场景尚未生成完成，请稍候再确认（Stage 3 进行中）",
        )

    # 3. 若 payload 含 modified_scenes → Wave 10 / RISK-T16-4: merge 而非 replace
    #    保留 LLM 原字段（含 action_beats 等 Stage 4 必需字段），
    #    仅用 modified_scenes 的字段覆盖用户改的部分。
    if payload.modified_scenes is not None:
        try:
            existing_scenes = json.loads(chapter.scenes_json) if chapter.scenes_json else []
            # 构建 existing_dict — key 为 str(scene_id) 或 str(id)
            existing_dict: dict = {}
            for s in existing_scenes:
                sid = s.get("scene_id") or s.get("id")
                if sid is not None:
                    existing_dict[str(sid)] = s

            merged: list = []
            for modified in payload.modified_scenes:
                sid = modified.get("scene_id") or modified.get("id")
                sid_key = str(sid) if sid is not None else None
                if sid_key and sid_key in existing_dict:
                    # 找到原 scene → 以 modified 字段覆盖（保留未传字段如 action_beats）
                    merged_scene = {**existing_dict[sid_key], **modified}
                    merged.append(merged_scene)
                else:
                    # 新增的 scene（用户加场景），直接追加
                    merged.append(modified)

            chapter.scenes_json = json.dumps(merged, ensure_ascii=False)
            db.add(chapter)
            logger.info(
                f"[ConfirmScenes] B58 merge (Wave 10 / RISK-T16-4): "
                f"existing={len(existing_scenes)} + modified={len(payload.modified_scenes)} "
                f"→ merged={len(merged)} "
                f"(保留 action_beats 等 LLM 字段, project={project_id}, chapter={chapter_number})"
            )
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"modified_scenes 序列化失败: {type(e).__name__}: {e}",
            )

    # 4. 标记 scenes_confirmed
    project.scenes_confirmed = True
    db.add(project)
    await db.commit()

    logger.info(f"[ConfirmScenes] ✅ 场景已确认: project={project_id}, chapter={chapter_number}")

    # 5. 返回最新 scenes（前端 hydrate / 显示用）
    try:
        scenes_data = json.loads(chapter.scenes_json) if chapter.scenes_json else []
    except (TypeError, ValueError):
        scenes_data = []

    return {
        "success": True,
        "scenes_confirmed": True,
        "scenes": scenes_data,
    }


@router.post("/{project_id}/confirm-scenes")
async def confirm_scenes_project_alias(
    project_id: str,
    payload: ConfirmScenesRequest,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """C1-backend — BUG-T13-SCENES-CONFIRM-PATH-MISMATCH (2026-05-12)

    Project-level alias for POST /api/projects/{project_id}/chapters/1/confirm-scenes

    背景：confirm-outline 和 confirm-characters 挂在 project 级别（/confirm-outline, /confirm-characters），
    但 confirm-scenes 只有 chapter 级别（/chapters/{n}/confirm-scenes），设计不对称。
    Frontend 按 project 级别构造路径调用 → 404 → R4-2 wait loop 无法解锁。

    修复：此 alias 转发到 chapter_number=1 的 confirm-scenes 端点，保持向后兼容。
    原有 chapter 级别 POST /api/projects/{project_id}/chapters/1/confirm-scenes 仍然保留。
    """
    return await confirm_scenes(
        project_id=project_id,
        chapter_number=1,
        payload=payload,
        user_id=user_id,
        db=db,
    )


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
    # B58 / R4-2: 每次启动 pipeline 时重置 scenes_confirmed（避免上次残留导致 R4-2 wait loop 直接跳过）
    project.scenes_confirmed = False
    # T21-NEW-7 DEC-047: R4-3 启动 pipeline 时重置 scene_references_confirmed (镜像 R4-1/R4-2)
    project.scene_references_confirmed = False
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
    # B33: 传入 user_selected_mood，确保 BGM 生成时应用用户选择的情绪基调
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
            user_selected_mood=project.user_selected_mood,  # B33: Stage A 情绪基调
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
    # T22-NEW-4 (2026-05-22): 旧 `import anthropic as anthropic_module` 已删,
    # LLM 调用改走 llm_fallback_chain.call_llm_with_fallback (Haiku → Gemini → Sonnet)

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

    # 4. 调用 Haiku 4.5 重写角色描述 — T22-NEW-4 (2026-05-22): 三层 fallback chain
    # Haiku → Gemini 3.1 Flash → Sonnet 4.6 (跨 provider 优先, KEY_LEARNINGS #55)
    from app.config import settings as app_settings
    if not app_settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY 未配置")

    from app.services.llm_fallback_chain import (
        call_llm_with_fallback as _call_llm_with_fallback,
        friendly_error_message as _friendly_err,
    )

    prompt = f"""你是一个专业的角色设计师。请根据用户的调整指令，修改角色的外观描述。

## 当前角色数据
```json
{json.dumps(target_char, ensure_ascii=False, indent=2)}
```

## 用户调整指令
{req.adjustment}

## 要求
1. 根据用户指令修改相应的 physical 和/或 clothing 字段
2. **MANDATORY**: 必须同步更新 description 字段使其与所有改动完全一致（2-3句中英双语，如"红色长波浪发，深棕色眼睛。Bright red wavy long hair, dark brown eyes."）
3. **MANDATORY**: physical 字段的每一个子字段必须同步更新——特别是：
   - 用户说"红发" → hair_color 必须改为 "bright_red" / "fiery_red"（具体英文颜色词，禁止保留旧颜色）
   - 用户说"短发" → hair_style 必须改为对应英文描述
   - 用户说"蓝眼" → eye_color 必须改为 "bright_blue" 等
   - 其余 physical 子字段（eye_color/skin_tone/hair_style/hair_texture等）若未涉及则保持不变
4. **MANDATORY clothing schema**: clothing 字段**必须是 dict 结构**（绝对不可输出为 str），必须包含以下子字段:
   - top: str（上衣描述，含颜色款式细节，全英文）
   - bottom: str（下装描述，全英文）
   - shoes: str（鞋子描述，全英文）
   - accessories: List[str]（配饰列表，全英文）
   - style: str（整体风格，全英文）
   - 用户说"换衣服换成米黄色毛衣" → clothing.top = "beige knit sweater"（其他子字段保持原值）
   - **严禁**把整个 clothing 字段压缩为一个字符串（例如 clothing: "米黄色毛衣" 是错误的）
5. clothing 字段的值必须全英文（用于图像生成 prompt）
6. 保持未被调整指令提到的字段不变
7. description 字段必须包含中文 + 英文双语（先中文再英文）
8. 如果用户要求的改动不涉及 physical 或 clothing，只更新 description

**重要**: 检查你的输出——description 中描述的颜色/特征必须与 physical.hair_color 等字段完全一致，不能有矛盾。

直接输出修改后的完整角色 JSON 对象（不要 ```json``` 包裹，不要解释文字）。
保持原始 JSON 结构，所有字段都保留。"""

    try:
        # T22-NEW-4: 三层 fallback (Haiku → Gemini Flash → Sonnet)
        # call_llm_with_fallback 永不抛异常, 返 FallbackResult.success bool
        fb_result = await _call_llm_with_fallback(
            user=prompt,
            max_tokens=2000,
            operation_label="adjust_character",
        )
        if not fb_result.success:
            logger.error(
                f"[AdjustCharacter] ❌ T22-NEW-4 fallback chain 全部失败: "
                f"{fb_result.error} (尝试 {len(fb_result.attempts)} 次)"
            )
            raise HTTPException(status_code=500, detail=_friendly_err(fb_result))

        content = fb_result.text.strip()
        logger.info(
            f"[AdjustCharacter] T22-NEW-4 LLM ok via {fb_result.provider_used}:"
            f"{fb_result.model_used} (chain_depth={fb_result.chain_depth})"
        )

        # 解析 JSON 响应
        # 去除可能的 markdown 代码块
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)

        updated_char = json.loads(content)

        # B58-followup: validate clothing is dict (Haiku 可能输出 str，违反 schema 约束)
        if 'clothing' in updated_char and isinstance(updated_char['clothing'], str):
            logger.warning(f"[AdjustCharacter] B58-followup: Haiku output clothing as str, fallback to dict structure")
            original_clothing = target_char.get('clothing', {})
            if isinstance(original_clothing, dict):
                original_clothing = dict(original_clothing)
                original_clothing['top'] = updated_char['clothing']
                updated_char['clothing'] = original_clothing
            else:
                updated_char['clothing'] = {
                    'top': updated_char['clothing'],
                    'bottom': '',
                    'shoes': '',
                    'accessories': [],
                    'style': ''
                }

    except HTTPException:
        # T22-NEW-4: 上面 fallback 全失败抛的 HTTPException 直接重抛, 不被下面 catch
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="角色调整 LLM 返回格式异常")
    except Exception as e:
        logger.error(f"[AdjustCharacter] ❌ LLM 调用失败: {e}")
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

        # RISK-T17-9 fix: 传入现有 portrait 作 reference，锁定 identity ground truth
        # Wave 10 P2 已修 reference_image_manager.py L107 接收 portrait_ref 参数，
        # 但 projects.py 此处调用时没传 → 修复入口失效，Seedream 完全靠 prompt 重生脸
        _outputs_root = _os.path.abspath("output")
        _char_refs_dir = _os.path.join(_outputs_root, str(project.uuid), "character_refs")
        _existing_portrait_path = _os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
        _existing_portrait_pil = None
        if _os.path.exists(_existing_portrait_path):
            from PIL import Image as _PilImage
            _existing_portrait_pil = _PilImage.open(_existing_portrait_path).convert("RGB")

        _portrait_result = await _ref_manager.generate_character_reference(
            character=updated_char,
            project_style=_project_style,
            image_generator=_image_gen,
            ref_type="portrait",
            portrait_ref=_existing_portrait_pil,
        )
        if _portrait_result.get("success") and _portrait_result.get("pil_image"):
            # 确保 character_refs 目录存在
            _os.makedirs(_char_refs_dir, exist_ok=True)
            _portrait_path = _os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
            _portrait_result["pil_image"].save(_portrait_path)
            # T21-NEW-4 (2026-05-21): portrait_url 加 ?v={epoch} cache-buster
            # 真根因: portrait URL 同名覆盖 (char_001_portrait.png), 浏览器 cache 旧 404 不重请求.
            # 镜像 Shot regenerate L2315 模式: ?v={int(time.time())}, 重生时 epoch 变 → URL 变.
            import time as _time
            _v_ts = int(_time.time())
            portrait_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_portrait.png?v={_v_ts}"
            logger.info(f"[AdjustCharacter] T21-NEW-4 R7-3: {char_id} 肖像已重生成 → {_portrait_path} (cache-buster v={_v_ts})")

            # 更新 updated_at 时间戳到角色 JSON，Stage 5 freshness check 用此判断肖像是否新鲜
            from datetime import datetime as _dt
            _now_iso = _dt.utcnow().isoformat() + "Z"
            updated_char["updated_at"] = _now_iso
            updated_char["portrait_url"] = portrait_url  # T21-NEW-4: outline 同写 cache-busted URL
            characters_overview[char_index] = updated_char
            outline["characters_overview"] = characters_overview
            if project.confirmed_outline_json:
                project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
            else:
                project.raw_outline_json = json.dumps(outline, ensure_ascii=False)

            # 同步更新 characters_json 中的 portrait_url 和 updated_at (T21-NEW-4: 带 ?v=)
            if chapter and chapter.characters_json:
                try:
                    chars_list = json.loads(chapter.characters_json)
                    if char_index < len(chars_list):
                        chars_list[char_index]["portrait_url"] = portrait_url  # 带 cache-buster
                        chars_list[char_index]["updated_at"] = _now_iso
                        chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
                except (json.JSONDecodeError, IndexError):
                    pass

            db.add(project)
            await db.commit()

            # B57 cascade fix: adjust 后同步重生 fullbody（用新 portrait 作参考）
            # 原因: Stage 5 shot 用 fullbody 作参考，若 portrait 换红发但 fullbody 黑发 → cascade
            try:
                logger.info(f"[AdjustCharacter] B57: 同步重生 {char_id} fullbody（用新 portrait 作参考）")
                _fullbody_result = await _ref_manager.generate_character_reference(
                    character=updated_char,
                    project_style=_project_style,
                    image_generator=_image_gen,
                    ref_type="fullbody",
                    portrait_ref=_portrait_result["pil_image"],  # 传入新 portrait 确保 face 一致
                    aspect_ratio=project.aspect_ratio or "2:3",
                )
                if _fullbody_result.get("success") and _fullbody_result.get("pil_image"):
                    _fullbody_path = _os.path.join(_char_refs_dir, f"{char_id}_fullbody.png")
                    _fullbody_result["pil_image"].save(_fullbody_path)
                    # T21-NEW-4: fullbody_url 也加 cache-buster (复用同一 epoch _v_ts)
                    _fullbody_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_fullbody.png?v={_v_ts}"
                    logger.info(f"[AdjustCharacter] T21-NEW-4 B57: ✅ {char_id} fullbody 已重生成 → {_fullbody_path} (cache-buster v={_v_ts})")
                    # 更新 chapter.characters_json 中的 fullbody_url (带 ?v=)
                    if chapter and chapter.characters_json:
                        try:
                            chars_list = json.loads(chapter.characters_json)
                            if char_index < len(chars_list):
                                chars_list[char_index]["fullbody_url"] = _fullbody_url
                                chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
                                db.add(chapter)
                                await db.commit()
                        except (json.JSONDecodeError, IndexError):
                            pass
                else:
                    logger.warning(
                        f"[AdjustCharacter] B57: ⚠️ {char_id} fullbody 重生成失败（非阻塞）: "
                        f"{_fullbody_result.get('error', '未知错误')}"
                    )
            except Exception as _fb_e:
                logger.warning(f"[AdjustCharacter] B57: fullbody 重生成异常（非阻塞）: {_fb_e}")
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
    # T21-NEW-4 (2026-05-21): cache-buster ?v={epoch} 防浏览器 cache 旧 404
    # 镜像 Shot regenerate L2315 模式
    import time as _time
    _v_ts = int(_time.time())
    portrait_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_portrait.png?v={_v_ts}"
    logger.info(f"[RegeneratePortrait] T21-NEW-4 ✅ {char_id} → {_portrait_path} (cache-buster v={_v_ts})")

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

    # B57 fix: portrait 重生成后必须同步重生 fullbody（用新 portrait 作参考保证角色一致性）
    # 原因: Stage 5 shot 用 fullbody 作参考。若 portrait 换了红发但 fullbody 还是黑发 → cascade 黑发 shot
    fullbody_url: str | None = None
    try:
        logger.info(f"[RegeneratePortrait] B57: 开始同步重生 {char_id} fullbody（用新 portrait 作参考）")
        _portrait_pil = _portrait_result["pil_image"]  # 刚生成的新 portrait

        _fullbody_result = await _ref_manager.generate_character_reference(
            character=target_char,
            project_style=_project_style,
            image_generator=_image_gen,
            ref_type="fullbody",
            portrait_ref=_portrait_pil,  # 传入新 portrait 确保 fullbody face 一致
            aspect_ratio=project.aspect_ratio or "2:3",
        )
        if _fullbody_result.get("success") and _fullbody_result.get("pil_image"):
            _fullbody_path = os.path.join(_char_refs_dir, f"{char_id}_fullbody.png")
            _fullbody_result["pil_image"].save(_fullbody_path)
            # T21-NEW-4: fullbody_url 也加 cache-buster (复用同一 _v_ts epoch)
            fullbody_url = f"/static/outputs/{project.uuid}/character_refs/{char_id}_fullbody.png?v={_v_ts}"
            logger.info(f"[RegeneratePortrait] T21-NEW-4 B57: ✅ {char_id} fullbody 已重生成 → {_fullbody_path} (cache-buster v={_v_ts})")

            # 更新 chapter.characters_json 的 fullbody_url + updated_at
            if chapter and chapter.characters_json:
                try:
                    chars_list = json.loads(chapter.characters_json)
                    if char_index < len(chars_list):
                        chars_list[char_index]["fullbody_url"] = fullbody_url
                        chars_list[char_index]["updated_at"] = _now_iso
                        chapter.characters_json = json.dumps(chars_list, ensure_ascii=False)
                        db.add(chapter)
                except (json.JSONDecodeError, IndexError):
                    pass

            # 同步更新 outline 中的 fullbody_url
            target_char["fullbody_url"] = fullbody_url
            characters_overview[char_index] = target_char
            outline["characters_overview"] = characters_overview
            if project.confirmed_outline_json:
                project.confirmed_outline_json = json.dumps(outline, ensure_ascii=False)
            else:
                project.raw_outline_json = json.dumps(outline, ensure_ascii=False)
            db.add(project)
            await db.commit()
        else:
            logger.warning(
                f"[RegeneratePortrait] B57: ⚠️ {char_id} fullbody 重生成失败（非阻塞）: "
                f"{_fullbody_result.get('error', '未知错误')}"
            )
    except Exception as _fb_e:
        logger.warning(f"[RegeneratePortrait] B57: fullbody 重生成异常（非阻塞）: {_fb_e}")

    return {
        "success": True,
        "char_id": char_id,
        "portrait_url": portrait_url,
        "fullbody_url": fullbody_url,
        "message": "肖像和全身图已重新生成" if fullbody_url else "肖像已重新生成（全身图更新失败）",
    }


# ---------------------------------------------------------------------------
# RISK-T18-E: /preview endpoint — 聚合项目预览数据（Wave 11.2, 2026-05-14）
# ---------------------------------------------------------------------------

@router.get("/{project_id}/preview")
async def get_project_preview(
    project_id: str,
    user_id: int = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """RISK-T18-E fix: 聚合项目预览数据，供预览页面 / 外部消费者使用。

    返回:
        project_id: str
        title: str
        style: str | None
        aspect_ratio: str | None
        bgm_url: str | None
        chapters: list[dict]  — 每章含 status + shots list + characters
        total_shots: int
        status: str  — 最新 chapter 的 status（"pending" / "generating_story" / "completed" / "failed"）

    设计原则:
    - 永远返回 200，不因数据未就绪而 404（同 T18-G 思路）
    - chapters=[] / total_shots=0 表示数据尚未就绪（不是错误）
    - frontend /preview 页面实际走 chapters/1/storyboard + chapters/1/story，
      本 endpoint 为外部消费者 / API completeness 设计
    """
    try:
        # 验证项目归属
        result = await db.execute(
            select(Project).where(Project.uuid == project_id, Project.user_id == user_id)
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 获取所有 chapter（通常只有 1 个）
        ch_result = await db.execute(
            select(Chapter)
            .where(Chapter.project_id == project.id)
            .order_by(Chapter.chapter_number)
        )
        chapters_db = ch_result.scalars().all()

        # 聚合 chapters 预览数据
        chapters_preview = []
        total_shots = 0
        latest_status = "pending"

        for chapter in chapters_db:
            latest_status = chapter.status or "pending"

            # 解析 storyboard shots
            shots: list[dict] = []
            if chapter.storyboard_json:
                try:
                    storyboard = json.loads(chapter.storyboard_json)
                    for shot in storyboard.get("shots", []):
                        if shot.get("deleted"):
                            continue
                        shot_id = shot.get("shot_id", 0)
                        shots.append({
                            "shot_id": shot_id,
                            "image_url": shot.get(
                                "image_url",
                                f"/static/outputs/{project_id}/images/shot_{shot_id:02d}.png"
                            ),
                            "narration": shot.get("narration_segment", ""),
                            "success": shot.get("success", True),
                        })
                    total_shots += len(shots)
                except (json.JSONDecodeError, Exception):
                    pass

            # 解析 characters（只含 id / name / portrait_url）
            characters: list[dict] = []
            if chapter.characters_json:
                try:
                    chars_raw = json.loads(chapter.characters_json)
                    for c in chars_raw:
                        char_id = c.get("id", "")
                        characters.append({
                            "id": char_id,
                            "name": c.get("name", ""),
                            "portrait_url": c.get(
                                "portrait_url",
                                f"/static/outputs/{project_id}/character_refs/{char_id}_portrait.png"
                                if char_id else None
                            ),
                        })
                except (json.JSONDecodeError, Exception):
                    pass

            chapters_preview.append({
                "chapter_number": chapter.chapter_number,
                "status": chapter.status or "pending",
                "shots": shots,
                "characters": characters,
                "bgm_url": chapter.bgm_url,
                "total_shots": len(shots),
            })

        # bgm_url: 取第一个 chapter 的 bgm_url
        bgm_url = chapters_db[0].bgm_url if chapters_db else None

        logger.info(
            f"[Preview] project={project_id} chapters={len(chapters_preview)} "
            f"total_shots={total_shots} status={latest_status}"
        )
        return {
            "project_id": project_id,
            "title": project.title or "",
            "style": project.style_preset,
            "aspect_ratio": project.aspect_ratio,
            "bgm_url": bgm_url,
            "status": latest_status,
            "chapters": chapters_preview,
            "total_shots": total_shots,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Preview] unhandled error project={project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"服务异常: {type(e).__name__}: {str(e)[:200]}"
        )


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
