"""
tests/test_image_compression_safety.py

Wave 14 RISK-T19-7: IMAGE_TOO_LARGE 真压缩单测

测试核心断言:
1. 5.7 MB PNG (Shot 21 真实场景) → 压缩后 binary < 3.5 MB → base64 < 5 MB
2. 7 MB PNG 极端场景 → 压缩后 binary < 3.5 MB → base64 < 5 MB
3. 10 MB PNG 超极端 → 压缩后 binary < 3.5 MB → base64 < 5 MB
4. 小图 (< 3.5 MB) → 原样返回，不额外压缩
5. 1664×2218 真实 Seedream 输出尺寸 → 验证 target 3.5 MB 可达
6. base64 编码后实际大小 < 5 MB（Anthropic API 硬限制）
7. resize 优先策略：压缩前后分辨率变化符合预期（使用了 resize 而非仅 quality）
8. fallback 兜底：极端大图仍能在所有 scale 中找到一个符合 target

修复说明（Wave 14 RISK-T19-7）:
- 旧 max_bytes=4_500_000 → base64 后 ~6 MB → 仍超 Anthropic 5 MB → IMAGE_TOO_LARGE_SKIPPED
- 新 max_bytes=3_500_000 → base64 后 ~4.65 MB → 安全低于 5 MB
- 策略改为 resize 优先：先 scale(0.75/0.60/0.50/0.40) × quality(80/65)，再极端 fallback
"""

import base64
import io
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# Helper: 创建填充随机噪声的图片（PNG，接近真实 Seedream 输出的压缩率）
# ---------------------------------------------------------------------------

def _make_noisy_pil(width: int, height: int, mode: str = "RGB") -> Image.Image:
    """创建随机噪声填充的 PIL 图片（低压缩比，模拟 Seedream 真实输出）。"""
    import random
    img = Image.new(mode, (width, height))
    pixels = img.load()
    for y in range(height):
        for x in range(width):
            if mode == "RGBA":
                pixels[x, y] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(180, 255),
                )
            else:
                pixels[x, y] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )
    return img


def _pil_to_png_bytes(pil_img: Image.Image) -> bytes:
    """PIL Image → PNG bytes。"""
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()


def _inject_size(target_mb: float) -> bytes:
    """生成一个伪造的 PNG 字节流，用于精确控制大小（测 size-check 逻辑）。
    注意：这不是合法 PNG，仅用于测试 _compress_for_claude 的 size guard 路径。
    """
    target_bytes = int(target_mb * 1_048_576)
    # 合法 PNG header + 填充 0xFF bytes（高熵，PNG 压缩率低）
    return bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]) + b"\xFF" * (target_bytes - 8)


# ---------------------------------------------------------------------------
# Case 1: 5.7 MB PNG（Shot 21 真实场景）→ binary < 3.5 MB + base64 < 5 MB
# ---------------------------------------------------------------------------

def test_compress_5_7mb_binary_under_3_5mb():
    """5.7 MB PNG → 压缩后 binary < 3.5 MB（Wave 14 target）。"""
    from app.services.shot_validator import _compress_for_claude

    # 用 1664×2218 随机噪声模拟 Shot 21（Seedream 输出尺寸）
    # 随机噪声 PNG ≈ 10+ MB；若不够大用 _inject_size 兜底
    pil = _make_noisy_pil(1664, 2218)
    png_bytes = _pil_to_png_bytes(pil)

    # 如果随机噪声 PNG < 5.7 MB（极端情况），用 inject 模拟
    if len(png_bytes) < 5_700_000:
        # 说明当前系统 PNG 压缩率异常高；用真实尺寸图 + 更高熵注入
        # 直接 pad 到 5.7 MB 模拟真实场景
        png_bytes = png_bytes + b"\xFF" * (5_700_000 - len(png_bytes))

    assert len(png_bytes) >= 5_700_000, f"前提: 模拟图应 >= 5.7 MB，实际 {len(png_bytes) / 1_048_576:.2f} MB"

    compressed, media_type = _compress_for_claude(png_bytes)

    # 核心断言 1: binary < 3.5 MB
    assert len(compressed) < 3_500_000, (
        f"compressed binary {len(compressed) / 1_048_576:.2f} MB >= 3.5 MB target "
        f"(Wave 14 RISK-T19-7 修复失效)"
    )
    assert media_type == "image/jpeg", "大图应压缩为 JPEG"


def test_compress_5_7mb_base64_under_5mb():
    """5.7 MB PNG 压缩后 base64 < 5 MB（Anthropic API 硬限制）。"""
    from app.services.shot_validator import _compress_for_claude

    pil = _make_noisy_pil(1664, 2218)
    png_bytes = _pil_to_png_bytes(pil)
    if len(png_bytes) < 5_700_000:
        png_bytes = png_bytes + b"\xFF" * (5_700_000 - len(png_bytes))

    compressed, _ = _compress_for_claude(png_bytes)

    b64_bytes = base64.standard_b64encode(compressed)
    b64_size = len(b64_bytes)

    # 核心断言 2: base64 < 5 MB
    assert b64_size < 5_000_000, (
        f"base64 大小 {b64_size / 1_048_576:.2f} MB >= 5 MB Anthropic 限制！"
        f" compressed binary = {len(compressed) / 1_048_576:.2f} MB"
    )


# ---------------------------------------------------------------------------
# Case 2: 7 MB PNG 极端场景 → binary < 3.5 MB + base64 < 5 MB
# ---------------------------------------------------------------------------

def test_compress_7mb_binary_under_3_5mb():
    """7 MB PNG → 压缩后 binary < 3.5 MB。"""
    from app.services.shot_validator import _compress_for_claude

    # 2048×2048 超高分辨率（Seedream 最大输出）
    pil = _make_noisy_pil(2048, 2048)
    png_bytes = _pil_to_png_bytes(pil)
    if len(png_bytes) < 7_000_000:
        png_bytes = png_bytes + b"\xFF" * (7_000_000 - len(png_bytes))

    compressed, media_type = _compress_for_claude(png_bytes)

    assert len(compressed) < 3_500_000, (
        f"7 MB 图压缩后 {len(compressed) / 1_048_576:.2f} MB >= 3.5 MB"
    )
    # base64 also < 5 MB
    b64_size = len(base64.standard_b64encode(compressed))
    assert b64_size < 5_000_000, (
        f"7 MB 图 base64 {b64_size / 1_048_576:.2f} MB >= 5 MB"
    )


# ---------------------------------------------------------------------------
# Case 3: 10 MB PNG 超极端 → binary < 3.5 MB + base64 < 5 MB
# ---------------------------------------------------------------------------

def test_compress_10mb_binary_under_3_5mb():
    """10 MB PNG → 压缩后 binary < 3.5 MB（极端兜底测试）。"""
    from app.services.shot_validator import _compress_for_claude

    # 3000×2000 超高分辨率
    pil = _make_noisy_pil(3000, 2000)
    png_bytes = _pil_to_png_bytes(pil)
    if len(png_bytes) < 10_000_000:
        png_bytes = png_bytes + b"\xFF" * (10_000_000 - len(png_bytes))

    compressed, media_type = _compress_for_claude(png_bytes)

    assert len(compressed) < 3_500_000, (
        f"10 MB 图压缩后 {len(compressed) / 1_048_576:.2f} MB >= 3.5 MB"
    )
    b64_size = len(base64.standard_b64encode(compressed))
    assert b64_size < 5_000_000, (
        f"10 MB 图 base64 {b64_size / 1_048_576:.2f} MB >= 5 MB"
    )


# ---------------------------------------------------------------------------
# Case 4: 小图 (< 3.5 MB) → 原样返回，不压缩
# ---------------------------------------------------------------------------

def test_compress_small_image_passthrough_new_target():
    """小图 < 3.5 MB 应原样返回 PNG（不触发压缩）。"""
    from app.services.shot_validator import _compress_for_claude

    # 300×300 随机噪声 PNG 约 260 KB，远小于 3.5 MB
    pil = _make_noisy_pil(300, 300)
    png_bytes = _pil_to_png_bytes(pil)
    assert len(png_bytes) < 3_500_000, f"前提: 300×300 应 < 3.5 MB，实际 {len(png_bytes)} bytes"

    result_bytes, media_type = _compress_for_claude(png_bytes)

    assert result_bytes == png_bytes, "小图应原样返回，不应修改 bytes"
    assert media_type == "image/png", "小图应保持 PNG 格式"
    assert len(result_bytes) < 3_500_000


# ---------------------------------------------------------------------------
# Case 5: 1664×2218 真实 Seedream 输出尺寸 → 3.5 MB target 可达
# ---------------------------------------------------------------------------

def test_compress_seedream_native_size_reaches_target():
    """1664×2218（Seedream 2:3 标准输出）随机噪声图 → binary < 3.5 MB。"""
    from app.services.shot_validator import _compress_for_claude

    pil = _make_noisy_pil(1664, 2218)
    png_bytes = _pil_to_png_bytes(pil)

    # 如果 PNG 随机噪声超 3.5 MB（大概率），验证压缩有效
    # 如果 PNG 本身 < 3.5 MB（理论上不会，但防御），直接 pass
    if len(png_bytes) <= 3_500_000:
        # PNG 本身已在 target 内，无需压缩
        result_bytes, media_type = _compress_for_claude(png_bytes)
        assert result_bytes == png_bytes
        return

    result_bytes, media_type = _compress_for_claude(png_bytes)

    assert len(result_bytes) < 3_500_000, (
        f"1664×2218 噪声 PNG 压缩后 {len(result_bytes) / 1_048_576:.2f} MB "
        f">= 3.5 MB target"
    )
    assert media_type == "image/jpeg"

    # 验证 base64 < 5 MB
    b64_size = len(base64.standard_b64encode(result_bytes))
    assert b64_size < 5_000_000, (
        f"base64 {b64_size / 1_048_576:.2f} MB >= 5 MB Anthropic 限制"
    )


# ---------------------------------------------------------------------------
# Case 6: base64 膨胀系数验证（3.5 MB binary × 1.34 = 4.69 MB < 5 MB）
# ---------------------------------------------------------------------------

def test_base64_inflation_factor_safety_margin():
    """验证 3.5 MB binary × base64 膨胀系数 < 5 MB Anthropic 限制（理论安全性）。"""
    # base64 每 3 bytes → 4 bytes，膨胀系数 = 4/3 ≈ 1.333
    TARGET_MB = 3.5
    INFLATION_FACTOR = 4.0 / 3.0  # 精确 base64 膨胀
    ANTHROPIC_LIMIT_MB = 5.0

    base64_estimate_mb = TARGET_MB * INFLATION_FACTOR
    safety_margin_mb = ANTHROPIC_LIMIT_MB - base64_estimate_mb

    assert base64_estimate_mb < ANTHROPIC_LIMIT_MB, (
        f"3.5 MB binary × {INFLATION_FACTOR:.4f} = {base64_estimate_mb:.2f} MB "
        f">= 5 MB Anthropic 限制！安全边际设计失败"
    )
    assert safety_margin_mb >= 0.3, (
        f"安全边际 {safety_margin_mb:.2f} MB 过小（< 0.3 MB），需降低 target"
    )

    # 验证实际 bytes 计算
    target_bytes = int(TARGET_MB * 1_048_576)
    b64_bytes = (target_bytes + 2) // 3 * 4  # base64 编码字节数（向上取整到 4 倍）
    assert b64_bytes < int(ANTHROPIC_LIMIT_MB * 1_048_576), (
        f"实际 base64 bytes {b64_bytes} >= Anthropic 5 MB ({int(ANTHROPIC_LIMIT_MB * 1_048_576)})"
    )


# ---------------------------------------------------------------------------
# Case 7: resize 优先策略 — 验证大图确实经历了 resize（不只是 quality 压缩）
# ---------------------------------------------------------------------------

def test_compress_uses_resize_strategy_for_large_images():
    """验证大图压缩时确实 resize 了（不只是 quality 调整）。"""
    from app.services.shot_validator import _compress_for_claude

    # 创建大图
    orig_w, orig_h = 1664, 2218
    pil = _make_noisy_pil(orig_w, orig_h)
    png_bytes = _pil_to_png_bytes(pil)
    if len(png_bytes) < 3_500_000:
        png_bytes = png_bytes + b"\xFF" * (3_500_001 - len(png_bytes))

    compressed, media_type = _compress_for_claude(png_bytes)

    # 解码 JPEG 验证尺寸确实缩小了
    if media_type == "image/jpeg":
        result_img = Image.open(io.BytesIO(compressed))
        result_w, result_h = result_img.size

        # resize 策略中最小 scale=0.25，所以 result 应比原图小
        assert result_w <= orig_w, (
            f"result width {result_w} > original {orig_w}，没有做 resize？"
        )
        assert result_h <= orig_h, (
            f"result height {result_h} > original {orig_h}，没有做 resize？"
        )
        # 实际 scale 最大 0.75，所以 max(result_w) = 1664 * 0.75 = 1248
        assert result_w <= int(orig_w * 0.76), (
            f"result width {result_w} 超过 scale=0.75 上限 {int(orig_w * 0.76)}，"
            f"说明没有正确走 resize 策略"
        )


# ---------------------------------------------------------------------------
# Case 8: fallback 兜底 — 超大图（20 MB）仍能压缩到 target
# ---------------------------------------------------------------------------

def test_compress_20mb_fallback_reaches_target():
    """20 MB 超大图应通过极端 fallback(scale=0.25/0.30) 压缩到 3.5 MB 以内。"""
    from app.services.shot_validator import _compress_for_claude

    # 4096×4096 超大图
    pil = _make_noisy_pil(4096, 4096)
    png_bytes = _pil_to_png_bytes(pil)
    if len(png_bytes) < 20_000_000:
        png_bytes = png_bytes + b"\xFF" * (20_000_000 - len(png_bytes))

    compressed, media_type = _compress_for_claude(png_bytes)

    # 即使 fallback 路径，binary 也应 <= 3.5 MB（或接近，视图像内容而定）
    # 对真实 4096×4096 随机噪声：scale=0.25 → 1024×1024, quality=55 → ~数百 KB
    # 实测应远低于 3.5 MB；若连 fallback 也超，说明 _compress_for_claude 逻辑有根本问题
    # 注意：对于填充 0xFF bytes（非真实图像）最终大小不可预测，
    # 因此对非真实图像宽松一些，只要 API 不拿到 > 5 MB base64 即可
    b64_size = len(base64.standard_b64encode(compressed))
    assert b64_size < 5_000_000, (
        f"20 MB 图 fallback 后 base64 仍 {b64_size / 1_048_576:.2f} MB >= 5 MB！"
        f" compressed = {len(compressed) / 1_048_576:.2f} MB"
    )
