"""
Logo 资源优化：
1. D_v1 形态学膨胀加粗 + 精确二值化消除反锯齿色偏
2. D_v2 圆形 favicon
3. 全尺寸资源重新生成
"""

from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
HYBRID_DIR = PROJECT_ROOT / "test_output" / "manualtest" / "logo_concepts" / "D_hybrid"
COLORIZED_DIR = PROJECT_ROOT / "test_output" / "manualtest" / "logo_concepts" / "D_colorized"
OUT_DIR = PROJECT_ROOT / "frontend" / "public" / "brand"
COMPARE_DIR = PROJECT_ROOT / "test_output" / "manualtest" / "logo_concepts" / "D_refined"

# 品牌色
AMBER = (255, 149, 0)       # #FF9500
DARK = (18, 18, 18)         # #121212
WHITE = (255, 255, 255)


def dilate_and_colorize(src_path: Path, dilation_rounds: int, fg: tuple, bg: tuple) -> Image.Image:
    """
    1. 加载黑白原图
    2. 转灰度 → 二值化（消除反锯齿中间色）
    3. 形态学膨胀（加粗线条）
    4. 轻微高斯模糊恢复边缘平滑
    5. 精确上色
    """
    img = Image.open(src_path).convert("L")  # 灰度

    # 二值化：< 128 → 0 (前景黑), >= 128 → 255 (背景白)
    arr = np.array(img)
    binary = (arr < 128).astype(np.uint8) * 255  # 前景=255, 背景=0

    mask = Image.fromarray(binary, "L")

    # 形态学膨胀：MaxFilter 扩张白色区域（前景）
    for _ in range(dilation_rounds):
        mask = mask.filter(ImageFilter.MaxFilter(3))

    # 轻微高斯模糊让边缘平滑（不然会有锯齿）
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1.0))

    # 用 mask 作为混合权重上色
    mask_arr = np.array(mask, dtype=np.float32) / 255.0  # 0=bg, 1=fg

    result = np.zeros((*mask_arr.shape, 4), dtype=np.uint8)
    for c in range(3):
        result[:, :, c] = (mask_arr * fg[c] + (1 - mask_arr) * bg[c]).astype(np.uint8)
    result[:, :, 3] = 255

    return Image.fromarray(result, "RGBA")


def make_circular_icon(src_path: Path, fg: tuple, bg: tuple, size: int) -> Image.Image:
    """从 D_v2 生成圆形 favicon：圆形深色背景 + logo + 透明角落"""
    # 加载并上色
    img = Image.open(src_path).convert("L")
    arr = np.array(img, dtype=np.float32)

    # 二值化
    binary = (arr < 128).astype(np.float32)

    # 上色到 RGBA（先做全尺寸再缩放）
    colored = np.zeros((*binary.shape, 4), dtype=np.uint8)
    for c in range(3):
        colored[:, :, c] = (binary * fg[c] + (1 - binary) * bg[c]).astype(np.uint8)
    colored[:, :, 3] = 255
    colored_img = Image.fromarray(colored, "RGBA")

    # 创建圆形蒙版（在原始大小上）
    w, h = colored_img.size
    circle_mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(circle_mask)
    # 留一点边距（5%）
    margin = int(w * 0.02)
    draw.ellipse([margin, margin, w - margin, h - margin], fill=255)
    # 平滑边缘
    circle_mask = circle_mask.filter(ImageFilter.GaussianBlur(radius=2))

    # 应用圆形蒙版
    result = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    result.paste(colored_img, mask=circle_mask)

    # 缩放到目标尺寸
    result = result.resize((size, size), Image.LANCZOS)
    return result


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    COMPARE_DIR.mkdir(parents=True, exist_ok=True)

    src_v1 = HYBRID_DIR / "D_hybrid_v1.png"
    src_v2 = HYBRID_DIR / "D_hybrid_v2.png"

    print("=" * 55)
    print("Logo 资源优化")
    print("=" * 55)

    # ──────────────────────────────────────────
    # Step 1: D_v1 膨胀对比（试不同轮数找最佳）
    # ──────────────────────────────────────────
    print("\n📐 Step 1: D_v1 膨胀对比")
    for rounds in [1, 2, 3]:
        result = dilate_and_colorize(src_v1, rounds, AMBER, DARK)
        path = COMPARE_DIR / f"D_v1_dilate{rounds}_amber.png"
        result.save(str(path), "PNG")
        print(f"  ✅ 膨胀 {rounds} 轮 → {path.name}")

    # 同时保存原版（0 轮膨胀）作为对照
    result_0 = dilate_and_colorize(src_v1, 0, AMBER, DARK)
    (COMPARE_DIR / "D_v1_dilate0_amber.png").unlink(missing_ok=True)
    result_0.save(str(COMPARE_DIR / "D_v1_dilate0_amber.png"), "PNG")
    print(f"  ✅ 原版（0 轮）→ D_v1_dilate0_amber.png")

    # ──────────────────────────────────────────
    # Step 2: D_v2 圆形 favicon 对比
    # ──────────────────────────────────────────
    print("\n📐 Step 2: D_v2 圆形 favicon")
    for size in [32, 64, 128]:
        icon = make_circular_icon(src_v2, AMBER, DARK, size)
        path = COMPARE_DIR / f"D_v2_circular_{size}.png"
        icon.save(str(path), "PNG")
        print(f"  ✅ 圆形 {size}px → {path.name}")

    print(f"\n{'=' * 55}")
    print(f"对比图输出: {COMPARE_DIR}")
    print("请 Founder 审核后确定膨胀轮数，再生成最终资源")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
