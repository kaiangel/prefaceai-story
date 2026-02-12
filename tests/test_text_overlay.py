"""
条漫MVP文字叠加测试脚本

验证「后处理叠加文字」方案的可行性。

任务: HANDOFF-2026-01-22-005
作者: @Backend
日期: 2026-01-22

⚠️ 注意：这是验证测试，代码保持独立，不耦合到主流程
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, List
from dataclasses import dataclass

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.text_overlay_service import (
    TextOverlayService,
    strip_speaker_prefix,
    get_bubble_position_for_index,
    detect_overlay_collision,
)

# =============================================================================
# 配置
# =============================================================================

# 输入输出路径
INPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "20260122_161450"
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "text_overlay_test"

# 字体配置 - 尝试多个可能的字体路径
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

# 默认字体大小
DEFAULT_FONT_SIZE = 28
SPEECH_BUBBLE_FONT_SIZE = 24

# =============================================================================
# 数据类型定义
# =============================================================================

@dataclass
class TextOverlay:
    """文字叠加配置"""
    text: str
    overlay_type: str  # "top_monologue", "bottom_monologue", "center_monologue", "top_narrative", "speech_bubble"
    position: Optional[Tuple[int, int]] = None  # 对于speech_bubble使用


# =============================================================================
# 测试用例定义 (来自PM决策文档)
# =============================================================================

TEST_CASES = {
    "shot_01": {
        "overlays": [
            TextOverlay(
                text="那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！",
                overlay_type="top_monologue"
            ),
            TextOverlay(
                text="你说句话呀宝宝…",
                overlay_type="speech_bubble"
            )
        ]
    },
    "shot_06": {
        "overlays": [
            TextOverlay(
                text="这一幕我突然觉得似曾相识。",
                overlay_type="bottom_monologue"
            )
        ]
    },
    "shot_08": {
        "overlays": [
            TextOverlay(
                text="可是现在，我发现我越来越像他了。我仗着对方的紧张和在意，堂而皇之的关闭了自己的沟通渠道。",
                overlay_type="center_monologue"
            )
        ]
    },
    "shot_12": {
        "overlays": [
            TextOverlay(
                text="好。",
                overlay_type="speech_bubble"
            )
        ]
    },
    "shot_14": {
        "overlays": [
            TextOverlay(
                text="如果我爱你，就一定会尽可能告诉你，我为什么生气，要学会大大方方的表达爱意。",
                overlay_type="top_narrative"
            )
        ]
    }
}


# =============================================================================
# 测试适配函数 (使用主服务的 TextOverlayService)
# =============================================================================

def apply_overlay(service: TextOverlayService, image: Image.Image, overlay: TextOverlay) -> Image.Image:
    """应用单个文字叠加 - 适配测试用例格式到主服务"""
    overlay_type = overlay.overlay_type
    text = overlay.text

    if overlay_type == "top_monologue":
        return service.add_monologue(image, text, position="top", height_ratio=0.15)
    elif overlay_type == "bottom_monologue":
        return service.add_monologue(image, text, position="bottom", height_ratio=0.18)
    elif overlay_type == "center_monologue":
        return service.add_monologue(image, text, position="center", height_ratio=0.20)
    elif overlay_type == "top_narrative":
        return service.add_narrative(image, text, position="top", height_ratio=0.18)
    elif overlay_type == "speech_bubble":
        return service.add_speech_bubble(image, text, bubble_x_percent=75, bubble_y_percent=15)
    else:
        print(f"[警告] 未知的叠加类型: {overlay_type}")
        return image


def process_image(service: TextOverlayService, image: Image.Image, overlays: List[TextOverlay]) -> Image.Image:
    """处理单张图片，应用所有叠加"""
    result = image
    for overlay in overlays:
        result = apply_overlay(service, result, overlay)
    return result


# =============================================================================
# 对比图生成
# =============================================================================

def create_comparison(original: Image.Image, processed: Image.Image, shot_name: str) -> Image.Image:
    """创建原图和处理后的对比图"""

    # 确保两张图尺寸一致
    width, height = original.size

    # 创建对比图（左右并排）
    comparison = Image.new('RGB', (width * 2 + 20, height + 60), color='white')

    # 转换为RGB模式（如果是RGBA）
    if original.mode == 'RGBA':
        original_rgb = Image.new('RGB', original.size, 'white')
        original_rgb.paste(original, mask=original.split()[3])
        original = original_rgb

    if processed.mode == 'RGBA':
        processed_rgb = Image.new('RGB', processed.size, 'white')
        processed_rgb.paste(processed, mask=processed.split()[3])
        processed = processed_rgb

    # 粘贴图片
    comparison.paste(original, (0, 30))
    comparison.paste(processed, (width + 20, 30))

    # 添加标签
    draw = ImageDraw.Draw(comparison)
    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 20)
    except:
        label_font = ImageFont.load_default()

    draw.text((width // 2 - 30, 5), "原图", font=label_font, fill="black")
    draw.text((width + 20 + width // 2 - 50, 5), "叠加后", font=label_font, fill="black")
    draw.text((width * 2 // 2 - 50, height + 35), shot_name, font=label_font, fill="gray")

    return comparison


# =============================================================================
# 主测试流程
# =============================================================================

def run_text_overlay_test():
    """运行文字叠加测试"""

    print("=" * 60)
    print("条漫MVP文字叠加测试")
    print("=" * 60)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n输出目录: {OUTPUT_DIR}")

    # 初始化服务
    try:
        service = TextOverlayService()
    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 处理每个测试用例
    results = []

    for shot_name, config in TEST_CASES.items():
        print(f"\n处理 {shot_name}...")

        # 读取原图
        input_path = INPUT_DIR / f"{shot_name}.png"
        if not input_path.exists():
            print(f"  ❌ 文件不存在: {input_path}")
            results.append({"shot": shot_name, "success": False, "error": "文件不存在"})
            continue

        try:
            original = Image.open(input_path)
            print(f"  原图尺寸: {original.size}")

            # 应用文字叠加
            processed = process_image(service, original, config["overlays"])

            # 保存处理后的图片
            output_path = OUTPUT_DIR / f"{shot_name}_with_text.png"
            processed.save(output_path)
            print(f"  ✅ 保存: {output_path}")

            # 创建对比图
            comparison = create_comparison(original, processed, shot_name)
            comparison_path = OUTPUT_DIR / f"{shot_name}_comparison.png"
            comparison.save(comparison_path)
            print(f"  ✅ 对比图: {comparison_path}")

            results.append({
                "shot": shot_name,
                "success": True,
                "output": str(output_path),
                "comparison": str(comparison_path),
                "overlays": [o.overlay_type for o in config["overlays"]]
            })

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()
            results.append({"shot": shot_name, "success": False, "error": str(e)})

    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"成功: {success_count}/{len(results)}")

    for r in results:
        status = "✅" if r.get("success") else "❌"
        print(f"  {status} {r['shot']}: {r.get('overlays', r.get('error', 'N/A'))}")

    # 保存结果JSON
    import json
    results_path = OUTPUT_DIR / "results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存至: {results_path}")

    print("\n" + "=" * 60)
    print("测试完成！请查看对比图验收效果")
    print(f"对比图目录: {OUTPUT_DIR}")
    print("=" * 60)


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    run_text_overlay_test()
