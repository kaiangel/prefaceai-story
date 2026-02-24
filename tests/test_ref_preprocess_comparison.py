"""
TASK-REF-PREPROCESS Step 3: 参考图预处理对比测试

对比有/无预处理对边缘问题的影响。
- shot_34: 留白/Jerry单角色/1张参考图
- shot_36: 留黑/Jerry+Cici双角色/2张参考图
- shot_22: 留白/Jerry+Cici双角色/2张参考图

输出:
- test_output/ref_preprocess_test/without/  (无预处理)
- test_output/ref_preprocess_test/with/     (有预处理)

用法:
    python tests/test_ref_preprocess_comparison.py

作者: @Backend
日期: 2026-02-13
任务: TASK-REF-PREPROCESS Step 3 (DEC-009)
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from PIL import Image

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 加载环境变量
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.image_generator import ImageGenerator

# =============================================================================
# 配置
# =============================================================================

OUTPUT_BASE = Path(__file__).parent.parent / "test_output" / "ref_preprocess_test"
WITHOUT_DIR = OUTPUT_BASE / "without"
WITH_DIR = OUTPUT_BASE / "with"

REF_DIR = Path(__file__).parent.parent / "test_output" / "manualtest" / "teststory_CCJerry" / "character_refs"

ASPECT_RATIO = "9:16"

# =============================================================================
# 韩漫风格前缀和无文字要求（从 test_comic_cc_jerry.py 提取）
# =============================================================================

KOREAN_WEBTOON_STYLE_PREFIX = """STYLE: Korean Webtoon / Manhwa Style

Full-color digital illustration in Korean webtoon aesthetic.
Refined facial features with detailed eyes and expressive emotions.
Soft lighting with warm color palette. Modern urban fashion sense.
Clean linework with subtle gradients. Romantic atmosphere.

MANDATORY STYLE REQUIREMENTS:
- Beautiful, detailed eyes with light reflections
- Soft shading with clean cel-shading techniques
- Warm, inviting color temperature
- Skin rendered with soft gradients (NOT flat color)
- Hair with detailed strands and highlights
- Modern fashion accuracy"""

TEXT_FREE_REQUIREMENT = """
ABSOLUTELY NO TEXT ALLOWED:
- This image must contain ZERO visible text, characters, letters, or words in any language
- DO NOT draw any speech bubbles, dialogue balloons, caption boxes, or text areas
- DO NOT leave blank white/empty rectangular areas for text
- Any visible text will cause this image to FAIL validation

FULL CANVAS COMPOSITION:
- Fill the ENTIRE canvas edge-to-edge with scene content
- DO NOT leave any black bars, white bars, or empty borders
- The image content MUST extend to all four edges
- NO letterboxing, NO pillarboxing, NO margins of any kind
- Background elements (sky, walls, floor, foliage) should reach every edge"""

# =============================================================================
# 3个对比测试shot的数据（从 test_comic_cc_jerry.py 提取）
# =============================================================================

TEST_SHOTS = [
    {
        "shot_id": 34,
        "scene": "车内对话",
        "edge_issue": "顶部大白边（留白）",
        "characters": ["Jerry"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
INTERIOR CAR SHOT from Cici's POV (passenger seat perspective). Shows Jerry in the driver's seat, hands on the wheel, driving smoothly. His profile is visible, expression focused but relaxed.

The dashboard provides soft illumination. Outside the windshield, city lights blur past. The atmosphere inside is warm and intimate despite the car being in motion.

Jerry wears his dark sweater (coat off while driving). His glasses reflect the passing lights. He occasionally glances toward the passenger seat (toward camera) with a warm smile.

COMPOSITION REQUIREMENT:
- Frame ends at center console - do NOT show passenger seat area
- Cici is NOT VISIBLE in this shot (camera is from her POV)
- Do NOT include partial body parts at frame edges
- All visible body parts must be complete and natural

CHARACTER REFERENCE:
- Jerry: FACE REFERENCE ONLY. Focused but happy while driving. CLOTHING: dark purple-black sweater, glasses

{TEXT_FREE_REQUIREMENT}
DO NOT include any readable dashboard text or signs.
"""
    },
    {
        "shot_id": 36,
        "scene": "到达楼下",
        "edge_issue": "上下有黑边（留黑）",
        "characters": ["Jerry", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
WIDE SHOT of a residential area entrance at night. A car is parked by the curb, and both figures have just gotten out, standing by the vehicle.

The residential entrance shows a modern Shanghai apartment complex - clean, well-lit entrance with some greenery. A security booth with soft light. The neighborhood is quiet, peaceful.

Both are back in their coats, standing close together by the car. Their body language shows reluctance to part - facing each other rather than walking toward the entrance.

Street lamps provide warm lighting. The night is deep but not too cold.

CHARACTER REFERENCE:
- Jerry: FACE REFERENCE ONLY. Standing by car. CLOTHING: black overcoat
- Cici: FACE REFERENCE ONLY. Standing close to him. CLOTHING: black coat, red scarf

{TEXT_FREE_REQUIREMENT}
"""
    },
    {
        "shot_id": 22,
        "scene": "眼神交汇",
        "edge_issue": "上边有分隔线（留白）",
        "characters": ["Jerry", "Cici"],
        "image_prompt": f"""{KOREAN_WEBTOON_STYLE_PREFIX}
CLOSE-UP TWO-SHOT capturing an intimate moment of eye contact across the table. Both characters' faces in frame, looking at each other with a moment of shared connection.

The moment captures that electric instant when both happen to look up at the same time - a beat of surprised recognition, then soft smiles spreading on both faces.

LEFT - Cici's face in close-up, her warm brown eyes meeting his gaze, a gentle surprised smile, cheeks slightly flushed.

RIGHT - Jerry's face in close-up, his eyes behind glasses showing warmth and connection, a matching smile forming.

ROMANTIC ATMOSPHERE:
- Soft candlelight between them (visible in lower frame)
- Warm color tones
- The air feels charged with unspoken attraction
- Korean webtoon style soft glow/sparkle effects subtle around their eyes

CHARACTER REFERENCE:
- Cici: FACE REFERENCE ONLY. Soft surprised smile, warm eyes. CLOTHING: BLACK fitted knit sweater (NOT beige, NOT teal, NOT any light color!)
- Jerry: FACE REFERENCE ONLY. Gentle smile, warm gaze through glasses. CLOTHING: dark purple-black sweater

{TEXT_FREE_REQUIREMENT}
Their eyes and expressions are the absolute focus.
"""
    },
]


# =============================================================================
# 核心逻辑
# =============================================================================

def load_reference_images() -> Dict[str, Image.Image]:
    """加载参考图"""
    refs = {}
    for name, filename in [("Jerry", "Jerry_fullbody.png"), ("Cici", "CC_fullbody.png")]:
        path = REF_DIR / filename
        if path.exists():
            refs[name] = Image.open(path)
            w, h = refs[name].size
            print(f"  ✅ {name}: {path.name} ({w}x{h}, ratio={w/h:.3f})")
        else:
            print(f"  ❌ {name}: {path} 不存在")
    return refs


async def generate_shot(
    image_gen: ImageGenerator,
    shot: dict,
    ref_images: Dict[str, Image.Image],
    output_dir: Path,
) -> dict:
    """生成单个shot"""
    shot_id = shot["shot_id"]
    char_ids = shot["characters"]

    # 收集该shot的参考图
    reference_images = [ref_images[c] for c in char_ids if c in ref_images]

    print(f"  [Shot {shot_id:02d}] {shot['scene']} | 参考图: {len(reference_images)}张 | 边缘问题: {shot['edge_issue']}")

    try:
        result = await image_gen.generate_image(
            prompt=shot["image_prompt"],
            aspect_ratio=ASPECT_RATIO,
            use_pro_model=False,
            reference_images=reference_images if reference_images else None
        )

        if result.get("success"):
            pil_image = result["pil_image"]
            image_path = output_dir / f"shot_{shot_id:02d}.png"
            pil_image.save(image_path)
            w, h = pil_image.size
            print(f"    ✅ 成功 ({w}x{h}, {result['generation_time_seconds']}s)")
            return {"success": True, "shot_id": shot_id, "size": f"{w}x{h}", "time": result["generation_time_seconds"]}
        else:
            print(f"    ❌ 失败: {result.get('error', 'Unknown')[:100]}")
            return {"success": False, "shot_id": shot_id, "error": result.get("error", "Unknown")}

    except Exception as e:
        print(f"    ❌ 异常: {str(e)[:100]}")
        return {"success": False, "shot_id": shot_id, "error": str(e)}


async def run_comparison_test():
    """运行对比测试"""
    print("=" * 70)
    print("TASK-REF-PREPROCESS Step 3: 参考图预处理对比测试")
    print("=" * 70)
    print(f"测试shot: 34(留白/单角色), 36(留黑/双角色), 22(留白/双角色)")
    print(f"目标宽高比: {ASPECT_RATIO}")
    print()

    # 创建输出目录
    WITHOUT_DIR.mkdir(parents=True, exist_ok=True)
    WITH_DIR.mkdir(parents=True, exist_ok=True)

    # 加载参考图
    print("--- 加载参考图 ---")
    ref_images = load_reference_images()
    if len(ref_images) < 2:
        print("❌ 参考图不完整，无法继续")
        return
    print()

    image_gen = ImageGenerator()
    results = {"without": [], "with": []}

    # =====================================================================
    # Phase 1: 无预处理
    # =====================================================================
    print("=" * 70)
    print("Phase 1: 无预处理（禁用 _preprocess_reference_to_aspect_ratio）")
    print(f"输出: {WITHOUT_DIR}")
    print("=" * 70)

    # Monkey-patch: 临时替换预处理方法为 noop（返回原图）
    original_method = image_gen._preprocess_reference_to_aspect_ratio
    image_gen._preprocess_reference_to_aspect_ratio = lambda ref_img, target_ratio: ref_img

    for shot in TEST_SHOTS:
        result = await generate_shot(image_gen, shot, ref_images, WITHOUT_DIR)
        results["without"].append(result)
        await asyncio.sleep(3)  # 避免限流

    # 恢复原方法
    image_gen._preprocess_reference_to_aspect_ratio = original_method

    print()

    # =====================================================================
    # Phase 2: 有预处理
    # =====================================================================
    print("=" * 70)
    print("Phase 2: 有预处理（启用 _preprocess_reference_to_aspect_ratio）")
    print(f"输出: {WITH_DIR}")
    print("=" * 70)

    for shot in TEST_SHOTS:
        result = await generate_shot(image_gen, shot, ref_images, WITH_DIR)
        results["with"].append(result)
        await asyncio.sleep(3)  # 避免限流

    # =====================================================================
    # 生成报告
    # =====================================================================
    print()
    print("=" * 70)
    print("对比测试完成 — 结果摘要")
    print("=" * 70)

    print(f"\n{'Shot':<10} {'边缘问题':<20} {'无预处理':<12} {'有预处理':<12}")
    print("-" * 54)
    for i, shot in enumerate(TEST_SHOTS):
        w_status = "✅" if results["without"][i]["success"] else "❌"
        p_status = "✅" if results["with"][i]["success"] else "❌"
        print(f"shot_{shot['shot_id']:02d}   {shot['edge_issue']:<18} {w_status:<12} {p_status:<12}")

    print(f"\n输出目录:")
    print(f"  无预处理: {WITHOUT_DIR}")
    print(f"  有预处理: {WITH_DIR}")
    print(f"\n请 @Tester 对比以上两组图片，评估边缘问题改善效果。")

    # 保存报告JSON
    report = {
        "task": "TASK-REF-PREPROCESS Step 3",
        "timestamp": datetime.now().isoformat(),
        "aspect_ratio": ASPECT_RATIO,
        "test_shots": [
            {"shot_id": s["shot_id"], "scene": s["scene"], "edge_issue": s["edge_issue"], "characters": s["characters"]}
            for s in TEST_SHOTS
        ],
        "results": results
    }
    report_path = OUTPUT_BASE / "comparison_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    asyncio.run(run_comparison_test())
