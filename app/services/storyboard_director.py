"""
Stage 4: StoryboardDirector

Phase 2.0 第四阶段 - 分镜脚本生成器（核心升级）
基于分场剧本和角色设计，生成具有专业镜头语言的分镜脚本，包含：
- 镜头信息 (camera: shot_size, angle, movement, lens, focus)
- 构图信息 (composition: subject_position, eye_line, leading_lines)
- 光影信息 (lighting: key_light, fill_light, rim_light, mood)
- 角色指导 (character_direction: position, expression, gesture)
- 专业image_prompt
"""

import asyncio
import json
import re
import time
import logging
from typing import Optional
import anthropic
from google import genai
from app.config import settings

logger = logging.getLogger("xuhua")

from app.prompts.storyboard_prompts import NARRATION_TO_VISUAL_EXTRACTION_RULES, COMIC_MODE_NARRATIVE_RULES


# T18: 场景道具连续性规则（同 NARRATION_TO_VISUAL_EXTRACTION_RULES 模式注入）
SCENE_PROP_CONTINUITY_RULES = """
═══════════════════════════════════════════════════════════
SCENE PROP CONTINUITY (IMPORTANT)
═══════════════════════════════════════════════════════════

When generating multiple shots within the SAME scene_id, you SHOULD maintain
consistent descriptions of key visible props and environmental details across
consecutive shots. This creates visual continuity for the reader.

## Rules:

1. PERSISTENT PROPS: If a shot establishes specific props on a shared surface
   (dishes on a table, items on a desk, objects in a room), subsequent shots
   in the same scene SHOULD describe those props in a consistent manner.
   Props do not vanish between shots unless the narrative explains why.

2. NARRATIVE-DRIVEN CHANGES ONLY: Props may change state ONLY when the story
   explicitly describes the change (e.g., "she finishes the soup" → bowl now
   empty; "he slams the book shut" → book now closed). Do not silently add
   or remove props between shots.

3. QUANTITY CONSISTENCY: If shot 1 describes "a table with 8 dishes",
   shot 2 in the same scene should NOT show an empty table or only 2 dishes
   — maintain approximate quantity unless consumption/removal is narrated.

4. FLEXIBILITY: You do NOT need to copy the exact prop list word-for-word.
   Different camera angles naturally show different portions of the scene.
   The goal is logical consistency, not verbatim repetition.

## Examples:

❌ BAD: Shot 1 "a table laden with 8 steaming dishes and a clay pot of soup"
        → Shot 3 (same scene) "the two characters sit at a bare wooden table"
        (Props vanished without narrative reason)

✅ GOOD: Shot 1 "a table laden with 8 steaming dishes and a clay pot of soup"
         → Shot 3 (same scene, close-up) "char_001 picks up chopsticks,
         several half-eaten dishes and the clay soup pot visible on the table behind"
         (Props persist, quantity roughly consistent, camera angle changed)

❌ BAD: Shot 2 "an open laptop and scattered papers on the desk"
        → Shot 4 (same scene) "char_002 types on a desktop computer at a clean desk"
        (Laptop changed to desktop, papers vanished)

✅ GOOD: Shot 2 "an open laptop and scattered papers on the desk"
         → Shot 4 (same scene) "char_002 leans toward the laptop screen,
         papers pushed to the side of the desk"
         (Same laptop, papers repositioned naturally)

═══════════════════════════════════════════════════════════
"""


# T27: 角色关系映射规则（P-S1 修复：跨Stage称谓混乱）
# 配合 T24 传入的 characters_overview 关系数据使用
CHARACTER_RELATIONSHIP_MAPPING_RULES = """
═══════════════════════════════════════════════════════════
CHARACTER RELATIONSHIP MAPPING (IMPORTANT)
═══════════════════════════════════════════════════════════

When generating text_overlay (dialogue and thought), you MUST use the CORRECT family
title/appellation for each character based on the CHARACTER RELATIONSHIPS data
provided above in the "CHARACTER RELATIONSHIPS" section.

## Rules:

1. STRICT TITLE MATCHING: Each character's chinese_text dialogue SHOULD use the
   family title that matches their actual role (e.g., if char_004 is "mother",
   narration and dialogue MUST call her "妈妈" — NOT "奶奶", "阿姨", or other titles).

2. PERSPECTIVE-AWARE TITLES: The title used depends on WHO is speaking/thinking:
   - A child calling their mother: "妈妈"
   - A grandchild calling their grandmother: "奶奶" / "外婆"
   - A son calling his father: "爸" / "爸爸"
   - Characters of the same generation: use given names

3. CROSS-SHOT CONSISTENCY: Once a title is established for a character in shot 1,
   ALL subsequent shots MUST use the same title for the same speaker-listener pair.
   Do NOT switch between "妈妈" and "慧兰" for the same character in the same scene.

4. TEXT_OVERLAY SELF-CHECK: Before finalizing each shot's text_overlay, verify:
   - Is the speaker using the correct title for the person they address?
   - Does the title match the CHARACTER RELATIONSHIPS data?
   - Is this title consistent with what was used in earlier shots?

═══════════════════════════════════════════════════════════
"""

# T27: 背景多样性规则（P-S3 修复：同场景连续shot背景单调）
BACKGROUND_VARIETY_RULES = """
═══════════════════════════════════════════════════════════
BACKGROUND VARIETY (IMPORTANT)
═══════════════════════════════════════════════════════════

When generating 3 or more consecutive shots in the SAME location (same scene_id),
you SHOULD describe DIFFERENT background focus areas across shots to avoid visual
monotony. Small spaces (kitchens, bedrooms, offices) are especially prone to
repetitive backgrounds.

## Rules:

1. SHIFT BACKGROUND FOCUS: Each shot in the same location SHOULD highlight a
   different portion or detail of the environment.
   ❌ BAD: Shot 1/2/3 all describe "warm kitchen with wooden cabinets"
   ✅ GOOD: Shot 1 "stove with a steaming pot, tiled backsplash"
            Shot 2 "window above the sink, afternoon light on hanging herbs"
            Shot 3 "refrigerator door covered with family photos, calendar on the wall"

2. VARY CAMERA ORIENTATION: Even in the same small room, rotate the implied
   camera direction — face different walls, corners, or angles.
   ❌ BAD: 3 shots all facing the same wall
   ✅ GOOD: Shot 1 faces the dining table, Shot 2 faces the window,
            Shot 3 looks toward the hallway entrance

3. USE ENVIRONMENTAL STORYTELLING: Each background shift SHOULD reveal new
   information about the characters or setting (family photos, bookshelf contents,
   weather outside the window, items on a shelf).

4. FLEXIBILITY: This rule applies to locations with 3+ shots. For locations with
   only 1-2 shots, normal background description is sufficient.

═══════════════════════════════════════════════════════════
"""

# T27: 室内纵深感强化规则（P-S4 修复：人物-背景比例不协调）
INTERIOR_SPATIAL_DEPTH_RULES = """
═══════════════════════════════════════════════════════════
INTERIOR SPATIAL DEPTH (IMPORTANT)
═══════════════════════════════════════════════════════════

For medium_shot and medium_close_up in INTERIOR scenes, you SHOULD include specific
spatial depth cues to prevent flat, portrait-like compositions where characters
appear pasted onto backgrounds.

## Rules:

1. DEPTH ANCHORING: Place at least one object BETWEEN the camera and the character
   (foreground), and at least one object BEHIND the character (background), to
   establish three-dimensional space.
   ❌ BAD: "char_001 sits at the dining table" (no depth cues)
   ✅ GOOD: "blurred edge of a rice bowl in the near foreground, char_001 sits at
            the dining table, the kitchen doorway and hanging calendar visible behind"

2. INTERIOR PERSPECTIVE LINES: Reference architectural elements that create
   depth — doorframes, hallways, window recesses, ceiling beams, floor tile
   patterns receding into distance.
   ❌ BAD: "two characters talk in the living room"
   ✅ GOOD: "two characters face each other across the coffee table, the long
            hallway stretches behind them toward a half-open bedroom door"

3. SCALE REFERENCE: Include objects of known size at different depths to help
   the viewer gauge spatial relationships — a chair in the foreground, characters
   in the midground, a bookshelf against the far wall.

4. AVOID FLAT COMPOSITION: Do NOT describe interior scenes as if characters are
   standing against a flat backdrop. Always imply room volume and depth.

═══════════════════════════════════════════════════════════
"""

# T35: 多人空间锚定规则（P-R7: 4人场景缺1人 + P-R10: 人物比例失调）
MULTI_CHARACTER_SPATIAL_ANCHORING_RULES = """
═══════════════════════════════════════════════════════════
MULTI-CHARACTER SPATIAL ANCHORING (IMPORTANT)
═══════════════════════════════════════════════════════════

When a shot contains 3 or more characters, you SHOULD follow these rules to ensure
every character is visible, properly scaled, and spatially grounded.

## Rules:

1. HEADCOUNT GUARANTEE: The image_prompt MUST explicitly state the total number of
   visible people (e.g., "four people gathered around the dining table"). Every
   character listed in characters_in_scene SHOULD be accounted for in the prompt
   with a distinct spatial position. Do NOT leave any character implied or off-screen
   unless the narrative specifically requires it.
   ❌ BAD: "the family sits at the table" (how many? who is where?)
   ✅ GOOD: "four people at the dining table: grandfather at the head, father and
            mother on opposite sides, granddaughter in the near-left seat"

2. FURNITURE-TO-BODY SCALE: Characters SHOULD be proportionally correct relative to
   furniture and environment objects. Seated characters' heads should be at chair-back
   height. Standing characters should be taller than table height. Children should be
   visibly shorter than adults. Elderly characters may be slightly hunched.
   ❌ BAD: "child and adult stand side by side" (no scale difference implied)
   ✅ GOOD: "the grandfather sits in the armchair, his head level with the chair back,
            the 8-year-old granddaughter stands beside him, her head barely reaching
            his shoulder"

3. ENVIRONMENT INTERACTION: Each character SHOULD have a physical interaction with the
   environment — holding an object, leaning on furniture, resting hands on a surface,
   or touching another character. Avoid floating or idle poses where characters stand
   stiffly with no spatial connection to their surroundings.
   ❌ BAD: "three people stand in the kitchen"
   ✅ GOOD: "mother stirs a pot at the stove, father leans against the counter holding
            a mug, daughter sits on the kitchen stool peeling an apple"

4. SPATIAL DISTRIBUTION: In group scenes (3+ characters), distribute characters across
   at least two depth planes (foreground + midground, or midground + background). Avoid
   lining up all characters in a single flat row at the same distance from camera.
   ❌ BAD: "four family members stand side by side facing the camera" (flat lineup)
   ✅ GOOD: "grandmother and granddaughter sit on the sofa in the midground, grandfather
            stands behind them resting his hand on the sofa back, father walks in from
            the hallway in the background carrying a tray"

5. OVERLAP AVOIDANCE: When characters are close together, use slight staggering or
   height variation so that no character is fully occluded by another. Partially
   overlapping is acceptable if faces remain visible.

═══════════════════════════════════════════════════════════
"""

# T34 Plan A: 镜头信息完整性规则（P-R6: 早期shot缺镜头信息）
CAMERA_INFORMATION_COMPLETENESS_RULE = """
═══════════════════════════════════════════════════════════
CAMERA INFORMATION IN IMAGE PROMPT (IMPORTANT)
═══════════════════════════════════════════════════════════

Every image_prompt SHOULD explicitly include the camera framing and angle as natural
English phrases. This helps the image generation model produce the intended composition.

## Rules:

1. SHOT SIZE IN PROMPT: The image_prompt SHOULD contain a phrase describing the shot size
   (e.g., "wide shot of...", "close-up of...", "medium shot showing..."). This should
   match the shot's `camera.shot_size` metadata.
   ❌ BAD: "char_001 sits at the dining table looking sad" (no framing info)
   ✅ GOOD: "medium shot of char_001 sitting at the dining table looking sad"

2. CAMERA ANGLE IN PROMPT: When the camera angle is NOT eye_level, the image_prompt
   SHOULD mention the angle perspective to guide composition.
   ❌ BAD: "char_001 stands alone on the rooftop" (shot metadata says high_angle but prompt doesn't reflect it)
   ✅ GOOD: "high-angle shot looking down at char_001 standing alone on the rooftop"

3. NATURAL INTEGRATION: Camera information should be woven into the description
   naturally, not appended as a technical tag.
   ❌ BAD: "char_001 walks through the rain. Shot size: medium_shot. Angle: low_angle."
   ✅ GOOD: "low-angle medium shot of char_001 walking through the rain, his silhouette framed against the stormy sky"

═══════════════════════════════════════════════════════════
"""

# 专业摄影知识库
CINEMATOGRAPHY_GUIDE = """
## 镜头语言指南

### 景别（Shot Size）及其情感含义
- extreme_wide_shot (EWS): 强调环境，人物渺小，适合开场建立场景或表达孤独/渺小
- wide_shot (WS): 展示人物与环境关系，适合动作场景、空间建立
- medium_wide_shot (MWS/Cowboy): 人物膝盖以上，适合走动、多人对话场景
- medium_shot (MS): 腰部以上，标准对话景别，平衡人物与环境
- medium_close_up (MCU): 胸部以上，强调表情同时保留手势
- close_up (CU): 面部特写，强调情绪、反应
- extreme_close_up (ECU): 眼睛或细节特写，极度强调情感或重要道具

### 机位角度（Camera Angle）及其心理暗示
- birds_eye: 俯瞰，上帝视角，命运感、全知感
- high_angle: 俯拍，被摄者显得弱小、脆弱、被压迫
- eye_level: 平视，中性，观众与角色平等
- low_angle: 仰拍，被摄者显得强大、威严、有力量
- worms_eye: 极低角度，戏剧化、不稳定感、超现实

### 镜头运动（Camera Movement）
- static: 固定镜头，稳定、客观
- pan_left/pan_right: 水平摇摄，跟随或揭示
- tilt_up/tilt_down: 垂直摇摄，揭示高度或反应
- dolly_in: 推进，增加紧迫感、亲密感
- dolly_out: 拉远，揭示环境、孤立感
- tracking: 跟拍，跟随角色移动

### 构图原则
- rule_of_thirds: 三分法，主体放在三分线交点
- look_room: 角色看向的方向留出空间
- leading_lines: 利用场景中的线条引导观众视线
- frame_within_frame: 画中画，利用门窗等创造层次
- negative_space: 大面积留白强调孤独或重要性
- symmetrical: 对称构图，正式、稳定、仪式感

### 光影情绪
- high_key: 明亮均匀，积极向上、轻松
- low_key: 强烈明暗对比，戏剧性、神秘、紧张
- side_light: 侧光，强调轮廓和质感、分裂感
- backlight: 逆光，剪影效果，神秘或浪漫
- practical_lights: 场景中的实际光源（路灯、霓虹灯）增加真实感
- motivated_light: 有来源的光线，增强可信度
"""


class StoryboardDirector:
    """
    分镜脚本生成器

    输入: screenplay.json + characters.json + visual_tone
    输出: storyboard.json

    模型优先级: Claude Sonnet 4.6 (主) → Gemini 3 Flash (备用)
    """

    def __init__(self):
        # 主模型: Claude Sonnet 4.6
        self.claude_client = None
        self.claude_model = "claude-sonnet-4-6"
        if settings.ANTHROPIC_API_KEY:
            self.claude_client = anthropic.Anthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )

        # 备用模型: Gemini 3 Flash
        self.gemini_client = None
        self.gemini_model = "gemini-3.1-flash-lite-preview"
        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    async def direct(
        self,
        screenplay: dict,
        characters: dict,
        visual_tone: dict,
        style_preset: str = "anime",
        characters_overview: list = None,
        family_relationships: list = None,
        progress_callback=None,
    ) -> dict:
        """
        生成分镜脚本（按scene分批生成，解决LLM输出不完整问题）

        Args:
            screenplay: Stage 3生成的分场剧本
            characters: Stage 2生成的角色设计
            visual_tone: Stage 1大纲中的视觉风调
            style_preset: 风格预设
            characters_overview: Stage 1大纲中的角色概述（含关系信息）
            family_relationships: Stage 1大纲中的角色间关系映射

        Returns:
            storyboard dict
        """
        scenes = screenplay.get("scenes", [])
        total_beats = sum(len(s.get("action_beats", [])) for s in scenes)

        print(f"[StoryboardDirector] 生成分镜脚本（按scene分批）...")
        print(f"  场景数: {len(scenes)}")
        print(f"  动作节拍: {total_beats}个")
        print(f"  风格: {style_preset}")
        logger.info(f"[StoryboardDirector] 开始生成分镜脚本")
        logger.info(f"  场景数: {len(scenes)}, 动作节拍: {total_beats}, 风格: {style_preset}")
        stage_start = time.time()

        # B-2: 并行生成 — Scene 1 先行获取 global_visual_direction，其余并行
        all_shots = []
        global_visual_direction = None
        shot_id_counter = 1

        # 过滤掉无 action_beats 的 scene
        valid_scenes = []
        for scene_idx, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", scene_idx + 1)
            beats = scene.get("action_beats", [])
            if not beats:
                print(f"  ⚠️ Scene {scene_id} 无action_beats，跳过")
                continue
            valid_scenes.append((scene_idx, scene))

        if not valid_scenes:
            raise ValueError("无法生成任何shots（所有scene无action_beats）")

        # Step 1: 生成 Scene 1（获取 global_visual_direction）
        first_scene_idx, first_scene = valid_scenes[0]
        first_scene_id = first_scene.get("scene_id", first_scene_idx + 1)
        first_beats = first_scene.get("action_beats", [])
        print(f"  生成 Scene {first_scene_id} ({len(first_beats)} beats)...", end=" ")

        first_shots, gvd = await self._generate_scene_shots(
            scene=first_scene,
            scene_idx=first_scene_idx,
            characters=characters,
            visual_tone=visual_tone,
            style_preset=style_preset,
            shot_id_start=shot_id_counter,
            characters_overview=characters_overview,
            family_relationships=family_relationships
        )

        if first_shots:
            for shot in first_shots:
                shot["shot_id"] = shot_id_counter
                shot_id_counter += 1
            all_shots.extend(first_shots)
            print(f"✅ {len(first_shots)} shots")
            if gvd:
                global_visual_direction = gvd
        else:
            print(f"❌ 失败")

        # B-4: Scene 进度回调（Scene 1 完成）
        if progress_callback and len(valid_scenes) > 0:
            p = 35 + int(1 / len(valid_scenes) * 30)
            await progress_callback("storyboard", p, f"分镜生成中 (Scene 1/{len(valid_scenes)})...")

        # Step 2: Scene 2+ 并行（Semaphore 限制并发数）
        remaining_scenes = valid_scenes[1:]
        if remaining_scenes:
            semaphore = asyncio.Semaphore(3)  # RB-3: 降低并发避免 529 overloaded

            async def _generate_with_semaphore(scene_idx: int, scene: dict) -> tuple:
                async with semaphore:
                    scene_id = scene.get("scene_id", scene_idx + 1)
                    beats = scene.get("action_beats", [])
                    print(f"  生成 Scene {scene_id} ({len(beats)} beats)...", end=" ")
                    shots, _ = await self._generate_scene_shots(
                        scene=scene,
                        scene_idx=scene_idx,
                        characters=characters,
                        visual_tone=visual_tone,
                        style_preset=style_preset,
                        shot_id_start=1,  # 临时值，后面统一重编号
                        characters_overview=characters_overview,
                        family_relationships=family_relationships
                    )
                    if shots:
                        print(f"✅ {len(shots)} shots")
                    else:
                        print(f"❌ 失败")
                    return (scene_idx, shots)

            # 并行执行
            tasks = [
                _generate_with_semaphore(si, sc) for si, sc in remaining_scenes
            ]
            parallel_results = await asyncio.gather(*tasks)

            # 按 scene_idx 排序，保证顺序正确
            parallel_results.sort(key=lambda x: x[0])

            # 统一重编号 shot_id 并合并结果
            for i, (scene_idx, shots) in enumerate(parallel_results):
                if shots:
                    for shot in shots:
                        shot["shot_id"] = shot_id_counter
                        shot_id_counter += 1
                    all_shots.extend(shots)

                # B-4: Scene 进度回调（每完成一个 scene）
                if progress_callback:
                    completed = i + 2  # +2 因为 Scene 1 已完成
                    p = 35 + int(completed / len(valid_scenes) * 30)
                    await progress_callback(
                        "storyboard", p,
                        f"分镜生成中 (Scene {completed}/{len(valid_scenes)})..."
                    )

        if not all_shots:
            raise ValueError("无法生成任何shots")

        total_duration = sum(s.get("estimated_duration", 5) for s in all_shots)

        stage_elapsed = time.time() - stage_start
        print(f"[StoryboardDirector] ✅ 分镜生成完成")
        print(f"  总镜头数: {len(all_shots)}")
        print(f"  预计时长: {total_duration}秒 ({total_duration/60:.1f}分钟)")
        logger.info(f"[StoryboardDirector] ✅ 分镜生成完成 (总耗时 {stage_elapsed:.1f}s)")
        logger.info(f"  总镜头数: {len(all_shots)}, 预计时长: {total_duration}s")

        storyboard = {
            "global_visual_direction": global_visual_direction or {
                "style_enforcement": f"{style_preset}_cinematic",
                "aspect_ratio": "2:3",
                "color_grade": "neutral",
                "overall_lighting": "natural",
                "lens_style": "35mm"
            },
            "shots": all_shots,
            "total_shots": len(all_shots),
            "total_duration_seconds": total_duration,
            "shot_continuity_notes": []
        }

        # T5+T7: 验证 + speaker-visibility 校验 + text_type 分布检查
        self._validate_storyboard(storyboard, characters=characters)
        self._rebalance_text_types(storyboard)

        return storyboard

    async def _generate_scene_shots(
        self,
        scene: dict,
        scene_idx: int,
        characters: dict,
        visual_tone: dict,
        style_preset: str,
        shot_id_start: int,
        characters_overview: list = None,
        family_relationships: list = None
    ) -> tuple:
        """为单个scene生成shots"""
        max_attempts = 2

        for attempt in range(max_attempts):
            prompt = self._build_scene_prompt(
                scene=scene,
                characters=characters,
                visual_tone=visual_tone,
                style_preset=style_preset,
                shot_id_start=shot_id_start,
                characters_overview=characters_overview,
                family_relationships=family_relationships
            )

            try:
                # DEBUG: 保存第一个scene的prompt
                if scene_idx == 0 and attempt == 0:
                    with open("forclaudeweb/stage4_actual_prompt.txt", "w", encoding="utf-8") as f:
                        f.write(prompt)

                content = await self._call_llm_with_retry(prompt, max_tokens=16384)

                # DEBUG: 保存第一个scene的响应
                if scene_idx == 0 and attempt == 0:
                    with open("forclaudeweb/stage4_raw_response.txt", "w", encoding="utf-8") as f:
                        f.write(f"\n=== Raw Response ===\n\n")
                        f.write(content)

                result = self._extract_json(content)

                if result:
                    shots = result.get("shots", [])
                    gvd = result.get("global_visual_direction")

                    # 验证每个shot
                    valid_shots = []
                    for shot in shots:
                        if "image_prompt" in shot:
                            # 设置默认值
                            if "camera" not in shot:
                                shot["camera"] = {"shot_size": "medium_shot", "angle": "eye_level", "movement": "static"}
                            if "estimated_duration" not in shot:
                                shot["estimated_duration"] = 5.0
                            valid_shots.append(shot)

                    if valid_shots:
                        # 检查image_prompt质量
                        for shot in valid_shots:
                            self._check_prompt_quality(shot)
                        return valid_shots, gvd

            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"(error: {e})", end=" ")

        return [], None

    async def _call_llm_with_retry(self, prompt: str, max_tokens: int = 16384) -> str:
        """
        RB-3: 带指数退避重试的 LLM 调用，529 特殊处理。

        - 非 529 错误: 退避 2s, 4s，最多 2 次重试（3 次尝试）
        - 529 overloaded: 退避 10s, 20s, 40s，最多 3 次重试（4 次尝试）
        """
        last_error = None
        is_529 = False
        max_retries = 3  # 默认非 529: 3 次尝试
        llm_start = time.time()

        for retry in range(4):  # 最多 4 次尝试（529 场景）
            if retry > 0:
                if is_529:
                    wait = 10 * (2 ** (retry - 1))  # 10s, 20s, 40s
                    print(f"    [RB-3] 529 overloaded 重试 {retry}/3，等待 {wait}s...")
                    logger.warning(f"[StoryboardDirector] ⚠️ 529 overloaded 重试 {retry}/3，等待 {wait}s")
                else:
                    if retry > 2:
                        break  # 非 529 最多 3 次尝试
                    wait = 2 ** retry  # 2s, 4s
                    print(f"    [RB-3] LLM 重试 {retry}/2，等待 {wait}s...")
                    logger.warning(f"[StoryboardDirector] ⚠️ LLM 重试 {retry}/2，等待 {wait}s, 上次错误: {last_error}")
                await asyncio.sleep(wait)

            try:
                content = None
                is_529 = False  # 重置

                # 优先使用 Claude Sonnet 4.6
                if self.claude_client:
                    try:
                        call_start = time.time()
                        response = self.claude_client.messages.create(
                            model=self.claude_model,
                            max_tokens=max_tokens,
                            temperature=0.8,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        content = response.content[0].text
                        call_elapsed = time.time() - call_start
                        logger.info(f"[StoryboardDirector] Claude 响应: {len(content)} chars, 耗时 {call_elapsed:.1f}s")
                    except Exception as ce:
                        last_error = ce
                        # 检测 529 状态码
                        error_str = str(ce)
                        if '529' in error_str or 'overloaded' in error_str.lower():
                            is_529 = True
                            max_retries = 4
                            print(f"    [RB-3] ⚠️ Claude 529 overloaded")
                            logger.warning(f"[StoryboardDirector] ⚠️ Claude 529 overloaded")
                        if hasattr(ce, 'status_code') and ce.status_code == 529:
                            is_529 = True
                            max_retries = 4

                # Fallback 到 Gemini 3 Flash
                if content is None and self.gemini_client:
                    try:
                        call_start = time.time()
                        response = await self.gemini_client.aio.models.generate_content(
                            model=self.gemini_model,
                            contents=prompt,
                            config={"max_output_tokens": max_tokens, "temperature": 0.8}
                        )
                        content = response.text
                        call_elapsed = time.time() - call_start
                        logger.info(f"[StoryboardDirector] Gemini 响应: {len(content)} chars, 耗时 {call_elapsed:.1f}s")
                    except Exception as ge:
                        last_error = ge
                        error_str = str(ge)
                        if '529' in error_str or 'overloaded' in error_str.lower():
                            is_529 = True
                            max_retries = 4

                if content is not None:
                    return content

            except Exception as e:
                last_error = e

            # 非 529 且已超出重试次数
            if not is_529 and retry >= 2:
                break

        # 所有重试都失败
        total_elapsed = time.time() - llm_start
        logger.error(f"[StoryboardDirector] ❌ LLM 调用失败 ({retry + 1} 次尝试, 总耗时 {total_elapsed:.1f}s): {last_error}")
        raise ValueError(f"LLM 调用失败（{retry + 1} 次尝试）: {last_error}")

    def _check_prompt_quality(self, shot: dict) -> None:
        """检查单个shot的image_prompt质量"""
        prompt = shot.get("image_prompt", "").lower()

        # 扩展的关键词列表，减少误报
        quality_markers = {
            "camera": [
                # 景别
                "shot", "close-up", "closeup", "wide", "medium", "extreme", "full",
                "establishing", "insert", "cutaway", "pov", "over-the-shoulder",
                # 角度
                "angle", "high angle", "low angle", "eye level", "dutch", "bird's eye",
                "worm's eye", "overhead", "tilted",
                # 镜头技术
                "lens", "focus", "depth of field", "bokeh", "shallow", "deep focus",
                "35mm", "50mm", "telephoto", "wide-angle",
                # 构图
                "composition", "framing", "foreground", "background", "midground",
                "rule of thirds", "centered", "negative space", "symmetry"
            ],
            "lighting": [
                # 光源
                "light", "lighting", "sunlight", "moonlight", "neon", "streetlight",
                "ambient", "backlight", "rim light", "fill light", "key light",
                # 光影效果
                "shadow", "shadows", "silhouette", "highlight", "contrast",
                "chiaroscuro", "halo", "glow", "reflection", "reflections",
                # 氛围词
                "mood", "moody", "atmosphere", "atmospheric", "dramatic",
                "cinematic", "ethereal", "dreamy", "gritty", "noir",
                # 色调
                "warm", "cold", "cool", "golden hour", "blue hour",
                "foggy", "misty", "hazy", "diffused", "harsh", "soft light"
            ],
            "character": [
                # 表情
                "expression", "face", "facial", "eyes", "gaze", "look", "stare",
                "smile", "frown", "tears", "crying", "laughing", "scowl",
                "worried", "anxious", "exhausted", "weary", "surprised",
                # 姿态
                "posture", "pose", "stance", "standing", "sitting", "leaning",
                "crouching", "squatting", "slouched", "upright",
                # 动作/手势
                "gesture", "gesturing", "reaching", "holding", "gripping",
                "pointing", "waving", "walking", "running", "turning",
                # 服装（核心）
                "wearing", "dressed", "outfit", "clothes", "clothing",
                " in a ", " in an ", " in his ", " in her ",
                "shirt", "pants", "dress", "jacket", "coat", "sweater",
                "vest", "tie", "skirt", "jeans", "shoes", "boots",
                # 配饰
                "glasses", "watch", "bag", "briefcase", "umbrella", "hat",
                "earphones", "necklace", "ring", "scarf"
            ]
        }

        missing = []
        for category, keywords in quality_markers.items():
            if not any(kw in prompt for kw in keywords):
                missing.append(category)

        # 只在缺少多个元素时警告
        if len(missing) >= 2:
            shot["_quality_warning"] = missing

    def _build_scene_prompt(
        self,
        scene: dict,
        characters: dict,
        visual_tone: dict,
        style_preset: str,
        shot_id_start: int,
        characters_overview: list = None,
        family_relationships: list = None
    ) -> str:
        """为单个scene构建prompt"""
        scene_id = scene.get("scene_id", 1)
        beats = scene.get("action_beats", [])
        num_beats = len(beats)

        # 格式化beats列表
        beats_list = []
        for i, beat in enumerate(beats):
            beat_id = beat.get("beat_id", f"{scene_id}{chr(97+i)}")
            action = beat.get("action", "")[:50]
            beats_list.append(f"  Shot {shot_id_start + i}: Beat {beat_id} - \"{action}...\"")
        beats_str = "\n".join(beats_list)

        # 简化角色信息
        chars_simplified = []
        for char in characters.get("characters", []):
            chars_simplified.append({
                "id": char.get("id"),
                "name": char.get("name"),
                "clothing_summary": f"{char.get('clothing', {}).get('top', '')}, {char.get('clothing', {}).get('bottom', '')}",
            })
        characters_json = json.dumps(chars_simplified, ensure_ascii=False, indent=2)

        scene_json = json.dumps({
            "scene_id": scene_id,
            "scene_heading": scene.get("scene_heading", ""),
            "atmosphere": scene.get("atmosphere", {}),
            "characters_in_scene": scene.get("characters_in_scene", []),
            "action_beats": beats,
            "dialogue_beats": scene.get("dialogue_beats", []),
            "narration": scene.get("narration", "")
        }, ensure_ascii=False, indent=2)

        # T24: 构建角色关系表（PM Code Review Fix: 修正字段名匹配 Stage 1 输出）
        char_relationships_block = ""
        if characters_overview:
            rel_lines = []
            for idx, co in enumerate(characters_overview):
                # Stage 1 输出字段: name_suggestion, age_range, family_role, archetype
                name = co.get("name_suggestion", co.get("name", ""))
                age = co.get("age_range", "")
                family_role = co.get("family_role", "")
                archetype = co.get("archetype", "")
                # 用 name 作为标识（Stage 1 无 char_id，Stage 2 才分配）
                label = name or f"char_{idx + 1:03d}"
                if name:
                    parts = [label]
                    if age:
                        parts.append(age)
                    if family_role and family_role != "none":
                        parts.append(family_role)
                    elif archetype:
                        parts.append(archetype)
                    rel_lines.append(f"- {', '.join(parts)}")

            # 追加顶层 family_relationships（T25 新增的角色间关系映射）
            fr_lines = []
            if family_relationships:
                for fr in family_relationships:
                    fr_from = fr.get("from", "")
                    fr_to = fr.get("to", "")
                    fr_rel = fr.get("relationship", "")
                    if fr_from and fr_to and fr_rel:
                        fr_lines.append(f"- {fr_from} → {fr_to}: {fr_rel}")

            if rel_lines:
                block_parts = [
                    "\n## CHARACTER RELATIONSHIPS (use to ensure correct family titles in text_overlay and interpersonal dynamics)\n",
                    "### Characters:",
                    *rel_lines
                ]
                if fr_lines:
                    block_parts.append("\n### Family Relationships:")
                    block_parts.extend(fr_lines)
                block_parts.append("")
                char_relationships_block = "\n".join(block_parts)

        return f"""Generate {num_beats} shots for Scene {scene_id}.

Required shots (one shot per beat):
{beats_str}

Scene data:
{scene_json}

Character data:
{characters_json}
{char_relationships_block}
{NARRATION_TO_VISUAL_EXTRACTION_RULES}

{COMIC_MODE_NARRATIVE_RULES}

## IMAGE PROMPT QUALITY REQUIREMENTS (MANDATORY)

### 1. Each character MUST have specific actions (NO vague descriptions)
❌ BAD: "char_001, char_002 are standing together"
✅ GOOD: "char_001 is rubbing his temples with his right hand, char_002 sits hunched on the bench clutching her knees"

### 2. Each character MUST have explicit gaze direction
❌ BAD: "avoiding eye contact" / "looking away"
✅ GOOD: "char_001 stares blankly down at his wet shoes, char_002 nervously glances sideways toward the empty road"

### 3. Characters MUST physically interact with environment (rain = wet characters)
❌ BAD: "Raindrops are visible in the air"
✅ GOOD: "Rain has soaked char_001's white shirt until it clings to his shoulders, water streams down his face"

### 4. Multi-character scenes MUST describe spatial relationships
❌ BAD: "standing at a distance from each other"
✅ GOOD: "char_001 stands at the far left near the signpost, char_002 curls up in the center of the bench"

### 5. Emotions MUST be shown through specific body language
❌ BAD: "looking exhausted"
✅ GOOD: "his shoulders sag under an invisible weight, dark circles hollow out his eyes, his tie hangs loose"

### 6. STRICT CHARACTER COUNT — NO EXTRA PEOPLE (CRITICAL)
Each image_prompt MUST depict EXACTLY the characters listed in characters_in_scene — NO ONE ELSE.
- State the exact count: "EXACTLY 2 characters in this scene"
- FORBIDDEN: bystanders, extras, crowd, background figures, passersby, waiters, strangers, onlookers, silhouettes of other people
- FORBIDDEN language: "blurred forms of other men/people", "other diners in the background", "busy restaurant with patrons"
- Empty chairs, empty tables, empty seats MUST remain empty — do NOT fill them with unnamed figures
- If the scene is a public place (restaurant, park, street), describe ONLY the named characters + environment/furniture/props — NEVER add ambient human figures
❌ BAD: "the two friends sit at a table, blurred forms of other diners visible in the background"
✅ GOOD: "EXACTLY 2 characters in this scene. The two friends sit at a table, empty chairs and warm pendant lights fill the rest of the restaurant"

### 7. OBJECT PHYSICAL PLAUSIBILITY ON SHARED SURFACES (CRITICAL)
When multiple objects sit on the same surface (table, desk, counter, shelf, floor), each object MUST have a distinct spatial anchor. Objects MUST NOT overlap or occupy the same position.
- Use explicit placement words: "at the near edge", "at the far left corner", "beside the plate", "to the right of the cup"
- FORBIDDEN vague spatial words when multiple objects share a surface: "among", "around it", "surrounded by", "in the midst of"
- Each object needs its own non-overlapping zone on the surface
❌ BAD: "a smartphone glows at the table's centre, around it a plate of braised pork and wine cups"
✅ GOOD: "a smartphone rests at the near edge of the table in front of char_001, a plate of braised pork sits at the centre, two wine cups stand at the far side"
❌ BAD: "books and laptop and coffee mug scattered on the desk"
✅ GOOD: "an open laptop at the desk's centre, a coffee mug at the right edge, three stacked books at the far left corner"

### 8. MULTI-CHARACTER LIMB INTERACTION LIMITS (CRITICAL)
At most 2 characters' hands/arms may actively interact with the SAME object in one shot. If 3+ characters need to touch the same object, use ONE of these alternatives:
- Split into sequential shots (each showing 1-2 characters interacting)
- Use a reaction shot (close-up of the object, then cut to characters' faces reacting)
- Show only 1-2 characters' hands in sharp focus, others' hands hidden or out of frame
- FORBIDDEN: 3+ pairs of hands converging on the same point/object in one image
❌ BAD: "three pairs of chopsticks enter frame from three directions, their tips converging on the same cluster of dumplings"
✅ GOOD: "char_001 picks up a dumpling with chopsticks, char_002's hand rests on the table holding a rice bowl, char_003 is visible in the background raising a cup"
❌ BAD: "all four hands reach for the same document on the table"
✅ GOOD: "close-up of char_001's hand sliding the document across the table toward char_002, whose fingers hover at the paper's edge"

### 9. SINGLE-CHARACTER HAND ACTION LIMIT
Each character may perform AT MOST ONE active hand/arm action per shot. If the narration describes multiple hand actions for one character, choose the most dramatically important one. Other actions can be implied or shown in a subsequent shot.
❌ BAD: "char_001 wipes his cheek with the back of his hand while reaching out to push the glass door"
✅ GOOD: "char_001 pushes the glass door open with one hand, rain dripping from his face"

### 10. BACK-VIEW / HIGH-ANGLE CHARACTER CONSISTENCY (IMPORTANT)
When a shot uses back-view, over-the-shoulder, bird's-eye, or high-angle camera looking DOWN at characters:
- REINFORCE clothing with EXACT color names and garment types (not "her top" but "sage-green cotton T-shirt")
- REINFORCE hair with EXACT color and style ("jet-black shoulder-length straight hair", not "her hair")
- Add explicit note: "Even viewed from behind/above, [character_name]'s [specific_color] [specific_garment] must remain clearly identifiable and match the reference image."
This ensures character recognition even when face is not visible.
❌ BAD: "char_001 walks away from camera in her top and jeans"
✅ GOOD: "char_001 walks away from camera in her sage-green cotton T-shirt and dark-blue denim jeans, jet-black shoulder-length straight hair swaying. Even viewed from behind, her sage-green T-shirt must remain clearly identifiable and match the reference image."

### 11. OFF-SCREEN CHARACTER PHYSICAL CONTACT (CRITICAL)
When a character in characters_visible interacts with a character who is NOT in characters_visible (off-screen):
- FORBIDDEN: describing direct physical contact between the visible character and the off-screen character
  ❌ "His right arm is extended forward, pulled by Xiaohe's grip off-screen left"
  ❌ "She holds hands with someone outside the frame"
- REQUIRED: show the visible character's INDEPENDENT body language that implies the interaction
  ✅ "His right arm reaches forward toward off-frame left, fingers open in a beckoning gesture"
  ✅ "She extends her hand toward the left edge of the frame"
- Reason: image generation models render invisible characters' body parts as floating/disconnected limbs
- This rule does NOT apply to interactions with objects or environment (reaching for a door, picking up items)

### 12. SPATIAL DIRECTION SELF-CONSISTENCY CHECK (IMPORTANT)
Before finalizing each shot's image_prompt, verify that camera_angle, character actions, and spatial descriptions form a coherent picture:
- If camera faces a character's FRONT → character should NOT be described as "walking away from camera" or "trailing behind"
- If character is "leading the group, walking ahead" → camera should show their BACK or SIDE, not their FACE
- If character is "at the rear of the group" → they should be further from camera or partially occluded, not centered in foreground
❌ CONTRADICTORY: camera_angle "eye level front-facing" + action "mom trails at the rear while family walks ahead"
  (This places mom in the foreground facing camera, but the family walks away in the background — spatially impossible if she's trailing behind them)
✅ CONSISTENT: camera_angle "low angle from behind" + action "mom trails at the rear while family walks ahead"
  (Camera behind the group, mom closest to camera, family ahead — spatially coherent)

## NARRATIVE VISUAL PROPS (MANDATORY)

Every image_prompt MUST include at least one plot-relevant prop or environmental detail that conveys story information visually:
❌ BAD: "two characters arguing in a living room"
✅ GOOD: "two characters arguing in a living room, a civil service exam registration form crumpled on the table, an open laptop showing job listings"
❌ BAD: "character sitting alone in bedroom"
✅ GOOD: "character sitting alone in bedroom, a half-packed suitcase open on the floor, plane tickets pinned on the bulletin board"

Props should tell the story even if the viewer cannot read the text overlay. The viewer should understand WHAT the conflict is about from the visual elements alone.

{SCENE_PROP_CONTINUITY_RULES}

{CHARACTER_RELATIONSHIP_MAPPING_RULES}

{BACKGROUND_VARIETY_RULES}

{MULTI_CHARACTER_SPATIAL_ANCHORING_RULES}

## SPATIAL DEPTH RULES (MANDATORY)

For medium_shot, medium_close_up, close_up: AT LEAST 30% of the frame must show visible background/environment.
❌ BAD: "extreme close-up of face filling entire frame with no background"
✅ GOOD: "close-up of her face, tears glistening, the blurred warm glow of the café behind her, shelves of books visible over her shoulder"

Use foreground objects (blurred cup, door frame, rain streaks) to create depth layers.
Aim for at least 2 depth layers per shot; 3 layers for emotional beats.

{INTERIOR_SPATIAL_DEPTH_RULES}

## SHOT TRANSITION RULES (MANDATORY — between consecutive shots in the same scene)

### 30-Degree Rule
Adjacent shots in the same scene MUST change camera angle by at least 30 degrees. Cutting between two nearly identical angles creates a jarring jump cut.

### Shot Size Variation
No more than 2 consecutive shots may use the same shot_size. After 2 shots of the same size, the 3rd MUST change.

### Camera Angle Variation
Do NOT default every shot to eye_level. Choose angle based on narrative intent:
- low_angle: empowerment, dominance, threat
- high_angle: vulnerability, isolation, overview
- eye_level: neutral, conversation, equality
- dutch_angle: disorientation, tension (use sparingly)

### Composition Variation
Alternate subject_position across shots: left_third → center → right_third. Avoid 3+ consecutive shots with the same subject_position.

### Lens & Focal Length
Match focal_length to shot_size for natural perspective:
- wide_shot / establishing: 24mm-35mm (environmental context)
- medium_shot / medium_wide: 35mm-50mm (balanced)
- close_up / medium_close_up: 85mm (portrait compression, background separation)
- extreme_close_up: 100mm-135mm (detail isolation)

{CAMERA_INFORMATION_COMPLETENESS_RULE}

## TEXT OVERLAY MAPPING RULES (MANDATORY)

For each shot, generate a `text_overlay` field by mapping from the scene's `dialogue_beats`:

### Mapping Logic:
1. Match each shot's action_beat_id to corresponding dialogue_beats (by beat_id prefix, e.g. beat "1a" matches "1a_dialogue", "1a_thought")
2. Use the dialogue_beat's `type` field: "dialogue" → text_type="dialogue", "thought" → text_type="thought"
3. Beat has BOTH dialogue AND thought beats → text_type="dialogue_with_thought", chinese_text=mixed list
4. Beat has NO matching dialogue_beat → check emotional_note: character feeling/realization → text_type="thought", pure action/environment → text_type="narration"
5. Only use text_type="none" if the beat truly has zero text content (rare)

### THOUGHT GENERATION RULE (CRITICAL):
When a beat has NO dialogue_beat match, do NOT default to narration.
Check the beat's emotional_note:
- Character internal state/feeling/realization → text_type="thought", create inner monologue
- Pure external action/environment description → text_type="narration"
**Prefer thought over narration.** narration should be the last resort.

### SPEAKER VISIBILITY RULE (MANDATORY - COMIC MEDIUM):
If text_type is "dialogue", EVERY speaker in chinese_text MUST appear in that shot's characters_visible.
Comics have NO audio channel — readers attribute bubbles to the most prominent visible character.
- Single-character reaction shot → use "thought" or "narration", NOT "dialogue"
- Multi-speaker dialogue → ALL speakers must be in characters_visible
- Do NOT borrow dialogue from other beats to fill the distribution target

### Distribution Target:
- dialogue: ≥60% of shots (stories are driven by conversation)
- thought: 10-20%
- narration: ≤15%
- none: ≤5% (purely visual, use sparingly)

### SELF-CHECK (before output):
Count your text_type distribution across all shots. If narration > 15%, convert some to thought (use emotional_note to create inner monologue). If thought < 10%, create thought content for beats with strong emotional_note.

### speaker_position:
- Match to the speaking character's position in composition.subject_position
- "left"/"right" for dialogue, "bottom" for narration/thought, "center" for centered text

### chinese_text Format:
- dialogue: ["角色名：「台词」", "角色名：「台词」"]
- thought: "（角色内心独白内容）"
- narration: "旁白描述文字"

Output format (JSON only, no other text):
```json
{{
    "global_visual_direction": {{
        "style_enforcement": "{style_preset}_cinematic",
        "aspect_ratio": "2:3",
        "color_grade": "based on atmosphere",
        "overall_lighting": "based on atmosphere"
    }},
    "shots": [
        {{
            "shot_id": {shot_id_start},
            "scene_id": {scene_id},
            "action_beat_id": "beat_id",
            "camera": {{"shot_size": "wide/medium/close_up", "angle": "eye_level/low/high", "movement": "static/pan/dolly", "focal_length": "24mm/35mm/50mm/85mm"}},
            "composition": {{"subject_position": "left_third/center/right_third", "foreground": "foreground element for depth (blurred object, rain, frame edge...)", "background": "background element (city lights, room interior, landscape...)", "depth_layers": "2_layers/3_layers"}},
            "lighting": {{"key_light": "light source", "mood": "atmosphere"}},
            "character_direction": {{"characters_visible": ["char_id"]}},
            "image_prompt": "Full English prompt, 80-100 words, including scene + character appearance + SPECIFIC POSTURE/GESTURE from narration + facial expression + lighting + mood",
            "narration_segment": "Chinese narration segment for TTS",
            "text_overlay": {{"text_type": "dialogue|thought|narration|dialogue_with_thought|none", "chinese_text": ["角色名：「台词」"] or "旁白/心理文字", "speaker_position": "left|right|center|bottom"}},
            "estimated_duration": 5.0
        }}
    ]
}}
```

Now generate the complete JSON with {num_beats} shots:"""

    def _build_prompt(
        self,
        screenplay: dict,
        characters: dict,
        visual_tone: dict,
        style_preset: str,
        min_shots: int = 18,
        attempt: int = 0
    ) -> str:
        """构建分镜脚本生成prompt（硬性约束前置）"""

        # 格式化beats列表
        beats_list = self._format_beats_list(screenplay)
        total_beats = sum(len(s.get("action_beats", [])) for s in screenplay.get("scenes", []))

        # Urgency message for retry
        urgency = ""
        if attempt > 0:
            urgency = f"""
⚠️⚠️⚠️ This is attempt #{attempt+1}, previous attempts generated too few shots ⚠️⚠️⚠️
You MUST generate one shot for each action_beat! Do NOT stop after 1-2 shots!
"""

        # 简化screenplay
        scenes_simplified = []
        for scene in screenplay.get("scenes", []):
            scenes_simplified.append({
                "scene_id": scene.get("scene_id"),
                "scene_heading": scene.get("scene_heading"),
                "location_id": scene.get("location_id"),
                "lighting_condition": scene.get("lighting_condition"),
                "atmosphere": scene.get("atmosphere"),
                "characters_in_scene": scene.get("characters_in_scene"),
                "action_beats": scene.get("action_beats"),
                "dialogue_beats": scene.get("dialogue_beats", []),
                "narration": scene.get("narration")
            })
        screenplay_json = json.dumps(scenes_simplified, ensure_ascii=False, indent=2)

        # 简化角色信息
        chars_simplified = []
        for char in characters.get("characters", []):
            chars_simplified.append({
                "id": char.get("id"),
                "name": char.get("name"),
                "name_en": char.get("name_en"),
                "physical_summary": f"{char.get('physical', {}).get('hair_color', '')} {char.get('physical', {}).get('hair_style', '')}, {char.get('physical', {}).get('eye_color', '')} eyes",
                "clothing_summary": f"{char.get('clothing', {}).get('top', '')}, {char.get('clothing', {}).get('bottom', '')}",
                "default_expression": char.get("character_specific_directions", {}).get("default_expression", "neutral"),
                "posture": char.get("character_specific_directions", {}).get("posture", "natural")
            })
        characters_json = json.dumps(chars_simplified, ensure_ascii=False, indent=2)

        visual_tone_json = json.dumps(visual_tone, ensure_ascii=False, indent=2)

        return f"""
═══════════════════════════════════════════════════════════════════════════════
⚠️ MANDATORY OUTPUT REQUIREMENT - MUST generate {min_shots} shots
═══════════════════════════════════════════════════════════════════════════════
{urgency}
🚫 FORBIDDEN behaviors (will invalidate output):
- Do NOT say "due to length limits" or "I will split into multiple replies" — you have 8192 tokens, enough for all content
- Do NOT add any explanatory text before or after JSON — output pure JSON only
- Do NOT generate only 2 shots then ask if you should continue — must generate all at once

The screenplay has {total_beats} action_beats. You MUST generate 1 shot per beat in this single response.

Each shot MUST include (fields can be simplified but must exist):
- camera (shot_size, angle, movement)
- composition (subject_position)
- lighting (key_light, mood)
- character_direction (characters_visible)
- image_prompt (full English prompt, 80-120 words)
- estimated_duration

You MUST generate all {min_shots} shots, not just 1-2.

═══════════════════════════════════════════════════════════════════════════════
📋 Required shots list (one shot per beat)
═══════════════════════════════════════════════════════════════════════════════

{beats_list}

You MUST generate a shot for each beat above, total {total_beats} shots.

═══════════════════════════════════════════════════════════════════════════════

{CINEMATOGRAPHY_GUIDE}

{NARRATION_TO_VISUAL_EXTRACTION_RULES}

{COMIC_MODE_NARRATIVE_RULES}

{SCENE_PROP_CONTINUITY_RULES}

## Visual Tone
{visual_tone_json}

## Character Data
{characters_json}

## Screenplay
{screenplay_json}

## Output Format

Strictly follow this JSON format (MUST include {min_shots} shots):

```json
{{
    "global_visual_direction": {{
        "style_enforcement": "{style_preset}_cinematic",
        "aspect_ratio": "2:3",
        "color_grade": "based on visual_tone",
        "overall_lighting": "based on visual_tone",
        "lens_style": "35mm_shallow_depth"
    }},
    "shots": [
        {{
            "shot_id": 1,
            "scene_id": 1,
            "action_beat_id": "1a",
            "camera": {{
                "shot_size": "wide_shot",
                "angle": "eye_level",
                "movement": "static",
                "lens": "35mm",
                "focus": "deep_focus"
            }},
            "composition": {{
                "subject_position": "left_third",
                "eye_line_direction": "looking_screen_right",
                "leading_lines": "wet_pavement_to_subject",
                "foreground_element": "rain_droplets",
                "background_element": "dim_city_lights",
                "negative_space": "empty_sky_upper_frame"
            }},
            "lighting": {{
                "key_light": "streetlamp_top_right",
                "fill_light": "ambient_city_glow",
                "rim_light": "subtle_backlight",
                "practical_lights": ["streetlamp", "shop_sign"],
                "shadow_direction": "long_shadows_toward_camera",
                "mood": "melancholic_isolated"
            }},
            "character_direction": {{
                "characters_visible": ["char_001"],
                "char_001": {{
                    "position_in_frame": "entering_from_right",
                    "body_posture": "hunched_running",
                    "facial_expression": "desperate",
                    "eye_line": "looking_at_bus_stop",
                    "gesture": "briefcase_over_head",
                    "clothing_state": "rain_soaked"
                }}
            }},
            "environment": {{
                "weather_visibility": "heavy_rain_in_streetlight",
                "time_indicators": "dark_night_wet_surfaces",
                "atmosphere_particles": "rain_streaks"
            }},
            "emotional_beat": "desperate_hope",
            "image_prompt": "Wide shot at eye level of a rain-soaked bus station at night...(full English prompt)",
            "narration_segment": "Chinese narration for TTS",
            "text_overlay": {{
                "text_type": "dialogue",
                "chinese_text": ["陈默：「你到了吗？」", "苏晨：「快了，别等我。」"],
                "speaker_position": "left"
            }},
            "estimated_duration": 5.0
        }}
    ],
    "shot_continuity_notes": []
}}
```

## Storyboard Principles

1. **One action_beat = One shot**: Direct mapping, do not skip any beat
2. **Shot size variation**: Avoid consecutive same shot sizes, use wide_shot for scene start, close_up for climax
3. **180-degree rule**: Maintain consistent character screen direction
4. **image_prompt**: Full English, include shot size + angle + subject + action + expression + lighting + environment + style tags

## IMAGE PROMPT QUALITY REQUIREMENTS (MANDATORY)

### 1. Each character MUST have specific actions (NO vague descriptions)
❌ BAD: "char_001, char_002 and char_003 are standing together"
✅ GOOD: "char_001 is rubbing his temples with his right hand while staring at his phone, char_002 sits hunched on the bench clutching her knees, char_003 slowly unscrews his thermos lid"

### 2. Each character MUST have explicit gaze direction
❌ BAD: "avoiding eye contact" / "looking away"
✅ GOOD: "char_001 stares blankly down at his wet shoes, char_002 nervously glances sideways toward the empty road"

### 3. Characters MUST physically interact with environment (rain = wet characters)
❌ BAD: "Raindrops are visible in the air"
✅ GOOD: "Rain has soaked char_001's white shirt until it clings transparently to his shoulders, water streams down his face"

### 4. Multi-character scenes MUST describe spatial relationships
❌ BAD: "standing at a distance from each other"
✅ GOOD: "char_001 stands rigid at the far left edge near the signpost, char_002 curls up in the center of the bench, char_003 leans against the right glass panel"

### 5. Emotions MUST be shown through specific body language
❌ BAD: "looking exhausted"
✅ GOOD: "his shoulders sag under an invisible weight, dark circles hollow out his eyes, his tie hangs loose and crooked"

### 6. STRICT CHARACTER COUNT — NO EXTRA PEOPLE
Each image_prompt MUST depict EXACTLY the characters in characters_in_scene — NO ONE ELSE. No bystanders, extras, crowd, or background figures. Empty chairs/seats stay empty.

### 7. OBJECT PHYSICAL PLAUSIBILITY
Multiple objects on the same surface (table/desk/floor) MUST have distinct spatial anchors with non-overlapping placement. Use "at the near edge", "at the far left corner" — NOT "among", "around it", "surrounded by".

### 8. MULTI-CHARACTER LIMB INTERACTION LIMITS
At most 2 characters' hands may actively interact with the SAME object in one shot. If 3+ characters need to touch one object, split into sequential shots or use a reaction shot instead.

### 9. SINGLE-CHARACTER HAND ACTION LIMIT
Each character may perform AT MOST ONE active hand/arm action per shot. If the narration describes multiple hand actions for one character, choose the most dramatically important one. Other actions can be implied or shown in a subsequent shot.
❌ BAD: "char_001 wipes his cheek with the back of his hand while reaching out to push the glass door"
✅ GOOD: "char_001 pushes the glass door open with one hand, rain dripping from his face"

### 10. BACK-VIEW / HIGH-ANGLE CHARACTER CONSISTENCY
When a shot uses back-view, over-the-shoulder, bird's-eye, or high-angle camera: REINFORCE clothing with EXACT color names and garment types, REINFORCE hair with EXACT color and style, and add an explicit note that the character must remain identifiable from behind/above matching the reference image.

### 11. OFF-SCREEN CHARACTER PHYSICAL CONTACT
FORBIDDEN: describing direct physical contact between a visible character and an off-screen character (grip, pull, hold, embrace). Instead show the visible character's INDEPENDENT body language that implies interaction (reaching toward frame edge, beckoning gesture). Reason: models render invisible characters' body parts as floating limbs.

### 12. SPATIAL DIRECTION SELF-CONSISTENCY CHECK
Verify camera_angle, character actions, and spatial descriptions are coherent: front-facing camera → character should not be "walking away"; character "leading ahead" → camera should show back/side not face; character "at the rear" → should not be centered in foreground.

## TEXT OVERLAY MAPPING RULES (MANDATORY)

For each shot, generate a `text_overlay` field by mapping from the scene's `dialogue_beats`:

### Mapping Logic:
1. Match each shot's action_beat_id to corresponding dialogue_beats (by beat_id prefix, e.g. beat "1a" matches "1a_dialogue", "1a_thought")
2. Use the dialogue_beat's `type` field: "dialogue" → text_type="dialogue", "thought" → text_type="thought"
3. Beat has BOTH dialogue AND thought beats → text_type="dialogue_with_thought", chinese_text=mixed list
4. Beat has NO matching dialogue_beat → check emotional_note: character feeling/realization → text_type="thought", pure action/environment → text_type="narration"
5. Only use text_type="none" if the beat truly has zero text content (rare)

### THOUGHT GENERATION RULE (CRITICAL):
When a beat has NO dialogue_beat match, do NOT default to narration.
Check the beat's emotional_note:
- Character internal state/feeling/realization → text_type="thought", create inner monologue
- Pure external action/environment description → text_type="narration"
**Prefer thought over narration.** narration should be the last resort.

### SPEAKER VISIBILITY RULE (MANDATORY - COMIC MEDIUM):
If text_type is "dialogue", EVERY speaker in chinese_text MUST appear in that shot's characters_visible.
Comics have NO audio channel — readers attribute bubbles to the most prominent visible character.
- Single-character reaction shot → use "thought" or "narration", NOT "dialogue"
- Multi-speaker dialogue → ALL speakers must be in characters_visible
- Do NOT borrow dialogue from other beats to fill the distribution target

### Distribution Target:
- dialogue: ≥60% of shots (stories are driven by conversation)
- thought: 10-20%
- narration: ≤15%
- none: ≤5% (purely visual, use sparingly)

### SELF-CHECK (before output):
Count your text_type distribution across all shots. If narration > 15%, convert some to thought (use emotional_note to create inner monologue). If thought < 10%, create thought content for beats with strong emotional_note.

### speaker_position:
- Match to the speaking character's position in composition.subject_position
- "left"/"right" for dialogue, "bottom" for narration/thought, "center" for centered text

### chinese_text Format:
- dialogue: ["角色名：「台词」", "角色名：「台词」"]
- thought: "（角色内心独白内容）"
- narration: "旁白描述文字"

═══════════════════════════════════════════════════════════════════════════════
REMEMBER: You MUST generate {min_shots} complete shots! One shot per beat!
Do NOT say "I will continue" or "do you need more" — output complete JSON directly!
═══════════════════════════════════════════════════════════════════════════════

Output JSON only, no other text:
"""

    def _format_beats_list(self, screenplay: dict) -> str:
        """格式化beats列表，让LLM明确知道要生成多少shots"""
        lines = []
        shot_num = 1
        for scene in screenplay.get("scenes", []):
            scene_id = scene.get("scene_id", "?")
            for beat in scene.get("action_beats", []):
                beat_id = beat.get("beat_id", "?")
                action = beat.get("action", "")[:40]
                lines.append(f"  Shot {shot_num}: Scene {scene_id}, Beat {beat_id} - \"{action}...\"")
                shot_num += 1
        return "\n".join(lines) if lines else "  (no action_beats)"

    def _extract_json(self, content: str) -> Optional[dict]:
        """从LLM响应中提取JSON"""
        import re

        # 尝试提取```json ... ```块
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试直接解析整个内容
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # 尝试找到第一个{和最后一个}
        start = content.find('{')
        end = content.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(content[start:end+1])
            except json.JSONDecodeError:
                pass

        return None

    def _extract_gaze_cues(self, narration: str, characters_in_scene: list) -> dict:
        """
        从narration中提取视线方向线索

        用于辅助生成更精确的image_prompt，确保角色视线方向与剧情一致

        Args:
            narration: 中文旁白文本
            characters_in_scene: 场景中的角色ID列表

        Returns:
            dict: {
                "has_gaze_cue": bool,
                "gaze_verb": str,  # 原始中文动词
                "gaze_translation": str,  # 英文翻译
                "gaze_target": str,  # 视线目标（如果能识别）
            }
        """
        gaze_verbs = {
            "发现": "eyes lock onto",
            "看到": "eyes catch sight of",
            "看着": "staring at",
            "注视": "gazing intently at",
            "盯着": "staring fixedly at",
            "望向": "looking toward",
            "瞥见": "catching a glimpse of",
            "回头看": "turning to look at",
            "打量": "eyes scanning over",
            "凝视": "eyes riveted on",
            "看向": "looking toward",
            "望着": "gazing at",
            "低头看": "looking down at",
            "抬头看": "looking up at",
        }

        result = {
            "has_gaze_cue": False,
            "gaze_verb": "",
            "gaze_translation": "",
            "gaze_target": ""
        }

        # 检查是否包含视线动词
        for verb, translation in gaze_verbs.items():
            if verb in narration:
                result["has_gaze_cue"] = True
                result["gaze_verb"] = verb
                result["gaze_translation"] = translation

                # 尝试提取视线目标
                # 简单启发式：视线动词后面的名词短语
                idx = narration.find(verb)
                if idx != -1:
                    # 取动词后面最多20个字符作为潜在目标
                    target_text = narration[idx + len(verb):idx + len(verb) + 20]
                    # 如果目标文本包含角色名称，标记为角色
                    for char_id in characters_in_scene:
                        if char_id in target_text:
                            result["gaze_target"] = f"[character: {char_id}]"
                            break
                    else:
                        # 取第一个标点之前的内容
                        for punct in ["，", "。", "！", "？", "；", "、"]:
                            if punct in target_text:
                                target_text = target_text[:target_text.find(punct)]
                        result["gaze_target"] = target_text.strip()

                break  # 找到第一个视线动词即返回

        return result

    def _validate_storyboard(self, storyboard: dict, characters: dict = None) -> None:
        """验证分镜脚本（含 T5 speaker-visibility 校验）"""
        shots = storyboard.get("shots", [])

        if len(shots) == 0:
            raise ValueError("shots数组不能为空")

        # 验证global_visual_direction
        gvd = storyboard.get("global_visual_direction", {})
        if not gvd:
            storyboard["global_visual_direction"] = {
                "style_enforcement": "realistic_cinematic",
                "aspect_ratio": "2:3",
                "color_grade": "neutral",
                "overall_lighting": "natural",
                "lens_style": "35mm"
            }

        # T5: 构建 中文名→char_id 映射
        name_to_id = {}
        if characters:
            for c in characters.get("characters", []):
                char_id = c.get("id", "")
                char_name = c.get("name", "")
                if char_id and char_name:
                    name_to_id[char_name] = char_id

        for shot in shots:
            shot_id = shot.get("shot_id", "?")

            # 验证必要字段
            required = ["shot_id", "scene_id", "camera", "image_prompt"]
            missing = [f for f in required if f not in shot]
            if missing:
                raise ValueError(f"Shot {shot_id} 缺少必要字段: {missing}")

            # 验证camera
            camera = shot.get("camera", {})
            camera_required = ["shot_size", "angle"]
            camera_missing = [f for f in camera_required if f not in camera]
            if camera_missing:
                print(f"  ⚠️ Shot {shot_id} camera缺少: {camera_missing}")

            # 设置默认值
            if "movement" not in camera:
                camera["movement"] = "static"
            if "lens" not in camera:
                camera["lens"] = "35mm"
            if "focus" not in camera:
                camera["focus"] = "deep_focus"

            # 验证composition（可选，设置默认值）
            if "composition" not in shot:
                shot["composition"] = {
                    "subject_position": "center",
                    "eye_line_direction": "neutral",
                    "leading_lines": "",
                    "foreground_element": "",
                    "background_element": "",
                    "negative_space": ""
                }

            # 验证lighting（可选，设置默认值）
            if "lighting" not in shot:
                shot["lighting"] = {
                    "key_light": "natural",
                    "fill_light": "ambient",
                    "rim_light": "none",
                    "practical_lights": [],
                    "shadow_direction": "natural",
                    "mood": "neutral"
                }

            # 验证character_direction（可选）
            if "character_direction" not in shot:
                shot["character_direction"] = {
                    "characters_visible": []
                }

            # 验证estimated_duration
            if "estimated_duration" not in shot:
                shot["estimated_duration"] = 5.0

            # T5: speaker-visibility 校验
            # 若 text_type 含 dialogue，speaker 必须在 characters_visible 中
            if name_to_id:
                text_overlay = shot.get("text_overlay", {})
                if text_overlay:
                    text_type = text_overlay.get("text_type", "none")
                    chars_visible = shot.get("character_direction", {}).get("characters_visible", [])
                    if text_type in ["dialogue", "dialogue_with_thought",
                                     "dialogue_with_narration", "narration_with_dialogue"]:
                        chinese_text = text_overlay.get("chinese_text", "")
                        texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
                        has_invisible_speaker = False
                        for txt in texts:
                            if isinstance(txt, dict):
                                sub_type = txt.get("type", "dialogue")
                                txt_str = txt.get("text", "")
                            else:
                                txt_str = txt
                                sub_type = "dialogue" if ("：「" in txt_str or ":「" in txt_str or "：\"" in txt_str) else "other"
                            if sub_type != "dialogue":
                                continue
                            # 提取说话者中文名
                            match = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', txt_str.strip())
                            if match:
                                speaker_zh = match.group(1)
                                # 查找 char_id
                                char_id = name_to_id.get(speaker_zh)
                                if not char_id:
                                    for name, cid in name_to_id.items():
                                        if speaker_zh in name or name in speaker_zh:
                                            char_id = cid
                                            break
                                if char_id and char_id not in chars_visible:
                                    has_invisible_speaker = True
                                    print(f"  ⚠️ [T5] Shot {shot_id}: speaker '{speaker_zh}' ({char_id}) "
                                          f"不在 characters_visible {chars_visible} 中")
                        # T29: 不降级 text_type，改为打标 off_screen_speaker
                        # 原逻辑（已移除）：dialogue→thought 导致气泡变成黑底白字旁白条
                        # 新逻辑：保留 dialogue 类型 + 标记画外音，渲染为画外音对话风格
                        if has_invisible_speaker:
                            text_overlay["off_screen_speaker"] = True
                            if text_type == "dialogue":
                                print(f"  ℹ️ [T29] Shot {shot_id}: dialogue 保留，标记 off_screen_speaker=true（画外音对话）")
                            elif text_type in ["dialogue_with_thought", "dialogue_with_narration", "narration_with_dialogue"]:
                                print(f"  ℹ️ [T29] Shot {shot_id}: '{text_type}' 保留，标记 off_screen_speaker=true（含画外音子类型）")

            # T34 Plan B: 检测 image_prompt 是否含镜头信息，缺失时从 shot 元数据注入
            image_prompt = shot.get("image_prompt", "")
            camera = shot.get("camera", {})
            shot_size = camera.get("shot_size", "")
            camera_angle = camera.get("angle", "")

            if image_prompt and shot_size:
                # 将 shot_size 映射到 image_prompt 中可能出现的关键词
                size_keywords = {
                    "wide_shot": ["wide shot", "wide-shot", "wide angle"],
                    "establishing": ["establishing shot", "wide shot", "panoramic"],
                    "medium_wide": ["medium wide", "medium-wide"],
                    "medium_shot": ["medium shot", "medium-shot", "mid shot", "mid-shot"],
                    "medium_close_up": ["medium close", "medium close-up"],
                    "close_up": ["close-up", "close up", "closeup"],
                    "extreme_close_up": ["extreme close", "extreme close-up", "macro"]
                }
                angle_keywords = {
                    "low_angle": ["low angle", "low-angle", "looking up"],
                    "high_angle": ["high angle", "high-angle", "looking down", "overhead", "bird"],
                    "dutch_angle": ["dutch angle", "dutch-angle", "tilted"],
                    "eye_level": ["eye level", "eye-level"]
                }

                # 检测 shot_size 是否在 image_prompt 中
                prompt_lower = image_prompt.lower()
                keywords_for_size = size_keywords.get(shot_size, [shot_size.replace("_", " ")])
                has_size = any(kw in prompt_lower for kw in keywords_for_size)

                # 检测 camera_angle 是否在 image_prompt 中（eye_level 不强制要求）
                has_angle = True  # eye_level 默认不需要
                if camera_angle and camera_angle != "eye_level":
                    keywords_for_angle = angle_keywords.get(camera_angle, [camera_angle.replace("_", " ")])
                    has_angle = any(kw in prompt_lower for kw in keywords_for_angle)

                if not has_size or not has_angle:
                    # 构建自然的镜头描述短语并注入 image_prompt 开头
                    size_phrase = shot_size.replace("_", " ")
                    angle_phrase = camera_angle.replace("_", " ") if camera_angle and camera_angle != "eye_level" else ""

                    if angle_phrase:
                        camera_prefix = f"{angle_phrase} {size_phrase}"
                    else:
                        camera_prefix = size_phrase

                    # 注入到 image_prompt 开头，自然融合
                    shot["image_prompt"] = f"{camera_prefix} — {image_prompt}"
                    print(f"  ℹ️ [T34] Shot {shot_id}: 注入镜头信息 '{camera_prefix}'（原 prompt 缺失 shot_size/angle 关键词）")

        # 验证shot_continuity_notes（可选）
        if "shot_continuity_notes" not in storyboard:
            storyboard["shot_continuity_notes"] = []

    def _rebalance_text_types(self, storyboard: dict) -> None:
        """T7: 检查 text_type 分布，narration > 15% 或 thought < 10% 时打印警告"""
        shots = storyboard.get("shots", [])
        if not shots:
            return

        counts = {"dialogue": 0, "thought": 0, "narration": 0, "none": 0, "compound": 0}
        for shot in shots:
            text_overlay = shot.get("text_overlay", {})
            text_type = text_overlay.get("text_type", "none") if text_overlay else "none"
            if text_type in counts:
                counts[text_type] += 1
            elif text_type != "none":
                counts["compound"] += 1

        total = len(shots)
        dialogue_pct = (counts["dialogue"] + counts["compound"]) / total * 100
        thought_pct = counts["thought"] / total * 100
        narration_pct = counts["narration"] / total * 100
        none_pct = counts["none"] / total * 100

        print(f"  [T7] text_type 分布: dialogue={dialogue_pct:.0f}% thought={thought_pct:.0f}% "
              f"narration={narration_pct:.0f}% none={none_pct:.0f}% (共{total}shots)")

        if narration_pct > 15:
            print(f"  ⚠️ [T7] narration 超标 ({narration_pct:.0f}% > 15%)，"
                  f"建议检查 Stage 3 dialogue_beats 覆盖率")
        if thought_pct < 10:
            print(f"  ⚠️ [T7] thought 不足 ({thought_pct:.0f}% < 10%)，"
                  f"建议检查 Stage 3 thought 类型 beats 比例")


# 便捷函数
async def direct_storyboard(
    screenplay: dict,
    characters: dict,
    visual_tone: dict,
    style_preset: str = "anime"
) -> dict:
    """便捷函数：生成分镜脚本"""
    director = StoryboardDirector()
    return await director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=visual_tone,
        style_preset=style_preset
    )
