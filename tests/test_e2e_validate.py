"""
TASK-E2E-VALIDATE: Phase 1 端到端流水线验证 + TextOverlay 集成

Step 1a: 用 Phase2PipelineOrchestrator 跑通 Stage 1→5 基础流水线（~18 shots）
Step 1b: TextOverlay 集成验证（Stage 4 输出 text_overlay + pipeline 后处理）

输出目录: ./test_output/manualtest/e2e_validate/{timestamp}/
  - images/          无文字原图
  - with_text_images/ 带文字版本
  - character_refs/   角色参考图
  - scene_refs/       场景参考图
  - 1_outline.json ~ 5_image_results.json  各阶段产出

作者: @Backend
日期: 2026-02-24
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from app.services.pipeline_orchestrator import Phase2PipelineOrchestrator


async def run_e2e_validate():
    """运行端到端流水线验证"""
    print("=" * 70)
    print("TASK-E2E-VALIDATE: Phase 1 端到端流水线验证")
    print("=" * 70)

    orchestrator = Phase2PipelineOrchestrator(
        output_dir="./test_output/manualtest/e2e_validate"
    )

    result = await orchestrator.run(
        idea="雨夜公交站，一个加班族和一个失恋女孩因为同一把伞产生交集的温暖故事",
        style_preset="realistic",
        target_duration_minutes=3,
        character_count=2,
        generate_images=True,
        shots_limit=0  # 不限制，生成全部 shots
    )

    print("\n" + "=" * 70)
    if result.get("success"):
        summary = result["summary"]
        print("✅ E2E VALIDATE 通过!")
        print(f"  项目目录: {summary['project_dir']}")
        print(f"  故事标题: {summary['title']}")
        print(f"  角色数: {summary['total_characters']}")
        print(f"  场景数: {summary['total_scenes']}")
        print(f"  镜头数: {summary['total_shots']}")
        print(f"  耗时: {summary['pipeline_duration_seconds']:.1f}秒")

        # 检查 TextOverlay 结果
        images = result.get("stage_results", {}).get("images", [])
        with_text_count = sum(1 for img in images if img.get("with_text_path"))
        print(f"\n  TextOverlay 统计:")
        print(f"    带文字版: {with_text_count}/{len(images)}")
    else:
        print(f"❌ E2E VALIDATE 失败!")
        print(f"  失败阶段: {result.get('failed_stage')}")
        print(f"  错误: {result.get('error')}")
    print("=" * 70)

    return result


if __name__ == "__main__":
    asyncio.run(run_e2e_validate())
