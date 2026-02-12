"""Audio serving API"""

import os
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/audio", tags=["audio"])


def sanitize_path_component(component: str) -> str:
    """
    清理路径组件，防止路径遍历攻击

    只允许字母、数字、下划线、横杠和点
    """
    # 移除任何可能的路径遍历尝试
    component = component.replace("..", "").replace("/", "").replace("\\", "")
    # 只保留安全字符
    return re.sub(r'[^a-zA-Z0-9_\-\.]', '', component)


@router.get("/{project_id}/{chapter_id}/{filename}")
async def serve_audio(
    project_id: str,
    chapter_id: str,
    filename: str
):
    """
    提供音频文件访问

    路径格式: /api/audio/{project_id}/{chapter_id}/{filename}
    示例: /api/audio/proj_xxx/chap_xxx/narration.mp3
    """
    # 安全检查：清理路径组件
    safe_project_id = sanitize_path_component(project_id)
    safe_chapter_id = sanitize_path_component(chapter_id)
    safe_filename = sanitize_path_component(filename)

    # 验证文件扩展名
    allowed_extensions = {'.mp3', '.wav', '.ogg', '.m4a'}
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式: {ext}"
        )

    # 构建文件路径
    audio_path = os.path.join(
        settings.AUDIO_STORAGE_PATH,
        safe_project_id,
        safe_chapter_id,
        safe_filename
    )

    # 转为绝对路径并验证
    audio_path = os.path.abspath(audio_path)
    base_path = os.path.abspath(settings.AUDIO_STORAGE_PATH)

    # 确保文件在允许的目录下
    if not audio_path.startswith(base_path):
        raise HTTPException(status_code=403, detail="禁止访问")

    # 检查文件是否存在
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    # 根据扩展名确定MIME类型
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4'
    }
    media_type = mime_types.get(ext, 'audio/mpeg')

    return FileResponse(
        audio_path,
        media_type=media_type,
        filename=safe_filename
    )


@router.head("/{project_id}/{chapter_id}/{filename}")
async def head_audio(
    project_id: str,
    chapter_id: str,
    filename: str
):
    """
    HEAD请求，用于检查音频是否存在和获取元信息

    支持音频播放器的预检请求
    """
    # 安全检查
    safe_project_id = sanitize_path_component(project_id)
    safe_chapter_id = sanitize_path_component(chapter_id)
    safe_filename = sanitize_path_component(filename)

    # 构建文件路径
    audio_path = os.path.join(
        settings.AUDIO_STORAGE_PATH,
        safe_project_id,
        safe_chapter_id,
        safe_filename
    )

    audio_path = os.path.abspath(audio_path)
    base_path = os.path.abspath(settings.AUDIO_STORAGE_PATH)

    if not audio_path.startswith(base_path):
        raise HTTPException(status_code=403, detail="禁止访问")

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="音频文件不存在")

    # 获取文件大小
    file_size = os.path.getsize(audio_path)

    # 返回带有Content-Length的响应
    from fastapi.responses import Response
    return Response(
        content=None,
        headers={
            "Content-Length": str(file_size),
            "Accept-Ranges": "bytes"
        }
    )
