"""音频存储服务"""

import os
import json
from typing import Optional
from datetime import datetime

from app.config import settings


class AudioStorageService:
    """
    音频存储服务

    存储结构：
    storage/
    └── audio/
        └── {project_id}/
            └── {chapter_id}/
                ├── narration.mp3           # 旁白音频
                ├── narration_meta.json     # 元数据（时长、转录等）
                └── timeline.json           # 时间轴映射
    """

    def __init__(self, base_path: str = None):
        self.base_path = base_path or settings.AUDIO_STORAGE_PATH
        os.makedirs(self.base_path, exist_ok=True)

    def _get_chapter_dir(self, project_id: str, chapter_id: str) -> str:
        """获取章节音频目录"""
        return os.path.join(self.base_path, project_id, chapter_id)

    async def save_audio(
        self,
        audio_data: bytes,
        project_id: str,
        chapter_id: str,
        audio_format: str = "mp3",
        filename: str = "narration"
    ) -> dict:
        """
        保存音频文件

        Args:
            audio_data: 音频二进制数据
            project_id: 项目ID
            chapter_id: 章节ID
            audio_format: 音频格式
            filename: 文件名（不含扩展名）

        Returns:
            {
                "audio_path": "相对路径",
                "full_path": "绝对路径",
                "format": "mp3",
                "file_size_bytes": 12345
            }
        """
        # 创建目录
        dir_path = self._get_chapter_dir(project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)

        # 保存音频
        audio_filename = f"{filename}.{audio_format}"
        audio_full_path = os.path.join(dir_path, audio_filename)

        with open(audio_full_path, 'wb') as f:
            f.write(audio_data)

        # 计算相对路径
        relative_path = os.path.join(project_id, chapter_id, audio_filename)

        return {
            "audio_path": relative_path,
            "full_path": os.path.abspath(audio_full_path),
            "format": audio_format,
            "file_size_bytes": len(audio_data)
        }

    async def save_metadata(
        self,
        project_id: str,
        chapter_id: str,
        metadata: dict,
        filename: str = "narration_meta.json"
    ) -> str:
        """
        保存音频元数据

        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            metadata: 元数据字典
            filename: 文件名

        Returns:
            保存的文件路径
        """
        dir_path = self._get_chapter_dir(project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)

        file_path = os.path.join(dir_path, filename)

        # 添加时间戳
        metadata["saved_at"] = datetime.now().isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        return file_path

    async def save_timeline(
        self,
        project_id: str,
        chapter_id: str,
        timeline: list
    ) -> str:
        """
        保存时间轴映射

        Args:
            project_id: 项目ID
            chapter_id: 章节ID
            timeline: 时间轴列表

        Returns:
            保存的文件路径
        """
        return await self.save_metadata(
            project_id=project_id,
            chapter_id=chapter_id,
            metadata={"timeline": timeline},
            filename="timeline.json"
        )

    def get_audio_path(
        self,
        project_id: str,
        chapter_id: str,
        filename: str = "narration.mp3"
    ) -> str:
        """获取音频文件完整路径"""
        return os.path.join(
            self.base_path,
            project_id,
            chapter_id,
            filename
        )

    def audio_exists(
        self,
        project_id: str,
        chapter_id: str,
        filename: str = "narration.mp3"
    ) -> bool:
        """检查音频文件是否存在"""
        path = self.get_audio_path(project_id, chapter_id, filename)
        return os.path.exists(path)

    async def load_metadata(
        self,
        project_id: str,
        chapter_id: str,
        filename: str = "narration_meta.json"
    ) -> Optional[dict]:
        """加载音频元数据"""
        file_path = os.path.join(
            self._get_chapter_dir(project_id, chapter_id),
            filename
        )

        if not os.path.exists(file_path):
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def load_timeline(
        self,
        project_id: str,
        chapter_id: str
    ) -> Optional[list]:
        """加载时间轴映射"""
        data = await self.load_metadata(
            project_id=project_id,
            chapter_id=chapter_id,
            filename="timeline.json"
        )

        if data and "timeline" in data:
            return data["timeline"]
        return None

    async def delete_chapter_audio(
        self,
        project_id: str,
        chapter_id: str
    ) -> bool:
        """
        删除章节的所有音频文件

        Args:
            project_id: 项目ID
            chapter_id: 章节ID

        Returns:
            是否成功删除
        """
        import shutil

        dir_path = self._get_chapter_dir(project_id, chapter_id)

        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                return True
            except Exception:
                return False

        return True  # 目录不存在也算成功

    def get_audio_url(
        self,
        project_id: str,
        chapter_id: str,
        filename: str = "narration.mp3"
    ) -> str:
        """
        获取音频的访问URL

        Returns:
            /api/audio/{project_id}/{chapter_id}/{filename}
        """
        return f"/api/audio/{project_id}/{chapter_id}/{filename}"

    async def get_audio_info(
        self,
        project_id: str,
        chapter_id: str
    ) -> Optional[dict]:
        """
        获取章节音频的完整信息

        Returns:
            {
                "exists": True,
                "audio_url": "/api/audio/...",
                "file_size_bytes": 12345,
                "metadata": {...},
                "timeline": [...]
            }
        """
        audio_path = self.get_audio_path(project_id, chapter_id)

        if not os.path.exists(audio_path):
            return {"exists": False}

        # 获取文件信息
        file_size = os.path.getsize(audio_path)

        # 加载元数据和时间轴
        metadata = await self.load_metadata(project_id, chapter_id)
        timeline = await self.load_timeline(project_id, chapter_id)

        return {
            "exists": True,
            "audio_url": self.get_audio_url(project_id, chapter_id),
            "file_size_bytes": file_size,
            "metadata": metadata,
            "timeline": timeline
        }
