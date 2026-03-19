"""
Logo 配色方案生成 — 纯 PIL 实现，无需 LLM
将黑白 logo 按网站配色体系上色
"""

from pathlib import Path
from PIL import Image
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / "test_output" / "manualtest" / "logo_concepts" / "D_hybrid"
OUTPUT_DIR = PROJECT_ROOT / "test_output" / "manualtest" / "logo_concepts" / "D_colorized"

# 网站配色体系
COLOR_SCHEMES = {
    "amber_on_dark": {
        "label": "品牌琥珀 on 深黑（主方案）",
        "fg": (255, 149, 0),      # #FF9500 品牌主色
        "bg": (18, 18, 18),       # #121212 主背景
    },
    "white_on_dark": {
        "label": "纯白 on 深黑（暗色模式）",
        "fg": (255, 255, 255),    # #FFFFFF
        "bg": (18, 18, 18),       # #121212
    },
    "amber_on_card": {
        "label": "浅琥珀 on 卡片灰（柔和变体）",
        "fg": (255, 179, 71),     # #FFB347 品牌次色
        "bg": (30, 30, 30),       # #1E1E1E 次背景
    },
}

# 要处理的源文件
SOURCE_LOGOS = ["D_hybrid_v1.png", "D_hybrid_v2.png"]


def colorize(src_path: Path, fg_color: tuple, bg_color: tuple) -> Image.Image:
    """将黑白 logo 重新上色：黑色→fg_color，白色→bg_color"""
    img = Image.open(src_path).convert("RGBA")
    data = np.array(img, dtype=np.float32)

    # 计算每个像素的亮度 (0=黑, 255=白)
    luminance = 0.299 * data[:, :, 0] + 0.587 * data[:, :, 1] + 0.114 * data[:, :, 2]

    # 归一化到 0-1（0=前景/黑, 1=背景/白）
    lum_norm = luminance / 255.0

    # 混合前景和背景色
    result = np.zeros_like(data)
    for c in range(3):
        result[:, :, c] = (1 - lum_norm) * fg_color[c] + lum_norm * bg_color[c]
    result[:, :, 3] = 255  # 完全不透明

    return Image.fromarray(result.astype(np.uint8), "RGBA")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 55)
    print("Logo 配色方案生成")
    print(f"源文件: {', '.join(SOURCE_LOGOS)}")
    print(f"配色: {len(COLOR_SCHEMES)} 种")
    print(f"总计: {len(SOURCE_LOGOS) * len(COLOR_SCHEMES)} 张")
    print("=" * 55)

    count = 0
    for logo_file in SOURCE_LOGOS:
        src = INPUT_DIR / logo_file
        if not src.exists():
            print(f"  ❌ 找不到 {src}")
            continue

        stem = src.stem  # e.g. "D_hybrid_v1"
        print(f"\n📐 {stem}")

        for scheme_key, scheme in COLOR_SCHEMES.items():
            output_name = f"{stem}_{scheme_key}.png"
            output_path = OUTPUT_DIR / output_name

            result = colorize(src, scheme["fg"], scheme["bg"])
            result.save(str(output_path), "PNG")

            fg_hex = "#{:02X}{:02X}{:02X}".format(*scheme["fg"])
            bg_hex = "#{:02X}{:02X}{:02X}".format(*scheme["bg"])
            print(f"  ✅ {output_name} — {scheme['label']} ({fg_hex} on {bg_hex})")
            count += 1

    print(f"\n{'=' * 55}")
    print(f"✅ 完成: {count} 张配色方案")
    print(f"📁 {OUTPUT_DIR}")
    print(f"{'=' * 55}")


if __name__ == "__main__":
    main()
