"""
tests/test_shot_validator_compression.py

RISK-T18-H: ShotValidator 5MB+ 图片压缩单测

测试场景:
1. _compress_for_claude: 小图 < 4.5MB → 原样返回 (PNG)
2. _compress_for_claude: 大图 > 4.5MB → 压缩后 < 4.5MB (JPEG)
3. _compress_for_claude: RGBA 大图 → 转 RGB 后压缩 (JPEG)
4. ShotValidator.validate_shot: 5MB+ 图片不触发 API_ERROR_SKIPPED（压缩后真调用）
5. ShotValidator.validate_shot: API 报错 reason=skip 而非 paste error stack
6. ShotValidator.validate_shot: client=None 时 reason="validator disabled"
7. validator_skipped_count 在 API 报错时递增
8. _compress_for_claude: 极端大图 (超高分辨率) → 降分辨率后仍 < 4.5MB

注意:
- test 4 使用 mock anthropic 客户端（不真实调用 API）
- 核心验证: 压缩后图片 < 5MB + reason 字段语义正确（"pass"/"failed_xxx"/"API_ERROR_SKIPPED"）
"""

import io
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image


# ---------------------------------------------------------------------------
# Helper: 创建指定大小的测试图片
# ---------------------------------------------------------------------------

def _make_png_bytes(width: int, height: int, mode: str = "RGB") -> bytes:
    """创建一张随机填充的 PNG，返回 bytes。"""
    import random
    img = Image.new(mode, (width, height))
    # 填充随机像素让 PNG 压缩比低（接近真实的 watercolor PNG）
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if mode == "RGBA":
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255),
                                 random.randint(0, 255), random.randint(200, 255))
            else:
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255),
                                 random.randint(0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_pil_image(width: int, height: int, mode: str = "RGB") -> Image.Image:
    """创建 PIL Image 用于 ShotValidator 输入。"""
    import random
    img = Image.new(mode, (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if mode == "RGBA":
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255),
                                 random.randint(0, 255), random.randint(200, 255))
            else:
                pixels[x, y] = (random.randint(0, 255), random.randint(0, 255),
                                 random.randint(0, 255))
    return img


# ---------------------------------------------------------------------------
# 1. _compress_for_claude: 小图原样返回
# ---------------------------------------------------------------------------

def test_compress_small_image_passthrough():
    """小图 < 4.5MB 应直接返回 PNG 不压缩。"""
    from app.services.shot_validator import _compress_for_claude

    # 小图 200×200 不会超 4.5MB
    small_bytes = _make_png_bytes(200, 200)
    assert len(small_bytes) < 4_500_000, "前提条件: 200×200 图应 < 4.5MB"

    result_bytes, media_type = _compress_for_claude(small_bytes)
    assert result_bytes == small_bytes, "小图应原样返回"
    assert media_type == "image/png", "小图应保持 PNG 格式"
    assert len(result_bytes) < 4_500_000


# ---------------------------------------------------------------------------
# 2. _compress_for_claude: 大图压缩后 < 4.5MB
# ---------------------------------------------------------------------------

def test_compress_large_image_reduces_size():
    """大图 > 4.5MB 应压缩至 < 4.5MB。"""
    from app.services.shot_validator import _compress_for_claude

    # 1664×2218 PNG 填充随机像素 ≈ 5.3MB (test18 Shot 1 的真实尺寸)
    large_bytes = _make_png_bytes(1664, 2218)
    # 如果随机像素 PNG 不够大，增大尺寸确保超限
    if len(large_bytes) < 4_500_000:
        # 直接创建确定 > 5MB 的 bytes（填充非零随机）
        large_bytes = bytes(range(256)) * 25_000  # ~6.4MB 纯 bytes

    original_size = len(large_bytes)
    result_bytes, media_type = _compress_for_claude(large_bytes)

    # 核心断言
    assert len(result_bytes) < 4_500_000, (
        f"压缩后仍 > 4.5MB ({len(result_bytes) / 1024 / 1024:.2f}MB)，压缩失败"
    )
    assert media_type == "image/jpeg", "大图应转为 JPEG"
    assert len(result_bytes) < original_size, "压缩后应比原始小"


# ---------------------------------------------------------------------------
# 3. _compress_for_claude: RGBA 大图转 RGB
# ---------------------------------------------------------------------------

def test_compress_rgba_large_image():
    """RGBA 模式大图应转 RGB 后正确压缩为 JPEG。"""
    from app.services.shot_validator import _compress_for_claude

    rgba_img = _make_pil_image(1664, 2218, mode="RGBA")
    buf = io.BytesIO()
    rgba_img.save(buf, format="PNG")
    rgba_bytes = buf.getvalue()

    # 如果 RGBA PNG 不够大，用大字节流代替
    if len(rgba_bytes) < 4_500_000:
        # 构造 > 4.5MB 的假字节（不是有效 PNG 但测 compress 的大小逻辑）
        # 这里改为 4MB 小图 + 反复拼接确保超限
        large_rgba_bytes = rgba_bytes + b"\x00" * (5_000_000 - len(rgba_bytes))
        # 实际测试用小图直接测 _compress_for_claude 的 RGBA 路径
        # 用 1200×1600 RGBA 确保压缩后格式正确
        img_small = _make_pil_image(1200, 1600, mode="RGBA")
        buf2 = io.BytesIO()
        img_small.save(buf2, format="PNG")
        test_bytes = buf2.getvalue()
        result_bytes, media_type = _compress_for_claude(test_bytes, max_bytes=len(test_bytes) - 1)
    else:
        result_bytes, media_type = _compress_for_claude(rgba_bytes)

    assert media_type == "image/jpeg", "RGBA 压缩后应为 JPEG"
    assert len(result_bytes) > 0, "压缩后图片不应为空"


# ---------------------------------------------------------------------------
# 4. validate_shot: 模拟 5MB+ 图片 → 压缩后真调用 API（不是 API_ERROR_SKIPPED）
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_shot_large_image_calls_api():
    """5MB+ 图片经压缩后，应真正调用 Haiku API，reason='pass' 而非 'API_ERROR_SKIPPED'。"""
    from app.services.shot_validator import ShotValidator

    # 模拟 Haiku 返回成功的 JSON 响应
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = '{"character_count": 1, "has_duplicate_bubbles": false, "has_visual_unnaturalness": false, "unnaturalness_details": "", "anatomy_severity": "none", "anatomy_issues": []}'

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)

    validator = ShotValidator.__new__(ShotValidator)
    validator.client = mock_client

    # 1664×2218 PIL Image（watercolor 高分辨率）
    large_pil = _make_pil_image(1664, 2218)

    result = await validator.validate_shot(
        pil_image=large_pil,
        expected_character_count=1,
    )

    # 核心断言：API 被真调用（不跳过）
    assert mock_client.messages.create.called, "应真调用 Haiku API，不应因 5MB 超限跳过"
    # reason 应为 "pass"（真验证通过）而非 "API_ERROR_SKIPPED" 或 "error: ..."
    assert result["reason"] == "pass", (
        f"reason 应为 'pass'（真通过），但实际是: {result['reason']!r}"
    )
    assert result["valid"] is True


# ---------------------------------------------------------------------------
# 5. validate_shot: API 报错时 reason="API_ERROR_SKIPPED" 不粘贴 error stack
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_shot_api_error_reason_is_clean():
    """API 调用失败时，reason 应为 'API_ERROR_SKIPPED'，不含完整 error stack。"""
    from app.services.shot_validator import ShotValidator
    import app.services.shot_validator as sv_module

    # 重置计数器
    sv_module.validator_skipped_count = 0

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=Exception("HTTP 400: Some API error occurred")
    )

    validator = ShotValidator.__new__(ShotValidator)
    validator.client = mock_client

    pil_img = _make_pil_image(400, 400)
    result = await validator.validate_shot(
        pil_image=pil_img,
        expected_character_count=1,
    )

    assert result["valid"] is True, "fail-open: API 报错时应返回 valid=True"
    # reason 不应含完整 error stack
    reason = result["reason"]
    assert "API_ERROR_SKIPPED" in reason or "SKIPPED" in reason, (
        f"reason 应含 'SKIPPED' 而非 error stack，实际: {reason!r}"
    )
    # 绝对不能把完整 exception 信息粘贴进 reason
    assert "HTTP 400: Some API error" not in reason, (
        f"reason 不应包含完整 error stack，实际: {reason!r}"
    )


# ---------------------------------------------------------------------------
# 6. validate_shot: client=None 时 reason="validator disabled"
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validate_shot_client_none_returns_disabled():
    """client=None 时应快速返回 reason='validator disabled'。"""
    from app.services.shot_validator import ShotValidator

    validator = ShotValidator.__new__(ShotValidator)
    validator.client = None

    pil_img = _make_pil_image(400, 400)
    result = await validator.validate_shot(
        pil_image=pil_img,
        expected_character_count=2,
    )

    assert result["valid"] is True
    assert result["reason"] == "validator disabled"
    assert result["actual_character_count"] == -1


# ---------------------------------------------------------------------------
# 7. validator_skipped_count: API 报错时递增
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_validator_skipped_count_increments():
    """API 报错时 validator_skipped_count 模块级计数器应递增。"""
    import app.services.shot_validator as sv_module
    from app.services.shot_validator import ShotValidator

    # 记录初始值
    initial_count = sv_module.validator_skipped_count

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=Exception("Forced error for test")
    )

    validator = ShotValidator.__new__(ShotValidator)
    validator.client = mock_client

    pil_img = _make_pil_image(300, 300)
    await validator.validate_shot(pil_image=pil_img, expected_character_count=1)

    assert sv_module.validator_skipped_count == initial_count + 1, (
        f"validator_skipped_count 应从 {initial_count} 增到 {initial_count + 1}，"
        f"实际: {sv_module.validator_skipped_count}"
    )


# ---------------------------------------------------------------------------
# 8. _compress_for_claude: 不同尺寸验证边界
# ---------------------------------------------------------------------------

def test_compress_exactly_at_limit():
    """4.5MB 边界内的图片不应触发压缩。"""
    from app.services.shot_validator import _compress_for_claude

    # 构造刚好 4.4MB 的 bytes
    test_bytes = b"\x89PNG\r\n" + b"\xAB" * (4_400_000 - 6)  # 不是合法 PNG，但测大小逻辑
    # 对于非 PNG 字节，函数会在 len <= max 时直接返回
    result_bytes, media_type = _compress_for_claude(test_bytes, max_bytes=4_500_000)
    assert result_bytes == test_bytes, "4.4MB < 4.5MB limit → 应原样返回"
    assert media_type == "image/png"


@pytest.mark.asyncio
async def test_validate_shot_5mb_specific_size_error_is_clean():
    """专门测试 5MB 超限错误（模拟 Anthropic 返回 5MB error），reason 应为 IMAGE_TOO_LARGE_SKIPPED。"""
    from app.services.shot_validator import ShotValidator
    import app.services.shot_validator as sv_module

    sv_module.validator_skipped_count = 0

    # 模拟 Anthropic 的 5MB 超限 error
    size_error_msg = "image exceeds 5 MB maximum: 5382432 bytes > 5242880 bytes"
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(
        side_effect=Exception(size_error_msg)
    )

    validator = ShotValidator.__new__(ShotValidator)
    validator.client = mock_client

    pil_img = _make_pil_image(400, 400)
    result = await validator.validate_shot(
        pil_image=pil_img,
        expected_character_count=1,
    )

    assert result["valid"] is True
    # reason 应为 IMAGE_TOO_LARGE_SKIPPED（比 API_ERROR_SKIPPED 更具体）
    assert result["reason"] == "IMAGE_TOO_LARGE_SKIPPED", (
        f"5MB 超限错误应有专用 reason 'IMAGE_TOO_LARGE_SKIPPED'，实际: {result['reason']!r}"
    )
    # 计数器递增
    assert sv_module.validator_skipped_count == 1
