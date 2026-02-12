"""Image storage service for managing generated images"""

import os
import uuid
import base64
from io import BytesIO
from typing import Optional
from PIL import Image


class ImageStorageService:
    """
    图像存储服务

    存储结构：
    storage/
    └── images/
        └── {project_id}/
            └── {chapter_id}/
                ├── scene_001.png
                ├── scene_001_thumb.png
                ├── character_xxx.png  # 角色参考图
                └── ...
    """

    def __init__(self, base_path: str = "./storage/images"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    async def save_image(
        self,
        image_data: str,  # base64 encoded
        project_id: str,
        chapter_id: str,
        scene_id: int,
        format: str = "png"
    ) -> dict:
        """
        保存场景图像到本地

        Args:
            image_data: base64编码的图像数据
            project_id: 项目ID
            chapter_id: 章节ID
            scene_id: 场景ID
            format: 图像格式 (png/jpg)

        Returns:
            {
                "image_path": "相对路径",
                "thumbnail_path": "缩略图路径",
                "full_path": "绝对路径",
                "width": 1920,
                "height": 1080
            }
        """
        # 创建目录
        dir_path = os.path.join(self.base_path, project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)

        # 解码base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        # 保存原图
        filename = f"scene_{scene_id:03d}.{format}"
        image_path = os.path.join(dir_path, filename)
        image.save(image_path, format.upper())

        # 生成缩略图
        thumb_filename = f"scene_{scene_id:03d}_thumb.{format}"
        thumb_path = os.path.join(dir_path, thumb_filename)
        thumb = image.copy()
        thumb.thumbnail((400, 400))
        thumb.save(thumb_path, format.upper())

        return {
            "image_path": os.path.relpath(image_path, self.base_path),
            "thumbnail_path": os.path.relpath(thumb_path, self.base_path),
            "full_path": os.path.abspath(image_path),
            "width": image.width,
            "height": image.height
        }

    async def save_character_reference(
        self,
        image_data: str,  # base64 encoded
        project_id: str,
        character_name: str,
        format: str = "png"
    ) -> dict:
        """
        保存角色参考图

        Args:
            image_data: base64编码的图像数据
            project_id: 项目ID
            character_name: 角色名称
            format: 图像格式

        Returns:
            {
                "image_path": "相对路径",
                "full_path": "绝对路径",
                "width": int,
                "height": int
            }
        """
        # 创建目录
        dir_path = os.path.join(self.base_path, project_id, "characters")
        os.makedirs(dir_path, exist_ok=True)

        # 解码base64
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        # 使用角色名生成安全的文件名
        safe_name = "".join(c if c.isalnum() else "_" for c in character_name)
        filename = f"char_{safe_name}.{format}"
        image_path = os.path.join(dir_path, filename)
        image.save(image_path, format.upper())

        return {
            "image_path": os.path.relpath(image_path, self.base_path),
            "full_path": os.path.abspath(image_path),
            "width": image.width,
            "height": image.height
        }

    async def save_image_from_pil(
        self,
        pil_image: Image.Image,
        project_id: str,
        chapter_id: str,
        scene_id: int,
        format: str = "png"
    ) -> dict:
        """
        直接从PIL Image对象保存图像

        Args:
            pil_image: PIL Image对象
            project_id: 项目ID
            chapter_id: 章节ID
            scene_id: 场景ID
            format: 图像格式

        Returns:
            同 save_image
        """
        # 创建目录
        dir_path = os.path.join(self.base_path, project_id, chapter_id)
        os.makedirs(dir_path, exist_ok=True)

        # 保存原图
        filename = f"scene_{scene_id:03d}.{format}"
        image_path = os.path.join(dir_path, filename)
        pil_image.save(image_path, format.upper())

        # 生成缩略图
        thumb_filename = f"scene_{scene_id:03d}_thumb.{format}"
        thumb_path = os.path.join(dir_path, thumb_filename)
        thumb = pil_image.copy()
        thumb.thumbnail((400, 400))
        thumb.save(thumb_path, format.upper())

        return {
            "image_path": os.path.relpath(image_path, self.base_path),
            "thumbnail_path": os.path.relpath(thumb_path, self.base_path),
            "full_path": os.path.abspath(image_path),
            "width": pil_image.width,
            "height": pil_image.height
        }

    def get_image_url(self, image_path: str) -> str:
        """
        获取图像访问URL

        当前：返回本地静态文件路径
        未来：返回OSS/CDN URL
        """
        return f"/api/images/{image_path}"

    def get_full_path(self, relative_path: str) -> str:
        """获取完整的文件系统路径"""
        return os.path.join(self.base_path, relative_path)

    def image_exists(self, relative_path: str) -> bool:
        """检查图像是否存在"""
        full_path = self.get_full_path(relative_path)
        return os.path.exists(full_path)

    async def load_image_as_pil(self, relative_path: str) -> Optional[Image.Image]:
        """加载图像为PIL对象（用于参考图）"""
        full_path = self.get_full_path(relative_path)
        if os.path.exists(full_path):
            return Image.open(full_path)
        return None

    async def load_image_as_base64(self, relative_path: str) -> Optional[str]:
        """加载图像为base64字符串"""
        full_path = self.get_full_path(relative_path)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        return None

    async def delete_image(self, relative_path: str) -> bool:
        """删除图像文件"""
        full_path = self.get_full_path(relative_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    async def list_chapter_images(self, project_id: str, chapter_id: str) -> list:
        """列出章节的所有图像"""
        dir_path = os.path.join(self.base_path, project_id, chapter_id)
        if not os.path.exists(dir_path):
            return []

        images = []
        for filename in os.listdir(dir_path):
            if filename.startswith("scene_") and not filename.endswith("_thumb.png"):
                scene_id = int(filename.split("_")[1].split(".")[0])
                images.append({
                    "scene_id": scene_id,
                    "filename": filename,
                    "path": os.path.join(project_id, chapter_id, filename)
                })

        return sorted(images, key=lambda x: x["scene_id"])
