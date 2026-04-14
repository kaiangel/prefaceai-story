"""
A vs B' Prompt Format A/B Test — 10-shot blind comparison

Generates 20 images (10 shots x 2 formats) using the same reference images,
then outputs blind-named files for human evaluation.

Usage:
    cd /Users/kaisbabybook/AIFun/xuhuastory/xuhua_story
    python3 tests/test_prompt_format_ab.py
"""

import asyncio
import json
import os
import random
import time
import sys

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from PIL import Image

from app.services.image_generator import ImageGenerator, build_dialogue_scene_embed, build_native_text_prompt
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.services.style_enforcer import StyleEnforcer
from app.models.style_config import ProjectStyleConfig
from app.prompts.storyboard_prompts import (
    Phase2PromptBuilder,
    build_identity_line_phase2,
    build_character_reference_mapping_phase2,
    build_critical_header_phase2,
    build_narrative_context_phase2,
    build_system_instruction_phase2,
)

# ============================================================================
# Configuration
# ============================================================================

DATA_DIR = os.path.join(PROJECT_ROOT, "test_output/manualtest/sq_upgrade_ab_test/20260304_113630")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "test_output/manualtest/prompt_ab_test")
BLIND_DIR = os.path.join(OUTPUT_DIR, "blind")
PROMPTS_DIR = os.path.join(OUTPUT_DIR, "prompts")
REFS_DIR = os.path.join(OUTPUT_DIR, "references")

STYLE_PRESET = "illustration"
NUM_SHOTS = 10
DELAY_BETWEEN_SHOTS = 5.0  # seconds between API calls


# ============================================================================
# B' Prompt Builder
# ============================================================================

def build_b_prime_prompt(
    shot: dict,
    storyboard: dict,
    characters: dict,
    style_preset: str,
    reference_images: list = None,
    use_native_text: bool = True,
) -> str:
    """
    Build prompt in B' (compressed label) format.

    Key difference from A: same identity_line and image_prompt content,
    but wrapped in compressed tagged structure instead of verbose decorated blocks.
    """
    enforcement = StyleEnforcer.get_enforcement(style_preset)
    if not enforcement:
        raise ValueError(f"Unknown style preset: {style_preset}")

    characters_list = characters.get("characters", [])
    global_dir = storyboard.get("global_visual_direction", {})

    # --- Style header (compressed) ---
    mandatory_str = ", ".join(enforcement.mandatory_keywords[:5])
    forbidden_str = ", ".join(enforcement.forbidden_keywords[:6])

    # Compressed style direction (~30 words as specified in task)
    compressed_style = (
        "Painterly light with warm gradients guiding the eye. "
        "Rich textures on fabric and surfaces. "
        "Characters defined through posture and micro-expression. "
        "Compositions balance clarity with depth."
    )

    parts = []
    parts.append(f"\u2550\u2550\u2550 MANDATORY STYLE: {enforcement.style_display_name} \u2550\u2550\u2550")
    parts.append(f"MUST INCLUDE: {mandatory_str}. DO NOT USE: {forbidden_str}.")
    parts.append(compressed_style)

    # --- Character consistency (compressed) ---
    char_direction = shot.get("character_direction", {})
    characters_visible = char_direction.get("characters_visible", [])

    if characters_visible:
        parts.append("")
        parts.append("[CHARACTER CONSISTENCY]")
        parts.append(
            "FIXED: facial features, hair, clothing, accessories MUST match reference images. "
            "FLEXIBLE: expression, pose, camera angle."
        )

    # --- References instruction (compressed) ---
    parts.append("")
    parts.append("[REFERENCES]")
    parts.append(
        'Reference images labeled on-image. "Character: XXX" for appearance, '
        '"Scene: XXX" for environment. Do not reproduce labels.'
    )

    # --- Character identity lines (same as A) ---
    for idx, char_id in enumerate(characters_visible, 1):
        char_data = next((c for c in characters_list if c.get("id") == char_id), None)
        if char_data:
            name_en = char_data.get("name_en", "") or char_data.get("name", "Unknown")
            name_zh = char_data.get("name", "")
            identity_line = build_identity_line_phase2(char_data)

            if name_zh and name_zh != name_en:
                parts.append(f"\n[CHARACTER {idx}: {name_en} ({name_zh})]")
            else:
                parts.append(f"\n[CHARACTER {idx}: {name_en}]")
            parts.append(identity_line)

    # --- Mood (compressed narrative context) ---
    lighting = shot.get("lighting", {})
    emotional_mood = lighting.get("mood", "")

    # Try to get scene atmosphere from storyboard context
    scene_atmosphere = ""
    # We don't have screenplay data in this test, so use a fallback
    scene_atmosphere = "peaceful and tender"  # Default for this story's atmosphere

    if emotional_mood:
        parts.append("")
        mood_line = f"[MOOD] {emotional_mood}."
        if scene_atmosphere:
            mood_line += f" Atmosphere: {scene_atmosphere}."
        parts.append(mood_line)

    # --- Direction (compressed global visual direction) ---
    color_grade = global_dir.get("color_grade", "neutral")
    overall_lighting = global_dir.get("overall_lighting", "natural")
    lens_style = global_dir.get("lens_style", "35mm")

    parts.append("")
    parts.append(f"[DIRECTION] Color: {color_grade} | Light: {overall_lighting} | Lens: {lens_style}")

    # --- Scene (same image_prompt as A) ---
    image_prompt = shot.get("image_prompt", "")
    parts.append("")
    parts.append("[SCENE]")
    parts.append(image_prompt)

    # --- Dialogue (same as A, if applicable) ---
    if use_native_text:
        text_overlay = shot.get("text_overlay", {})
        chars_visible = shot.get("character_direction", {}).get("characters_visible", [])

        dialogue_embed = build_dialogue_scene_embed(
            text_overlay,
            characters=characters_list,
            speaker_format='english',
            text_language='zh-CN',
            characters_in_scene=chars_visible
        )

        native_text_block = build_native_text_prompt(
            text_overlay,
            characters=characters_list,
            characters_in_scene=chars_visible
        )

        # Combine dialogue + text overlay
        text_parts = []
        if dialogue_embed:
            text_parts.append(dialogue_embed)
        if native_text_block:
            text_parts.append(native_text_block)

        if text_parts:
            parts.append("")
            parts.append("[DIALOGUE]")
            parts.append("\n".join(text_parts))

    # --- Constraints ---
    parts.append("")
    parts.append("[CONSTRAINTS] TEXT-FREE: Do not generate text unless requested above.")

    return "\n".join(parts)


# ============================================================================
# Main Test
# ============================================================================

async def run_test():
    start_time = time.time()

    # --- Create output directories ---
    for d in [OUTPUT_DIR, BLIND_DIR, PROMPTS_DIR, REFS_DIR]:
        os.makedirs(d, exist_ok=True)

    # --- Load test data ---
    print("=" * 60)
    print("PROMPT FORMAT A vs B' TEST")
    print("=" * 60)

    with open(os.path.join(DATA_DIR, "2_characters.json"), "r") as f:
        characters_data = json.load(f)

    with open(os.path.join(DATA_DIR, "4_storyboard.json"), "r") as f:
        storyboard_data = json.load(f)

    shots = storyboard_data["shots"][:NUM_SHOTS]
    print(f"\nLoaded {len(characters_data['characters'])} characters, {len(shots)} shots")

    # --- Initialize services ---
    image_gen = ImageGenerator()
    ref_manager = ReferenceImageManager()
    scene_ref_manager = SceneReferenceManager()

    project_style = ProjectStyleConfig(style_preset=STYLE_PRESET)

    # --- Step 1: Generate character reference images ---
    print("\n" + "=" * 60)
    print("STEP 1: Generating character reference images...")
    print("=" * 60)

    for char in characters_data["characters"]:
        char_name = char.get("name", "Unknown")
        print(f"\n  Generating references for {char_name}...")
        results = await ref_manager.generate_character_multi_refs(
            character=char,
            project_style=project_style,
            image_generator=image_gen,
            delay=3.0
        )

        for ref_type, result in results.items():
            if result.get("success"):
                print(f"    {ref_type}: OK ({result.get('generation_time_seconds', 0):.1f}s)")
            else:
                print(f"    {ref_type}: FAILED - {result.get('error', 'unknown')}")

        await asyncio.sleep(3.0)

    # Save references
    saved_refs = ref_manager.save_all_references(REFS_DIR)
    print(f"\n  Saved reference images to {REFS_DIR}")
    for char_id, refs in saved_refs.items():
        for ref_type, path in refs.items():
            print(f"    {char_id}_{ref_type}: {os.path.basename(path)}")

    ref_gen_time = time.time() - start_time
    print(f"\n  Reference generation time: {ref_gen_time:.1f}s")

    # --- Step 2: Generate A format images (current pipeline) ---
    print("\n" + "=" * 60)
    print("STEP 2: Generating A format images (current pipeline)...")
    print("=" * 60)

    a_results = {}
    a_start = time.time()

    for shot in shots:
        shot_id = shot["shot_id"]
        print(f"\n  Shot {shot_id} (A format)...")

        # Get character references for this shot
        chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
        char_refs = ref_manager.get_smart_references_for_scene(chars_visible, shot_type)

        # No scene references in this test (no location data generated)
        all_refs = char_refs

        result = await image_gen.generate_shot_image_phase2(
            shot=shot,
            storyboard=storyboard_data,
            characters=characters_data,
            style_preset=STYLE_PRESET,
            reference_images=all_refs,
            screenplay=None,
            aspect_ratio="2:3",
            use_native_text=True,
        )

        a_results[shot_id] = result

        if result.get("success"):
            gen_time = result.get("generation_time_seconds", 0)
            print(f"    OK ({gen_time:.1f}s)")

            # Save the A prompt
            # Reconstruct the prompt from prompt_package for saving
            prompt_package = result.get("prompt_package", {})
            prompt_text = _reconstruct_a_prompt_text(shot, storyboard_data, characters_data, STYLE_PRESET, all_refs)
            prompt_path = os.path.join(PROMPTS_DIR, f"shot_{shot_id:02d}_A.txt")
            with open(prompt_path, "w", encoding="utf-8") as f:
                f.write(prompt_text)
        else:
            print(f"    FAILED: {result.get('error', 'unknown')}")

        await asyncio.sleep(DELAY_BETWEEN_SHOTS)

    a_gen_time = time.time() - a_start
    a_success = sum(1 for r in a_results.values() if r.get("success"))
    print(f"\n  A format: {a_success}/{NUM_SHOTS} success, time: {a_gen_time:.1f}s")

    # --- Step 3: Generate B' format images ---
    print("\n" + "=" * 60)
    print("STEP 3: Generating B' format images (compressed labels)...")
    print("=" * 60)

    b_results = {}
    b_start = time.time()

    for shot in shots:
        shot_id = shot["shot_id"]
        print(f"\n  Shot {shot_id} (B' format)...")

        # Same reference images as A
        chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
        shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
        char_refs = ref_manager.get_smart_references_for_scene(chars_visible, shot_type)
        all_refs = char_refs

        # Build B' prompt
        b_prime_prompt = build_b_prime_prompt(
            shot=shot,
            storyboard=storyboard_data,
            characters=characters_data,
            style_preset=STYLE_PRESET,
            reference_images=all_refs,
            use_native_text=True,
        )

        # Save B' prompt
        prompt_path = os.path.join(PROMPTS_DIR, f"shot_{shot_id:02d}_B.txt")
        with open(prompt_path, "w", encoding="utf-8") as f:
            f.write(b_prime_prompt)

        # Call generate_image directly with the B' prompt + same reference images
        result = await image_gen.generate_image(
            prompt=b_prime_prompt,
            aspect_ratio="2:3",
            reference_images=all_refs,
        )

        # Add shot metadata
        if result.get("success"):
            result["shot_id"] = shot_id
            result["phase2"] = True

        b_results[shot_id] = result

        if result.get("success"):
            gen_time = result.get("generation_time_seconds", 0)
            print(f"    OK ({gen_time:.1f}s)")
        else:
            print(f"    FAILED: {result.get('error', 'unknown')}")

        await asyncio.sleep(DELAY_BETWEEN_SHOTS)

    b_gen_time = time.time() - b_start
    b_success = sum(1 for r in b_results.values() if r.get("success"))
    print(f"\n  B' format: {b_success}/{NUM_SHOTS} success, time: {b_gen_time:.1f}s")

    # --- Step 4: Blind output ---
    print("\n" + "=" * 60)
    print("STEP 4: Creating blind output...")
    print("=" * 60)

    blind_mapping = {}
    saved_count = 0

    for shot in shots:
        shot_id = shot["shot_id"]
        a_result = a_results.get(shot_id, {})
        b_result = b_results.get(shot_id, {})

        a_ok = a_result.get("success", False)
        b_ok = b_result.get("success", False)

        if not a_ok and not b_ok:
            print(f"  Shot {shot_id}: Both A and B' failed, skipping")
            blind_mapping[f"shot_{shot_id:02d}"] = {"X": "FAILED", "Y": "FAILED"}
            continue

        # Randomly assign X and Y
        if random.random() < 0.5:
            x_format, y_format = "A", "B'"
            x_result, y_result = a_result, b_result
        else:
            x_format, y_format = "B'", "A"
            x_result, y_result = b_result, a_result

        blind_mapping[f"shot_{shot_id:02d}"] = {
            "X": x_format,
            "Y": y_format,
        }

        # Save X
        if x_result.get("success") and x_result.get("pil_image"):
            x_path = os.path.join(BLIND_DIR, f"shot_{shot_id:02d}_X.png")
            x_result["pil_image"].save(x_path)
            saved_count += 1
            print(f"  shot_{shot_id:02d}_X.png saved ({x_format})")
        else:
            print(f"  shot_{shot_id:02d}_X.png SKIPPED (failed)")

        # Save Y
        if y_result.get("success") and y_result.get("pil_image"):
            y_path = os.path.join(BLIND_DIR, f"shot_{shot_id:02d}_Y.png")
            y_result["pil_image"].save(y_path)
            saved_count += 1
            print(f"  shot_{shot_id:02d}_Y.png saved ({y_format})")
        else:
            print(f"  shot_{shot_id:02d}_Y.png SKIPPED (failed)")

    # Save mapping (NOT in blind dir)
    mapping_path = os.path.join(OUTPUT_DIR, "blind_mapping.json")
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(blind_mapping, f, indent=2, ensure_ascii=False)
    print(f"\n  Mapping saved to {mapping_path}")

    # --- Summary ---
    total_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"  Reference generation: {ref_gen_time:.1f}s")
    print(f"  A format generation: {a_gen_time:.1f}s ({a_success}/{NUM_SHOTS} success)")
    print(f"  B' format generation: {b_gen_time:.1f}s ({b_success}/{NUM_SHOTS} success)")
    print(f"  Blind images saved: {saved_count}")
    print(f"  Prompt files: {NUM_SHOTS * 2}")
    print(f"")
    print(f"  Output directories:")
    print(f"    Blind images: {BLIND_DIR}")
    print(f"    Prompts: {PROMPTS_DIR}")
    print(f"    References: {REFS_DIR}")
    print(f"    Mapping: {mapping_path}")
    print(f"")

    # Estimate API cost
    # NB2 model: ~$0.02/image (rough estimate)
    total_images = a_success + b_success + len(characters_data["characters"]) * 2
    est_cost = total_images * 0.02
    print(f"  Estimated API cost: ~${est_cost:.2f} ({total_images} images @ ~$0.02/image)")

    return {
        "total_time": total_time,
        "a_success": a_success,
        "b_success": b_success,
        "saved_count": saved_count,
        "est_cost": est_cost,
    }


def _reconstruct_a_prompt_text(
    shot: dict,
    storyboard: dict,
    characters: dict,
    style_preset: str,
    reference_images: list,
) -> str:
    """
    Reconstruct the full A-format prompt text (same logic as generate_shot_image_phase2)
    for saving to file. This mirrors the assembly in image_generator.py L873-957.
    """
    prompt_builder = Phase2PromptBuilder(
        storyboard=storyboard,
        characters=characters,
        style_preset=style_preset,
    )

    char_direction = shot.get("character_direction", {})
    characters_in_shot = char_direction.get("characters_visible", [])
    char_refs_count = len(characters_in_shot) * 1
    total_refs = len(reference_images) if reference_images else 0
    scene_ref_count = max(0, total_refs - char_refs_count)

    prompt_package = prompt_builder.build_full_prompt(
        shot=shot,
        screenplay=None,
        include_system_instruction=True,
        scene_ref_count=scene_ref_count,
    )

    system_instruction = prompt_package.get("system_instruction", "")
    critical_header = prompt_package.get("critical_header", "")
    character_mapping = prompt_package.get("character_mapping", "")
    main_prompt = prompt_package.get("image_prompt", "")
    continuity_context = prompt_package.get("continuity_context", "")
    narrative_context = prompt_package.get("narrative_context", "")

    full_prompt_parts = []

    if critical_header:
        full_prompt_parts.append(critical_header)

    if character_mapping:
        full_prompt_parts.append(character_mapping)

    if narrative_context:
        full_prompt_parts.append(narrative_context)

    if system_instruction:
        full_prompt_parts.append(f"[GLOBAL STYLE DIRECTIVE]\n{system_instruction}")

    if continuity_context:
        full_prompt_parts.append(f"[CONTINUITY]\n{continuity_context}")

    # Dialogue embed
    text_overlay = shot.get("text_overlay", {})
    chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
    dialogue_embed = build_dialogue_scene_embed(
        text_overlay,
        characters=characters.get("characters", []),
        speaker_format='english',
        text_language='zh-CN',
        characters_in_scene=chars_visible,
    )

    if dialogue_embed:
        full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}\n{dialogue_embed}")
    else:
        full_prompt_parts.append(f"[SCENE DESCRIPTION]\n{main_prompt}")

    full_prompt = "\n\n".join(full_prompt_parts)

    # Apply style enforcer (same as pipeline)
    full_prompt = StyleEnforcer.enforce_prompt(full_prompt, style_preset, add_quality_suffix=False)

    # Color mode
    color_mode = shot.get("color_mode", "full_color")
    if color_mode == "grayscale":
        full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in GRAYSCALE, black and white."
    elif color_mode == "sepia":
        full_prompt += "\n\n[COLOR OVERRIDE] This shot MUST be in SEPIA TONE."

    # Native text (thought/narration)
    native_text_block = build_native_text_prompt(
        text_overlay,
        characters=characters.get("characters", []),
        characters_in_scene=chars_visible,
    )
    if native_text_block:
        full_prompt += "\n\n" + native_text_block

    return full_prompt


if __name__ == "__main__":
    result = asyncio.run(run_test())

    if result:
        print("\n" + "=" * 60)
        if result["a_success"] == NUM_SHOTS and result["b_success"] == NUM_SHOTS:
            print("ALL 20 IMAGES GENERATED SUCCESSFULLY")
        else:
            failed = (NUM_SHOTS - result["a_success"]) + (NUM_SHOTS - result["b_success"])
            print(f"COMPLETED WITH {failed} FAILURES")
        print("=" * 60)
