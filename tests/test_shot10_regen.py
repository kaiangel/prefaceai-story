"""
TASK-SHOT10-REGEN: 补生成 shot_10（Bug #5 修复验证）

Shot 10 在回归验证中因 Bug #5 (dialogue handler dict crash) 缺失。
Bug #5 已修复 (image_generator.py L81-82 isinstance dict check)。
本脚本使用已有 storyboard 数据和参考图，仅重新生成 shot_10。
"""

import asyncio
import json
import os
import sys
import time

from PIL import Image
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import _label_reference_image
from app.services.scene_reference_manager import _label_scene_image

PROJECT_DIR = "test_output/manualtest/bugfix_regression/20260304_162910"


async def main():
    print("=" * 60)
    print("TASK-SHOT10-REGEN: 补生成 shot_10")
    print("=" * 60)

    # 1. Load JSON data
    with open(f"{PROJECT_DIR}/2_characters.json", "r", encoding="utf-8") as f:
        characters = json.load(f)

    with open(f"{PROJECT_DIR}/3_screenplay.json", "r", encoding="utf-8") as f:
        screenplay = json.load(f)

    with open(f"{PROJECT_DIR}/4_storyboard.json", "r", encoding="utf-8") as f:
        storyboard = json.load(f)

    # 2. Find shot_10
    shots = storyboard.get("shots", [])
    shot = next((s for s in shots if s.get("shot_id") == 10), None)
    if not shot:
        print("❌ shot_id=10 not found in storyboard")
        return

    print(f"\n[Shot 10] scene_id={shot['scene_id']}, "
          f"shot_size={shot['camera']['shot_size']}, "
          f"angle={shot['camera']['angle']}")
    print(f"  text_type={shot['text_overlay']['text_type']}")
    print(f"  chinese_text type: {type(shot['text_overlay']['chinese_text']).__name__}")

    # Verify dict format (Bug #5 trigger)
    ct = shot['text_overlay']['chinese_text']
    if isinstance(ct, list) and len(ct) > 0 and isinstance(ct[0], dict):
        print(f"  ✅ chinese_text is dict list ({len(ct)} items) — Bug #5 trigger data confirmed")
    else:
        print(f"  ⚠️ chinese_text is NOT dict list — may not exercise Bug #5 fix")

    # 3. Build reference images (labeled, matching pipeline behavior)
    chars_in_scene = shot.get("character_direction", {}).get("characters_visible", [])
    shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
    print(f"\n  Characters: {chars_in_scene}")
    print(f"  Shot type: {shot_type} → using fullbody refs")

    # Character name lookup
    char_names = {}
    for c in characters.get("characters", []):
        char_names[c["id"]] = c.get("name_en", c["id"])

    # Load and label character refs (wide_shot → fullbody)
    reference_images = []
    for char_id in chars_in_scene:
        fullbody_path = f"{PROJECT_DIR}/character_refs/{char_id}_fullbody.png"
        if os.path.exists(fullbody_path):
            img = Image.open(fullbody_path)
            name_en = char_names.get(char_id, char_id)
            labeled = _label_reference_image(img, f"Character: {name_en}")
            reference_images.append(labeled)
            print(f"  Loaded: {char_id} fullbody → labeled 'Character: {name_en}'")

    # Load and label scene ref (scene_id=4 → old_family_dining_room)
    location_id = "old_family_dining_room"
    scene_path = f"{PROJECT_DIR}/scene_refs/{location_id}_interior_anchor.png"
    if os.path.exists(scene_path):
        img = Image.open(scene_path)
        labeled = _label_scene_image(img, f"Scene: {location_id} Interior")
        reference_images.append(labeled)
        print(f"  Loaded: {location_id} interior → labeled")

    print(f"\n  Total reference images: {len(reference_images)}")

    # 4. Generate shot_10
    print(f"\n{'='*60}")
    print(f"Generating shot_10...")
    print(f"{'='*60}")

    image_generator = ImageGenerator()
    start_time = time.time()

    result = await image_generator.generate_shot_image_phase2(
        shot=shot,
        storyboard=storyboard,
        characters=characters,
        style_preset="illustration",
        reference_images=reference_images,
        screenplay=screenplay,
        aspect_ratio="2:3",
        use_native_text=True,
    )

    elapsed = time.time() - start_time

    # 5. Save result
    if result.get("success") and result.get("pil_image"):
        output_path = f"{PROJECT_DIR}/shots/shot_10.png"
        result["pil_image"].save(output_path)
        w, h = result["pil_image"].size
        print(f"\n✅ shot_10 生成成功!")
        print(f"  输出: {output_path}")
        print(f"  尺寸: {w}x{h}")
        print(f"  模型: {result.get('model_used', 'unknown')}")
        print(f"  耗时: {elapsed:.1f}s")
        print(f"\n  Bug #5 验证: dict 格式 chinese_text 被正确处理 ✅")
    else:
        print(f"\n❌ shot_10 生成失败!")
        print(f"  错误: {result.get('error', 'unknown')}")
        print(f"  耗时: {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
