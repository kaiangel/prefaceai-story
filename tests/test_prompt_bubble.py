"""
TASK-PROMPT-BUBBLE 验证测试

使用已有的对话密集型 storyboard 数据（含 text_overlay），
仅重跑 Stage 5（图像生成），验证 prompt 架构优化效果。

数据源:
  - dialogue_dense_test: 年夜饭三代人争吵 (illustration, 29 shots, 23 含对话)
  - e2e_slamdunk: 篮球故事 (slam_dunk, 20 shots, 5 含对话)

验证维度:
  1. 对话气泡渲染成功率（气泡是否出现 + 中文是否准确）
  2. 气泡定位准确性（是否靠近正确说话者）
  3. 角色一致性保持
  4. 风格一致性保持
  5. 场景描述准确性

运行: python tests/test_prompt_bubble.py
"""

import os
import sys
import json
import shutil
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 数据源配置
TEST_CONFIGS = [
    {
        "name": "dialogue_dense_illustration",
        "source_dir": "./test_output/manualtest/dialogue_dense_test/20260302_165748",
        "style": "illustration",
        "max_shots": 10,
        "description": "年夜饭三代人争吵 (illustration, 对话密集)"
    },
    {
        "name": "slamdunk_dialogue",
        "source_dir": "./test_output/manualtest/e2e_slamdunk/20260227_140414",
        "style": "slam_dunk",
        "max_shots": 10,
        "description": "篮球故事 (slam_dunk, 混合类型)"
    }
]


async def run_stage5_test(config: dict) -> dict:
    """使用已有 Stage 1-4 数据，仅运行 Stage 5 图像生成"""
    from app.services.image_generator import ImageGenerator, build_dialogue_scene_embed
    from app.services.reference_image_manager import ReferenceImageManager
    from app.services.scene_reference_manager import SceneReferenceManager
    from app.models.style_config import ProjectStyleConfig

    name = config["name"]
    source_dir = config["source_dir"]
    style = config["style"]
    max_shots = config["max_shots"]

    print(f"\n{'='*60}")
    print(f"TASK-PROMPT-BUBBLE Stage 5 测试: {name}")
    print(f"  source: {source_dir}")
    print(f"  style: {style}")
    print(f"  max_shots: {max_shots}")
    print(f"  描述: {config['description']}")
    print(f"{'='*60}")

    # 加载 Stage 1-4 数据
    outline = load_json(os.path.join(source_dir, "1_outline.json"))
    characters = load_json(os.path.join(source_dir, "2_characters.json"))
    screenplay = load_json(os.path.join(source_dir, "3_screenplay.json"))
    storyboard = load_json(os.path.join(source_dir, "4_storyboard.json"))

    shots = storyboard.get("shots", [])
    print(f"  加载完成: {len(shots)} shots")

    # 筛选含对话的 shots（优先）+ 补充其他类型至 max_shots
    dialogue_shots = [s for s in shots if s.get("text_overlay", {}).get("text_type", "none") in
                      ["dialogue", "dialogue_with_thought", "narration_with_dialogue", "dialogue_with_narration"]]
    other_shots = [s for s in shots if s not in dialogue_shots]

    # 取对话 shots（最多 max_shots），不够时补充其他
    test_shots = dialogue_shots[:max_shots]
    remaining = max_shots - len(test_shots)
    if remaining > 0:
        test_shots.extend(other_shots[:remaining])

    print(f"  测试 shots: {len(test_shots)} (含对话: {len([s for s in test_shots if s.get('text_overlay', {}).get('text_type', 'none') != 'none'])})")

    # 创建输出目录
    output_dir = f"./test_output/manualtest/prompt_bubble/{name}"
    os.makedirs(output_dir, exist_ok=True)
    images_dir = os.path.join(output_dir, "images")
    prompts_dir = os.path.join(output_dir, "prompts")
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(prompts_dir, exist_ok=True)

    # 复制 Stage 1-4 数据
    for fname in ["1_outline.json", "2_characters.json", "3_screenplay.json", "4_storyboard.json"]:
        src = os.path.join(source_dir, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(output_dir, fname))

    # 初始化服务
    image_generator = ImageGenerator()
    project_style = ProjectStyleConfig(style_preset=style)
    ref_manager = ReferenceImageManager()
    scene_ref_manager = SceneReferenceManager()

    # 生成角色参考图
    chars_list = characters.get("characters", [])
    print(f"\n--- 生成角色参考图 ({len(chars_list)} 角色) ---")
    for char in chars_list:
        char_name = char.get("name", "?")
        print(f"  生成 {char_name}...", end=" ")
        try:
            await ref_manager.generate_character_multi_refs(
                character=char,
                project_style=project_style,
                image_generator=image_generator
            )
            print("✅")
        except Exception as e:
            print(f"❌ {e}")

    # 生成场景参考图
    unique_locations = outline.get("unique_locations", [])
    if unique_locations:
        print(f"\n--- 生成场景参考图 ({len(unique_locations)} 场景) ---")
        try:
            await scene_ref_manager.generate_anchor_images(
                scenes=[],
                project_style=project_style,
                image_generator=image_generator,
                unique_locations=unique_locations,
                delay=3.0
            )
            print("  ✅ 场景参考图生成完成")
        except Exception as e:
            print(f"  ❌ 场景参考图生成失败: {e}")

    # 生成 shot 图像
    print(f"\n--- 生成 Shot 图像 ({len(test_shots)} shots) ---")
    results = []
    start_time = datetime.now()

    for i, shot in enumerate(test_shots):
        shot_id = shot.get("shot_id", i + 1)
        text_type = shot.get("text_overlay", {}).get("text_type", "none")
        chinese_text = shot.get("text_overlay", {}).get("chinese_text", "")

        # 显示对话嵌入预览
        dialogue_embed = ""
        if text_type != "none":
            dialogue_embed = build_dialogue_scene_embed(shot.get("text_overlay", {}))

        print(f"\n  Shot {shot_id}/{test_shots[-1].get('shot_id', '?')} (text_type={text_type})")
        if dialogue_embed:
            print(f"    嵌入文本: {dialogue_embed[:80]}...")

        # 获取参考图
        chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
        char_refs = ref_manager.get_references_for_scene(chars_in_scene)
        location_id = shot.get("location_id", "")
        scene_refs = scene_ref_manager.get_references_for_location(location_id) if location_id else []
        all_refs = char_refs + scene_refs

        print(f"    角色: {chars_in_scene} ({len(char_refs)}张), 场景: {location_id} ({len(scene_refs)}张)")

        try:
            result = await image_generator.generate_shot_image_phase2(
                shot=shot,
                storyboard=storyboard,
                characters=characters,
                style_preset=style,
                reference_images=all_refs,
                screenplay=screenplay,
                aspect_ratio="2:3",
                use_native_text=True  # 关键: 启用原生文字渲染
            )

            if result.get("success"):
                img_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                result["pil_image"].save(img_path)
                print(f"    ✅ 已保存: {img_path}")

                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "chinese_text": str(chinese_text)[:50] if chinese_text else "",
                    "dialogue_embedded": bool(dialogue_embed),
                    "success": True,
                    "generation_time": result.get("generation_time_seconds", 0)
                })
            else:
                print(f"    ❌ 生成失败: {result.get('error', 'unknown')}")
                results.append({
                    "shot_id": shot_id,
                    "text_type": text_type,
                    "success": False,
                    "error": result.get("error", "unknown")
                })
        except Exception as e:
            print(f"    ❌ 异常: {e}")
            results.append({
                "shot_id": shot_id,
                "text_type": text_type,
                "success": False,
                "error": str(e)
            })

        # Rate limiting
        await asyncio.sleep(1)

    elapsed = (datetime.now() - start_time).total_seconds()

    # 保存结果
    results_path = os.path.join(output_dir, "test_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 统计
    total = len(results)
    success = sum(1 for r in results if r.get("success"))
    dialogue_count = sum(1 for r in results if r.get("dialogue_embedded"))
    dialogue_success = sum(1 for r in results if r.get("dialogue_embedded") and r.get("success"))

    print(f"\n--- 结果统计 ---")
    print(f"  总数: {total}, 成功: {success}/{total}")
    print(f"  含对话嵌入: {dialogue_count}, 成功: {dialogue_success}/{dialogue_count}")
    print(f"  耗时: {elapsed:.0f}s")

    # 分析 prompt 字符数
    prompt_stats = analyze_prompt_stats(output_dir)

    return {
        "test_name": name,
        "description": config["description"],
        "style": style,
        "total_shots": total,
        "success_count": success,
        "dialogue_embedded_count": dialogue_count,
        "dialogue_success_count": dialogue_success,
        "elapsed_seconds": elapsed,
        "prompt_stats": prompt_stats or {},
        "results": results
    }


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_prompt_stats(project_dir):
    prompt_dir = os.path.join(project_dir, "prompts")
    if not os.path.exists(prompt_dir):
        prompt_dir = "forclaudeweb"
    if not os.path.exists(prompt_dir):
        return None

    lengths = []
    for f in os.listdir(prompt_dir):
        if f.endswith(".txt"):
            with open(os.path.join(prompt_dir, f), "r", encoding="utf-8") as fh:
                lengths.append(len(fh.read()))

    if not lengths:
        return None

    return {
        "avg_length": int(sum(lengths) / len(lengths)),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "count": len(lengths)
    }


def generate_comparison_report(results: list, elapsed: float) -> str:
    lines = [
        "# TASK-PROMPT-BUBBLE 验证报告",
        f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"总测试耗时: {elapsed:.0f}s",
        "",
        "## 优化内容",
        "",
        "| 优化项 | 描述 |",
        "|--------|------|",
        "| 方向 2 | 对话气泡嵌入 [SCENE DESCRIPTION]，格式: 'Near {speaker}, a white speech bubble...' |",
        "| 方向 3a | System Instruction 精简: 去掉冗余 Style Enforcement/Aspect Ratio 行 |",
        "| 方向 3b | Quality Suffix 禁用: 与 StyleEnforcer mandatory keywords 重叠 |",
        "| 方向 3c | TEXT OVERLAY REQUIREMENT dialogue 分支移除，仅保留 thought/narration |",
        "",
        "## 测试结果",
        "",
    ]

    for r in results:
        lines.append(f"### {r['test_name']}")
        lines.append(f"- **描述**: {r['description']}")
        lines.append(f"- **风格**: {r['style']}")
        lines.append(f"- **总 shots**: {r['total_shots']}")
        lines.append(f"- **成功**: {r['success_count']}/{r['total_shots']}")
        lines.append(f"- **含对话嵌入**: {r['dialogue_embedded_count']}")
        lines.append(f"- **对话嵌入成功**: {r['dialogue_success_count']}/{r['dialogue_embedded_count']}")
        lines.append(f"- **耗时**: {r['elapsed_seconds']:.0f}s")

        ps = r.get("prompt_stats", {})
        if ps:
            lines.append(f"- **Prompt 平均长度**: {ps.get('avg_length', 'N/A')} chars")

        # 列出每个 shot 的详情
        lines.append("")
        lines.append("| Shot ID | text_type | 对话嵌入 | 成功 | 备注 |")
        lines.append("|---------|-----------|---------|------|------|")
        for sr in r.get("results", []):
            embed = "✅" if sr.get("dialogue_embedded") else "-"
            success = "✅" if sr.get("success") else "❌"
            text = sr.get("chinese_text", "")[:30]
            error = sr.get("error", "")[:30] if not sr.get("success") else ""
            lines.append(f"| {sr['shot_id']} | {sr['text_type']} | {embed} | {success} | {text or error} |")
        lines.append("")

    lines.extend([
        "## 验证维度 (需人工检查图片)",
        "",
        "| 维度 | 检查项 | 结果 |",
        "|------|--------|------|",
        "| 对话气泡渲染 | 气泡是否出现 + 中文是否准确 | 待检查 |",
        "| 气泡定位 | 是否靠近正确说话者 | 待检查 |",
        "| 角色一致性 | 角色是否变脸 | 待检查 |",
        "| 风格一致性 | 风格是否保持 | 待检查 |",
        "| 场景描述 | 构图/光线/氛围是否准确 | 待检查 |",
        "",
        "## Prompt 架构变更对比",
        "",
        "### 优化前 (估算)",
        "- System Instruction: ~400 chars (含冗余 Style Enforcement + Aspect Ratio + 4条 CRITICAL REQUIREMENTS)",
        "- Quality Suffix: ~50-100 chars (与 mandatory keywords 重叠)",
        "- TEXT OVERLAY for dialogue: ~200-300 chars (追加在 prompt 末尾，注意力权重 < 1%)",
        "- **总冗余**: ~500-800 chars",
        "",
        "### 优化后",
        "- System Instruction: ~150 chars (精简为 Color Grade + Lighting + Lens + 1行 CONSISTENCY)",
        "- Quality Suffix: 已移除 (0 chars)",
        "- 对话: 嵌入 [SCENE DESCRIPTION] (~80-120 chars/条，在场景描述核心区，高注意力权重)",
        "- **净减少**: ~400-600 chars",
    ])

    return "\n".join(lines)


async def main():
    start_time = datetime.now()
    results = []

    for config in TEST_CONFIGS:
        if not os.path.exists(config["source_dir"]):
            print(f"⚠️ 跳过 {config['name']}: 源数据不存在 {config['source_dir']}")
            continue

        r = await run_stage5_test(config)
        if r:
            results.append(r)

    elapsed = (datetime.now() - start_time).total_seconds()

    # 生成报告
    report = generate_comparison_report(results, elapsed)
    report_path = "./test_output/manualtest/prompt_bubble/comparison_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n\n{'='*60}")
    print(f"TASK-PROMPT-BUBBLE 验证完成")
    print(f"  总耗时: {elapsed:.0f}s")
    print(f"  报告: {report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
