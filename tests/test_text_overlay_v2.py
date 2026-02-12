"""
条漫MVP文字叠加测试脚本 V2

V2 增强:
1. 字体增大50% (28→42, 24→36)
2. 动态气泡位置（根据说话者位置）
3. LLM驱动情感强调（红色高亮）
4. 支持多气泡场景

任务: HANDOFF-2026-01-22-007 / TASK-002
作者: @Backend
日期: 2026-01-22

⚠️ 注意：这是验证测试，代码保持独立，不耦合到主流程
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field

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
NO_TEXT_INPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "no_text_images"
OUTPUT_DIR = Path(__file__).parent.parent / "test_output" / "comic_mvp_test" / "text_overlay_v2_test"

# 字体配置
FONT_PATHS = [
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]

# V2 字体大小 (+50%)
DEFAULT_FONT_SIZE = 42  # V1: 28
SPEECH_BUBBLE_FONT_SIZE = 36  # V1: 24
EMPHASIS_FONT_SIZE = 52  # 强调文字 (+25% on default)

# 颜色
EMPHASIS_COLOR = "#FF4444"  # 红色强调

# =============================================================================
# 数据类型定义
# =============================================================================

@dataclass
class TextSegment:
    """文字片段（带强调标记）"""
    text: str
    emphasis: str = "none"  # "none", "red_large", "bold"


@dataclass
class TextEmphasis:
    """文字强调分析结果"""
    original_text: str
    segments: List[TextSegment] = field(default_factory=list)


@dataclass
class SpeechBubbleConfig:
    """对话气泡配置"""
    text: str
    speaker_position: str = "right"  # "left", "right", "center"
    speaker_vertical: str = "upper"  # "upper", "middle", "lower"


@dataclass
class TextOverlayV2:
    """V2 文字叠加配置"""
    text: str
    overlay_type: str  # "top_monologue", "bottom_monologue", "center_monologue", "top_narrative", "speech_bubble"
    speaker_position: Optional[str] = None  # 对于speech_bubble: "left", "right", "center"
    enable_emphasis: bool = True  # 是否启用情感强调


# =============================================================================
# LLM 情感强调分析（简化版，基于规则）
# =============================================================================

def analyze_text_emphasis_simple(text: str) -> TextEmphasis:
    """
    简化版文字强调分析（基于规则，无需LLM调用）

    规则:
    1. 多个感叹号(!!!) → 该句红色放大
    2. 强烈情绪词 → 红色放大
    3. 其他 → 无强调
    """
    result = TextEmphasis(original_text=text, segments=[])

    # 强调触发词
    emphasis_triggers = [
        "没一张能看的", "怎么回事", "不敢相信", "震惊", "崩溃",
        "太过分了", "受不了", "气死", "不可能", "凭什么"
    ]

    # 检查是否有多个感叹号
    if "!!!" in text or "！！！" in text:
        # 找到感叹号位置，分割文本
        for sep in ["!!!", "！！！"]:
            if sep in text:
                idx = text.find(sep)
                # 向前找到句子开始（逗号、句号、或开头）
                start_idx = max(
                    text.rfind("，", 0, idx),
                    text.rfind(",", 0, idx),
                    text.rfind("。", 0, idx),
                    0
                )
                if start_idx > 0:
                    start_idx += 1  # 跳过标点

                before_text = text[:start_idx].strip()
                emphasis_text = text[start_idx:idx + len(sep)].strip()
                after_text = text[idx + len(sep):].strip()

                if before_text:
                    result.segments.append(TextSegment(text=before_text, emphasis="none"))
                if emphasis_text:
                    result.segments.append(TextSegment(text=emphasis_text, emphasis="red_large"))
                if after_text:
                    result.segments.append(TextSegment(text=after_text, emphasis="none"))

                return result

    # 检查强调触发词
    for trigger in emphasis_triggers:
        if trigger in text:
            idx = text.find(trigger)
            before_text = text[:idx].strip()
            emphasis_text = trigger
            after_text = text[idx + len(trigger):].strip()

            if before_text:
                result.segments.append(TextSegment(text=before_text, emphasis="none"))
            result.segments.append(TextSegment(text=emphasis_text, emphasis="red_large"))
            if after_text:
                result.segments.append(TextSegment(text=after_text, emphasis="none"))

            return result

    # 无强调
    result.segments.append(TextSegment(text=text, emphasis="none"))
    return result


# =============================================================================
# LLM 情感强调分析（完整版，调用Gemini）
# =============================================================================

async def analyze_text_emphasis_llm(text: str) -> TextEmphasis:
    """
    使用LLM分析文字，识别需要强调的部分

    返回结构化的强调信息
    """
    try:
        from app.services.gemini_service import GeminiService

        gemini = GeminiService()

        prompt = f"""你是一个漫画文字分析助手。分析以下文字，识别需要视觉强调的部分。

文字：{text}

请返回JSON格式：
{{
  "original_text": "{text}",
  "segments": [
    {{"text": "普通文字部分", "emphasis": "none"}},
    {{"text": "需要强调的部分", "emphasis": "red_large", "reason": "原因"}}
  ]
}}

强调规则：
1. "red_large": 红色+放大 - 用于强烈情绪（愤怒、震惊、崩溃、多感叹号）
2. "bold": 加粗 - 用于重点词但非强烈情绪
3. "none": 无强调 - 普通叙述

只返回JSON，不要其他内容。"""

        response = await gemini.generate_text(prompt)

        # 解析JSON
        import json
        data = json.loads(response)
        segments = [TextSegment(text=s["text"], emphasis=s.get("emphasis", "none"))
                    for s in data.get("segments", [])]
        return TextEmphasis(original_text=text, segments=segments)

    except Exception as e:
        print(f"[TextOverlay V2] LLM分析失败，使用规则分析: {e}")
        return analyze_text_emphasis_simple(text)


# =============================================================================
# 测试适配函数 (使用主服务的 TextOverlayService)
# =============================================================================

def apply_overlay_v2(service: TextOverlayService, image: Image.Image, overlay: TextOverlayV2) -> Image.Image:
    """应用单个文字叠加 - V2 适配器"""
    overlay_type = overlay.overlay_type
    text = overlay.text

    if overlay_type == "top_monologue":
        return service.add_monologue(
            image, text, position="top", height_ratio=0.15,
            enable_emphasis=overlay.enable_emphasis
        )
    elif overlay_type == "bottom_monologue":
        return service.add_monologue(
            image, text, position="bottom", height_ratio=0.18,
            enable_emphasis=overlay.enable_emphasis
        )
    elif overlay_type == "center_monologue":
        return service.add_monologue(
            image, text, position="center", height_ratio=0.20,
            enable_emphasis=overlay.enable_emphasis
        )
    elif overlay_type == "top_narrative":
        return service.add_narrative(image, text, position="top", height_ratio=0.18)
    elif overlay_type == "speech_bubble":
        # 转换 speaker_position 到 bubble_x_percent
        speaker_pos = overlay.speaker_position or "right"
        if speaker_pos == "left":
            x_pct = 25
        elif speaker_pos == "center":
            x_pct = 50
        else:  # right
            x_pct = 75
        return service.add_speech_bubble(image, text, bubble_x_percent=x_pct, bubble_y_percent=12)
    else:
        print(f"[警告] 未知的叠加类型: {overlay_type}")
        return image


def process_image_v2(service: TextOverlayService, image: Image.Image, overlays: List[TextOverlayV2]) -> Image.Image:
    """处理单张图片，应用所有叠加"""
    result = image
    for overlay in overlays:
        result = apply_overlay_v2(service, result, overlay)
    return result


# =============================================================================
# 测试用例定义 V2
# =============================================================================

TEST_CASES_V2 = {
    "shot_01": {
        "overlays": [
            TextOverlayV2(
                text="那天和男朋友逛街，让他帮我拍照，拍了好多张没一张能看的！！！",
                overlay_type="top_monologue",
                enable_emphasis=True  # 测试情感强调
            ),
            TextOverlayV2(
                text="你说句话呀宝宝…",
                overlay_type="speech_bubble",
                speaker_position="right"  # 男主在右侧说话
            )
        ]
    },
    "shot_06": {
        "overlays": [
            TextOverlayV2(
                text="这一幕我突然觉得似曾相识。",
                overlay_type="bottom_monologue",
                enable_emphasis=False
            )
        ]
    },
    "shot_08": {
        "overlays": [
            TextOverlayV2(
                text="可是现在，我发现我越来越像他了。我仗着对方的紧张和在意，堂而皇之的关闭了自己的沟通渠道。",
                overlay_type="center_monologue",
                enable_emphasis=False
            )
        ]
    },
    "shot_12": {
        "overlays": [
            TextOverlayV2(
                text="好。",
                overlay_type="speech_bubble",
                speaker_position="left"  # 女主在左侧说话
            )
        ]
    },
    "shot_14": {
        "overlays": [
            TextOverlayV2(
                text="如果我爱你，就一定会尽可能告诉你，我为什么生气，要学会大大方方的表达爱意。",
                overlay_type="top_narrative"
            )
        ]
    }
}


# =============================================================================
# 对比图生成
# =============================================================================

def create_comparison(original: Image.Image, processed: Image.Image, shot_name: str) -> Image.Image:
    """创建原图和处理后的对比图"""

    width, height = original.size
    comparison = Image.new('RGB', (width * 2 + 20, height + 60), color='white')

    if original.mode == 'RGBA':
        original_rgb = Image.new('RGB', original.size, 'white')
        original_rgb.paste(original, mask=original.split()[3])
        original = original_rgb

    if processed.mode == 'RGBA':
        processed_rgb = Image.new('RGB', processed.size, 'white')
        processed_rgb.paste(processed, mask=processed.split()[3])
        processed = processed_rgb

    comparison.paste(original, (0, 30))
    comparison.paste(processed, (width + 20, 30))

    draw = ImageDraw.Draw(comparison)
    try:
        label_font = ImageFont.truetype("/System/Library/Fonts/STHeiti Medium.ttc", 20)
    except:
        label_font = ImageFont.load_default()

    draw.text((width // 2 - 50, 5), "无文字原图", font=label_font, fill="black")
    draw.text((width + 20 + width // 2 - 70, 5), "V2叠加后", font=label_font, fill="black")
    draw.text((width * 2 // 2 - 50, height + 35), shot_name, font=label_font, fill="gray")

    return comparison


# =============================================================================
# 主测试流程
# =============================================================================

def run_text_overlay_v2_test():
    """运行文字叠加V2测试"""

    print("=" * 60)
    print("条漫MVP文字叠加测试 V2")
    print("增强: 字体+50%, 动态气泡, 情感强调")
    print("=" * 60)

    # 检查输入目录
    if not NO_TEXT_INPUT_DIR.exists():
        print(f"\n❌ 无文字图片目录不存在: {NO_TEXT_INPUT_DIR}")
        print("请先运行 test_comic_mvp_story_no_text.py 生成无文字图片")
        return

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n输入目录: {NO_TEXT_INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 初始化服务
    try:
        service = TextOverlayService()
    except RuntimeError as e:
        print(f"❌ 初始化失败: {e}")
        return

    # 处理每个测试用例
    results = []

    for shot_name, config in TEST_CASES_V2.items():
        print(f"\n处理 {shot_name}...")

        # 读取无文字原图
        input_path = NO_TEXT_INPUT_DIR / f"{shot_name}.png"
        if not input_path.exists():
            print(f"  ❌ 文件不存在: {input_path}")
            results.append({"shot": shot_name, "success": False, "error": "文件不存在"})
            continue

        try:
            original = Image.open(input_path)
            print(f"  原图尺寸: {original.size}")

            # 应用V2文字叠加
            processed = process_image_v2(service, original, config["overlays"])

            # 保存处理后的图片
            output_path = OUTPUT_DIR / f"{shot_name}_with_text_v2.png"
            processed.save(output_path)
            print(f"  ✅ 保存: {output_path}")

            # 创建对比图
            comparison = create_comparison(original, processed, shot_name)
            comparison_path = OUTPUT_DIR / f"{shot_name}_comparison_v2.png"
            comparison.save(comparison_path)
            print(f"  ✅ 对比图: {comparison_path}")

            results.append({
                "shot": shot_name,
                "success": True,
                "output": str(output_path),
                "comparison": str(comparison_path),
                "overlays": [o.overlay_type for o in config["overlays"]],
                "v2_features": {
                    "font_size": f"default={DEFAULT_FONT_SIZE}, bubble={SPEECH_BUBBLE_FONT_SIZE}",
                    "emphasis_enabled": any(o.enable_emphasis for o in config["overlays"]),
                    "dynamic_position": any(o.speaker_position for o in config["overlays"])
                }
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
    results_path = OUTPUT_DIR / "results_v2.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果保存至: {results_path}")

    print("\n" + "=" * 60)
    print("V2测试完成！")
    print(f"对比图目录: {OUTPUT_DIR}")
    print("=" * 60)

    print("\nV2增强验收点:")
    print("  1. 字体大小是否增大50%（对比V1更清晰）")
    print("  2. 气泡位置是否靠近说话角色")
    print("  3. shot_01的'没一张能看的！！！'是否红色高亮")


# =============================================================================
# 入口
# =============================================================================

if __name__ == "__main__":
    run_text_overlay_v2_test()
