"""Chapters API"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.project import Project
from app.models.chapter import Chapter
from app.models.job import GenerationJob
from app.models.scene_image import SceneImage
from app.schemas.chapter import ChapterStatus, ChapterStory, ChapterResponse
from app.api.projects import verify_user

router = APIRouter(prefix="/api/projects/{project_id}/chapters", tags=["chapters"])


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
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """List all chapters for a project"""
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    result = await db.execute(
        select(Chapter)
        .where(Chapter.project_id == project_id)
        .order_by(Chapter.chapter_number)
    )
    chapters = result.scalars().all()
    return [ChapterResponse.model_validate(c) for c in chapters]


@router.get("/{chapter_number}/status", response_model=ChapterStatus)
async def get_generation_status(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Query generation status (for frontend polling)
    """
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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
        return ChapterStatus(
            status=chapter.status,
            stage=None,
            progress=0,
            estimated_remaining_seconds=None,
            message="暂无生成任务",
        )

    return ChapterStatus(
        status=job.status,
        stage=job.current_stage,
        progress=job.progress,
        estimated_remaining_seconds=job.estimated_seconds,
        message=job.stage_message,
    )


@router.get("/{chapter_number}/story", response_model=ChapterStory)
async def get_chapter_story(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get generated story content
    """
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # Get chapter
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
        )
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    # Check if story is ready
    if chapter.status == "pending":
        raise HTTPException(status_code=400, detail="故事尚未开始生成")

    if chapter.status == "generating_story":
        raise HTTPException(status_code=400, detail="故事正在生成中，请稍候")

    if chapter.status == "failed":
        raise HTTPException(
            status_code=400,
            detail=f"故事生成失败: {chapter.error_message or '未知错误'}",
        )

    if not chapter.full_script:
        raise HTTPException(status_code=400, detail="故事内容不存在")

    # Parse stored JSON
    try:
        full_script = json.loads(chapter.full_script)
        scenes = json.loads(chapter.scenes_json) if chapter.scenes_json else []
        characters = (
            json.loads(chapter.characters_json) if chapter.characters_json else []
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"数据解析错误: {str(e)}")

    return ChapterStory(
        title=full_script.get("title", "未命名"),
        summary=chapter.summary or "",
        full_script=full_script,
        scenes=scenes,
        characters=characters,
    )


@router.get("/{chapter_number}", response_model=ChapterResponse)
async def get_chapter(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """Get basic chapter info"""
    # Verify project ownership
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
        )
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    return ChapterResponse.model_validate(chapter)


# ============ Phase 2: 图像生成端点 ============

@router.post("/{chapter_number}/generate-images", response_model=ImageGenerationResponse)
async def generate_chapter_images(
    project_id: str,
    chapter_number: int,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    为章节生成所有分镜图像

    前置条件：章节故事已生成完成
    """
    # 1. 验证项目所有权
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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
    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        chapter_id=chapter.id,
        status="queued",
        current_stage="image_generation",
        progress=0,
        stage_message="图像生成任务已创建，等待开始...",
        created_at=datetime.utcnow(),
    )
    db.add(job)

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
        job_id=job_id,
        status="generating_images",
        message="图像生成已开始",
        total_scenes=len(scenes)
    )


@router.get("/{chapter_number}/images", response_model=ChapterImagesResponse)
async def get_chapter_images(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节的所有分镜图像
    """
    # 1. 验证项目
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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


@router.post("/{chapter_number}/images/{scene_id}/regenerate")
async def regenerate_scene_image(
    project_id: str,
    chapter_number: int,
    scene_id: int,
    background_tasks: BackgroundTasks,
    request: RegenerateRequest = None,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    重新生成单个场景的图像

    用于用户对某张图不满意时重新生成
    """
    # 1. 验证项目
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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
    job_id: str,
    chapter_id: str,
    project_id: str,
    style_preset: str
):
    """
    图像生成后台任务
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
                    aspect_ratio=scene_board.get("aspect_ratio", "16:9"),
                    # reference_images=list(char_references.values()) if char_references else None,
                    style_preset=style_preset
                )

                # 保存结果
                scene_image_id = str(uuid.uuid4())

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
                        id=scene_image_id,
                        chapter_id=chapter_id,
                        scene_id=scene_board["scene_id"],
                        image_prompt=scene_board["image_prompt"],
                        style_prompt=scene_board.get("style_prompt", ""),
                        negative_prompt=scene_board.get("negative_prompt", ""),
                        image_path=saved["image_path"],
                        thumbnail_path=saved["thumbnail_path"],
                        width=saved["width"],
                        height=saved["height"],
                        aspect_ratio=scene_board.get("aspect_ratio", "16:9"),
                        generation_model=result.get("model_used", ""),
                        generation_time_seconds=int(result.get("generation_time_seconds", 0)),
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                else:
                    # 记录失败
                    scene_image = SceneImage(
                        id=scene_image_id,
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

        except Exception as e:
            print(f"Image generation error: {e}")
            if job:
                job.status = "failed"
                job.stage_message = f"图像生成失败: {str(e)}"
                await db.commit()

            chapter = await db.get(Chapter, chapter_id)
            if chapter:
                chapter.error_message = str(e)
                await db.commit()


async def regenerate_single_image_task(
    chapter_id: str,
    project_id: str,
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
                aspect_ratio = "16:9"
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
                aspect_ratio = scene_board.get("aspect_ratio", "16:9")

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
            scene_image_id = str(uuid.uuid4())

            if result["success"]:
                saved = await storage.save_image(
                    image_data=result["image_data"],
                    project_id=project_id,
                    chapter_id=chapter_id,
                    scene_id=scene_id
                )

                scene_image = SceneImage(
                    id=scene_image_id,
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
                    id=scene_image_id,
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

        except Exception as e:
            print(f"Regenerate image error: {e}")


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
    user_id: str = Depends(verify_user),
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
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    project = project_result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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
    job_id = str(uuid.uuid4())
    job = GenerationJob(
        id=job_id,
        chapter_id=chapter.id,
        status="queued",
        current_stage="audio_generation",
        progress=0,
        stage_message="音频生成任务已创建，等待开始...",
        created_at=datetime.utcnow(),
    )
    db.add(job)

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
        job_id=job_id,
        status="generating_audio",
        message="音频生成已开始"
    )


@router.get("/{chapter_number}/timeline", response_model=ChapterTimelineResponse)
async def get_chapter_timeline(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节的音画时间轴

    返回每个场景对应的时间段和图片
    """
    # 1. 验证项目
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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


@router.get("/{chapter_number}/audio")
async def get_chapter_audio_info(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取章节音频信息
    """
    # 1. 验证项目
    project_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if not project_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="项目不存在")

    # 2. 获取章节
    chapter_result = await db.execute(
        select(Chapter).where(
            Chapter.project_id == project_id, Chapter.chapter_number == chapter_number
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


@router.get("/{chapter_number}/voices")
async def get_available_voices(
    project_id: str,
    chapter_number: int,
    user_id: str = Depends(verify_user),
):
    """
    获取可用的音色列表
    """
    from app.services.tts_service import TTSService

    tts = TTSService()
    voices = tts.get_available_voices()

    return {
        "voices": voices,
        "default": "zh_female_shuangkuai"
    }


# ============ Phase 3 后台任务 ============

async def generate_audio_and_align_task(
    job_id: str,
    chapter_id: str,
    project_id: str,
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

        except Exception as e:
            print(f"Audio generation error: {e}")
            import traceback
            traceback.print_exc()

            if job:
                job.status = "failed"
                job.stage_message = f"音频生成失败: {str(e)}"
                await db.commit()

            chapter = await db.get(Chapter, chapter_id)
            if chapter:
                chapter.error_message = str(e)
                chapter.status = "failed"
                await db.commit()
