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

import json
import os
from typing import Optional
import anthropic
from google import genai

from app.prompts.storyboard_prompts import NARRATION_TO_VISUAL_EXTRACTION_RULES


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

    模型优先级: Gemini 3 Flash (主) → Claude Haiku (备用)
    """

    def __init__(self):
        # 主模型: Gemini 3 Flash
        self.gemini_client = None
        self.gemini_model = "gemini-3-flash-preview"
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

        # 备用模型: Claude Haiku
        self.claude_client = None
        self.claude_model = "claude-haiku-4-5-20251001"
        if os.getenv("ANTHROPIC_API_KEY"):
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

    async def direct(
        self,
        screenplay: dict,
        characters: dict,
        visual_tone: dict,
        style_preset: str = "realistic"
    ) -> dict:
        """
        生成分镜脚本（按scene分批生成，解决LLM输出不完整问题）

        Args:
            screenplay: Stage 3生成的分场剧本
            characters: Stage 2生成的角色设计
            visual_tone: Stage 1大纲中的视觉风调
            style_preset: 风格预设

        Returns:
            storyboard dict
        """
        scenes = screenplay.get("scenes", [])
        total_beats = sum(len(s.get("action_beats", [])) for s in scenes)

        print(f"[StoryboardDirector] 生成分镜脚本（按scene分批）...")
        print(f"  场景数: {len(scenes)}")
        print(f"  动作节拍: {total_beats}个")
        print(f"  风格: {style_preset}")

        # 按scene分批生成
        all_shots = []
        global_visual_direction = None
        shot_id_counter = 1

        for scene_idx, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", scene_idx + 1)
            beats = scene.get("action_beats", [])

            if not beats:
                print(f"  ⚠️ Scene {scene_id} 无action_beats，跳过")
                continue

            print(f"  生成 Scene {scene_id} ({len(beats)} beats)...", end=" ")

            # 为这个scene生成shots
            scene_shots, gvd = await self._generate_scene_shots(
                scene=scene,
                scene_idx=scene_idx,
                characters=characters,
                visual_tone=visual_tone,
                style_preset=style_preset,
                shot_id_start=shot_id_counter
            )

            if scene_shots:
                # 更新shot_id
                for shot in scene_shots:
                    shot["shot_id"] = shot_id_counter
                    shot_id_counter += 1
                all_shots.extend(scene_shots)
                print(f"✅ {len(scene_shots)} shots")

                # 保存第一个scene的global_visual_direction
                if global_visual_direction is None and gvd:
                    global_visual_direction = gvd
            else:
                print(f"❌ 失败")

        if not all_shots:
            raise ValueError("无法生成任何shots")

        total_duration = sum(s.get("estimated_duration", 5) for s in all_shots)

        print(f"[StoryboardDirector] ✅ 分镜生成完成")
        print(f"  总镜头数: {len(all_shots)}")
        print(f"  预计时长: {total_duration}秒 ({total_duration/60:.1f}分钟)")

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

        return storyboard

    async def _generate_scene_shots(
        self,
        scene: dict,
        scene_idx: int,
        characters: dict,
        visual_tone: dict,
        style_preset: str,
        shot_id_start: int
    ) -> tuple:
        """为单个scene生成shots"""
        max_attempts = 2

        for attempt in range(max_attempts):
            prompt = self._build_scene_prompt(
                scene=scene,
                characters=characters,
                visual_tone=visual_tone,
                style_preset=style_preset,
                shot_id_start=shot_id_start
            )

            try:
                # DEBUG: 保存第一个scene的prompt
                if scene_idx == 0 and attempt == 0:
                    with open("forclaudeweb/stage4_actual_prompt.txt", "w", encoding="utf-8") as f:
                        f.write(prompt)

                content = None

                # 优先使用 Gemini 3 Flash
                if self.gemini_client:
                    try:
                        response = await self.gemini_client.aio.models.generate_content(
                            model=self.gemini_model,
                            contents=prompt,
                            config={"max_output_tokens": 8631}
                        )
                        content = response.text
                    except Exception as ge:
                        pass  # 静默失败，尝试Claude

                # Fallback到Claude Haiku
                if content is None and self.claude_client:
                    response = self.claude_client.messages.create(
                        model=self.claude_model,
                        max_tokens=8631,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    content = response.content[0].text

                if content is None:
                    raise ValueError("无可用的LLM服务")

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
        shot_id_start: int
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
            "narration": scene.get("narration", "")
        }, ensure_ascii=False, indent=2)

        return f"""Generate {num_beats} shots for Scene {scene_id}.

Required shots (one shot per beat):
{beats_str}

Scene data:
{scene_json}

Character data:
{characters_json}

{NARRATION_TO_VISUAL_EXTRACTION_RULES}

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
            "camera": {{"shot_size": "wide/medium/close_up", "angle": "eye_level/low/high", "movement": "static/pan/dolly"}},
            "composition": {{"subject_position": "position description"}},
            "lighting": {{"key_light": "light source", "mood": "atmosphere"}},
            "character_direction": {{"characters_visible": ["char_id"]}},
            "image_prompt": "Full English prompt, 80-100 words, including scene + character appearance + SPECIFIC POSTURE/GESTURE from narration + facial expression + lighting + mood",
            "narration_segment": "Chinese narration segment for TTS",
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

    def _validate_storyboard(self, storyboard: dict) -> None:
        """验证分镜脚本"""
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

        # 验证shot_continuity_notes（可选）
        if "shot_continuity_notes" not in storyboard:
            storyboard["shot_continuity_notes"] = []


# 便捷函数
async def direct_storyboard(
    screenplay: dict,
    characters: dict,
    visual_tone: dict,
    style_preset: str = "realistic"
) -> dict:
    """便捷函数：生成分镜脚本"""
    director = StoryboardDirector()
    return await director.direct(
        screenplay=screenplay,
        characters=characters,
        visual_tone=visual_tone,
        style_preset=style_preset
    )
