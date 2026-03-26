"""文件上传存储服务 — 本地文件系统"""

import os
import uuid
from io import BytesIO
from PIL import Image


UPLOAD_BASE = os.path.join(os.path.dirname(__file__), "..", "..", "storage", "uploads")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSION = 2048
JPEG_QUALITY = 90


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def validate_image(contents: bytes, content_type: str | None) -> Image.Image:
    """验证图片类型、大小，返回 PIL Image"""
    if not content_type or content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("仅支持 JPEG / PNG / WebP 图片")
    if len(contents) > MAX_IMAGE_SIZE:
        raise ValueError("图片不能超过 10MB")
    try:
        img = Image.open(BytesIO(contents))
        img.verify()
        img = Image.open(BytesIO(contents))  # re-open after verify
        return img
    except Exception:
        raise ValueError("无法打开为有效图片")


def compress_image(img: Image.Image) -> bytes:
    """如果超过 2048px 等比缩小，保存为 JPEG"""
    w, h = img.size
    if max(w, h) > MAX_DIMENSION:
        ratio = MAX_DIMENSION / max(w, h)
        img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def save_upload(contents: bytes, category: str, project_id: str, ext: str = ".jpg") -> str:
    """保存上传文件，返回相对路径"""
    filename = f"{uuid.uuid4().hex}{ext}"
    rel_path = os.path.join(project_id, category, filename)
    abs_path = os.path.join(UPLOAD_BASE, rel_path)
    _ensure_dir(abs_path)
    with open(abs_path, "wb") as f:
        f.write(contents)
    return rel_path


def get_upload_abs_path(rel_path: str) -> str:
    """相对路径 → 绝对路径"""
    return os.path.join(UPLOAD_BASE, rel_path)


def delete_upload(rel_path: str) -> None:
    """删除上传文件"""
    abs_path = get_upload_abs_path(rel_path)
    if os.path.exists(abs_path):
        os.remove(abs_path)
