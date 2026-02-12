"""
新故事V2文字叠加测试 - 古风武侠《剑心》
从无文字图读取overlay_config，应用V2文字叠加

作者: @Tester
日期: 2026-01-22
"""

import json
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
from app.services.text_overlay_service import (
    TextOverlayService,
    strip_speaker_prefix,
    get_bubble_position_for_index,
    detect_overlay_collision,
)

# =============================================================================
# 配置
# =============================================================================

INPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "new_story_test"
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "new_story_overlay_v2"

# =============================================================================
# V2 增强配置
# =============================================================================

DEFAULT_FONT_SIZE = 42        # V1: 28, V2: +50%
SPEECH_BUBBLE_FONT_SIZE = 36  # V1: 24, V2: +50%
EMPHASIS_FONT_SIZE = 52       # 强调文字 +25%
EMPHASIS_COLOR = "#FF4444"    # 红色强调

# 尝试的字体路径
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """获取支持中文的字体"""
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()


# =============================================================================
# V2 情感强调分析 (简化规则版)
# =============================================================================

@dataclass
class TextSegment:
    text: str
    emphasis_type: Optional[str] = None  # None, "red_large"


@dataclass
class TextEmphasis:
    segments: List[TextSegment]
    has_emphasis: bool


def analyze_text_emphasis_simple(text: str) -> TextEmphasis:
    """
    V2简化版情感强调分析
    规则驱动：检测 "!!!" 或 "！！！" 触发红色放大
    """
    # 检测强调标记
    emphasis_markers = ["!!!", "！！！", "!!", "！！"]

    for marker in emphasis_markers:
        if marker in text:
            # 找到包含marker的部分
            parts = text.split(marker)
            segments = []

            for i, part in enumerate(parts):
                if part:
                    segments.append(TextSegment(text=part, emphasis_type=None))
                if i < len(parts) - 1:
                    # 找到marker前的词组作为强调
                    if segments and segments[-1].emphasis_type is None:
                        # 将最后一个segment标记为强调
                        last_text = segments[-1].text
                        # 提取最后一个短语（逗号或句号分隔）
                        for sep in ['，', '。', ',', '.', ' ']:
                            if sep in last_text:
                                prefix, phrase = last_text.rsplit(sep, 1)
                                if phrase:
                                    segments[-1] = TextSegment(text=prefix + sep if prefix else "", emphasis_type=None)
                                    segments.append(TextSegment(text=phrase + marker, emphasis_type="red_large"))
                                    break
                        else:
                            # 整句标记为强调
                            segments[-1] = TextSegment(text=last_text + marker, emphasis_type="red_large")

            if any(s.emphasis_type for s in segments):
                return TextEmphasis(segments=segments, has_emphasis=True)

    # 无强调
    return TextEmphasis(
        segments=[TextSegment(text=text, emphasis_type=None)],
        has_emphasis=False
    )


# =============================================================================
# 测试适配函数 (使用主服务的 TextOverlayService)
# =============================================================================

def add_top_monologue(service: TextOverlayService, image: Image.Image, text: str) -> Image.Image:
    """添加顶部黑底旁白"""
    return service.add_monologue(image, text, position="top", height_ratio=0.12, enable_emphasis=True)


def add_bottom_monologue(service: TextOverlayService, image: Image.Image, text: str) -> Image.Image:
    """添加底部黑底旁白"""
    return service.add_monologue(image, text, position="bottom", height_ratio=0.10)


def add_center_monologue(service: TextOverlayService, image: Image.Image, text: str) -> Image.Image:
    """添加中央黑底旁白"""
    return service.add_monologue(image, text, position="center", height_ratio=0.15)


def add_top_narrative(service: TextOverlayService, image: Image.Image, text: str) -> Image.Image:
    """添加顶部白底叙事旁白"""
    return service.add_narrative(image, text, position="top", height_ratio=0.12)


def add_speech_bubble_v2(service: TextOverlayService, image: Image.Image, text: str,
                         speaker_position: str = "right",
                         speaker_vertical: str = "upper") -> Image.Image:
    """添加对话气泡"""
    # 转换 speaker_position 到 bubble_x_percent
    if speaker_position == "left":
        x_pct = 25
    elif speaker_position == "center":
        x_pct = 50
    else:  # right
        x_pct = 75

    # 转换 speaker_vertical 到 bubble_y_percent
    if speaker_vertical == "upper":
        y_pct = 15
    elif speaker_vertical == "middle":
        y_pct = 40
    else:  # lower
        y_pct = 70

    return service.add_speech_bubble(image, text, bubble_x_percent=x_pct, bubble_y_percent=y_pct)


# =============================================================================
# 创建对比图
# =============================================================================

def create_comparison(original: Image.Image, processed: Image.Image, shot_name: str) -> Image.Image:
    """创建左右对比图"""
    width, height = original.size

    # 创建新图
    comparison = Image.new('RGB', (width * 2 + 20, height + 80), color='white')

    # 粘贴原图和处理后的图
    comparison.paste(original, (0, 50))
    comparison.paste(processed, (width + 20, 50))

    # 添加标签
    draw = ImageDraw.Draw(comparison)
    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 24)
    except:
        label_font = ImageFont.load_default()

    draw.text((width // 2 - 60, 10), "无文字原图", font=label_font, fill="black")
    draw.text((width + 20 + width // 2 - 60, 10), "V2叠加后", font=label_font, fill="black")
    draw.text((width, height + 55), shot_name, font=label_font, fill="gray")

    return comparison


# =============================================================================
# 主测试流程
# =============================================================================

def run_v2_overlay_test():
    """运行V2文字叠加测试"""

    print("=" * 60)
    print("新故事V2文字叠加测试 - 古风武侠《剑心》")
    print("增强: 字体+50%, 动态气泡, 情感强调")
    print("=" * 60)

    # 检查输入目录
    if not INPUT_DIR.exists():
        print(f"\n❌ 错误: 输入目录不存在: {INPUT_DIR}")
        print("请先运行: python tests/test_new_story_no_text.py")
        return

    # 读取prompts_log获取overlay配置
    prompts_log_path = INPUT_DIR / "prompts_log.json"
    if not prompts_log_path.exists():
        print(f"\n❌ 错误: prompts_log.json 不存在")
        return

    with open(prompts_log_path, 'r', encoding='utf-8') as f:
        prompts_log = json.load(f)

    print(f"\n输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 初始化服务（使用主服务）
    overlay_service = TextOverlayService()

    results = []

    for shot_info in prompts_log:
        shot_id = shot_info["shot_id"]
        overlay_config = shot_info.get("overlay_config", {})

        # 读取原图
        image_path = INPUT_DIR / f"shot_{shot_id:02d}.png"
        if not image_path.exists():
            print(f"\n[Shot {shot_id:02d}] ⚠️ 图片不存在: {image_path}")
            continue

        print(f"\n处理 shot_{shot_id:02d}...")

        # 加载原图
        original = Image.open(image_path).convert("RGBA")
        processed = original.copy()
        print(f"  原图尺寸: {original.size}")

        # 应用overlay（使用适配函数）
        overlays_applied = []

        if "top_monologue" in overlay_config:
            text = overlay_config["top_monologue"]
            processed = add_top_monologue(overlay_service, processed, text)
            overlays_applied.append("top_monologue")

        if "bottom_monologue" in overlay_config:
            text = overlay_config["bottom_monologue"]
            processed = add_bottom_monologue(overlay_service, processed, text)
            overlays_applied.append("bottom_monologue")

        if "center_monologue" in overlay_config:
            text = overlay_config["center_monologue"]
            processed = add_center_monologue(overlay_service, processed, text)
            overlays_applied.append("center_monologue")

        if "top_narrative" in overlay_config:
            text = overlay_config["top_narrative"]
            processed = add_top_narrative(overlay_service, processed, text)
            overlays_applied.append("top_narrative")

        if "speech_bubble" in overlay_config:
            bubble_config = overlay_config["speech_bubble"]
            text = bubble_config["text"]
            speaker = bubble_config.get("speaker", "right")
            processed = add_speech_bubble_v2(overlay_service, processed, text, speaker_position=speaker)
            overlays_applied.append("speech_bubble")

        # 保存处理后的图
        output_path = OUTPUT_DIR / f"shot_{shot_id:02d}_with_text_v2.png"
        processed.convert("RGB").save(output_path)
        print(f"  ✅ 保存: {output_path}")

        # 创建对比图
        comparison = create_comparison(
            original.convert("RGB"),
            processed.convert("RGB"),
            f"shot_{shot_id:02d}"
        )
        comparison_path = OUTPUT_DIR / f"shot_{shot_id:02d}_comparison_v2.png"
        comparison.save(comparison_path)
        print(f"  ✅ 对比图: {comparison_path}")

        results.append({
            "shot": f"shot_{shot_id:02d}",
            "success": True,
            "output": str(output_path),
            "comparison": str(comparison_path),
            "overlays": overlays_applied,
            "v2_features": {
                "font_size": f"default={DEFAULT_FONT_SIZE}, bubble={SPEECH_BUBBLE_FONT_SIZE}",
                "emphasis_enabled": "top_monologue" in overlays_applied or "speech_bubble" in overlays_applied,
                "dynamic_position": "speech_bubble" in overlays_applied
            }
        })

    # 保存结果
    results_path = OUTPUT_DIR / "results_v2.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计
    success_count = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"成功: {success_count}/{len(prompts_log)}")
    for r in results:
        overlays = r.get("overlays", [])
        print(f"  ✅ {r['shot']}: {overlays}")

    print(f"\n结果保存至: {results_path}")

    print("\n" + "=" * 60)
    print("新故事V2测试完成！")
    print(f"对比图目录: {OUTPUT_DIR}")
    print("=" * 60)


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    run_v2_overlay_test()
