"""Image API endpoints"""

import os
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/images", tags=["images"])

# 图像存储根路径
IMAGE_BASE_PATH = settings.IMAGE_STORAGE_PATH


@router.get("/{project_id}/{chapter_id}/{filename}")
async def serve_image(
    project_id: str,
    chapter_id: str,
    filename: str
):
    """
    提供图像文件访问

    实际路径：storage/images/{project_id}/{chapter_id}/{filename}
    """
    # 构建完整路径
    image_path = os.path.join(IMAGE_BASE_PATH, project_id, chapter_id, filename)

    # 安全检查 - 防止路径遍历攻击
    abs_path = os.path.abspath(image_path)
    abs_base = os.path.abspath(IMAGE_BASE_PATH)
    if not abs_path.startswith(abs_base):
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image not found")

    # 确定内容类型
    content_type = "image/png"
    if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
        content_type = "image/jpeg"
    elif filename.lower().endswith(".webp"):
        content_type = "image/webp"

    return FileResponse(
        image_path,
        media_type=content_type,
        filename=filename
    )


@router.get("/{project_id}/characters/{filename}")
async def serve_character_reference(
    project_id: str,
    filename: str
):
    """
    提供角色参考图访问

    实际路径：storage/images/{project_id}/characters/{filename}
    """
    # 构建完整路径
    image_path = os.path.join(IMAGE_BASE_PATH, project_id, "characters", filename)

    # 安全检查
    abs_path = os.path.abspath(image_path)
    abs_base = os.path.abspath(IMAGE_BASE_PATH)
    if not abs_path.startswith(abs_base):
        raise HTTPException(status_code=403, detail="Access denied")

    # 检查文件是否存在
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Character reference not found")

    # 确定内容类型
    content_type = "image/png"
    if filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
        content_type = "image/jpeg"

    return FileResponse(
        image_path,
        media_type=content_type,
        filename=filename
    )
