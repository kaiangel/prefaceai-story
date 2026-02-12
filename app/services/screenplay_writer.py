"""
Stage 3: ScreenplayWriter

Phase 2.0 第三阶段 - 分场剧本生成器（分批生成模式）
基于故事大纲和角色设计，按plot_point分批生成详细的分场剧本。

核心改进：
- 每个plot_point独立生成一个scene
- 避免LLM"篇幅恐惧"导致的截断
- 传入previous_scenes保证叙事连贯性
"""

import json
import os
from typing import Optional, List
import anthropic
from google import genai


class ScreenplayWriter:
    """
    分场剧本生成器（分批模式）

    输入: outline.json + characters.json
    输出: screenplay.json

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

    async def write(self, outline: dict, characters: dict) -> dict:
        """
        生成分场剧本（分批生成：每个plot_point生成一个scene）

        Args:
            outline: Stage 1生成的故事大纲
            characters: Stage 2生成的角色设计

        Returns:
            screenplay dict
        """
        plot_points = outline.get("plot_points", [])
        target_metrics = outline.get("target_metrics", {})
        target_seconds = target_metrics.get("target_duration_seconds", 180)

        print(f"[ScreenplayWriter] 生成分场剧本（按plot_point分批）...")
        print(f"  剧情节点数: {len(plot_points)}")
        print(f"  目标时长: {target_seconds}秒")

        all_scenes = []

        for i, plot_point in enumerate(plot_points):
            beat_name = plot_point.get("beat", f"plot_{i+1}")
            print(f"  生成 Scene {i+1}/{len(plot_points)} [{beat_name}]...", end=" ")

            scene = await self._generate_scene_for_plot_point(
                plot_point=plot_point,
                plot_point_index=i,
                total_plot_points=len(plot_points),
                outline=outline,
                characters=characters,
                previous_scenes=all_scenes
            )

            if scene:
                all_scenes.append(scene)
                beats_count = len(scene.get("action_beats", []))
                narration_len = len(scene.get("narration", ""))
                print(f"✅ {beats_count} beats, {narration_len}字")
            else:
                print(f"❌ 失败")

        if not all_scenes:
            raise ValueError("无法生成任何scene")

        # 统计
        total_beats = sum(len(s.get("action_beats", [])) for s in all_scenes)
        total_words = sum(len(s.get("narration", "")) for s in all_scenes)

        print(f"[ScreenplayWriter] ✅ 剧本生成完成")
        print(f"  场景数: {len(all_scenes)}")
        print(f"  动作节拍: {total_beats}个")
        print(f"  旁白字数: {total_words}字 (≈{total_words/4:.0f}秒)")

        screenplay = {
            "scenes": all_scenes,
            "total_scenes": len(all_scenes),
            "total_action_beats": total_beats,
            "total_narration_words": total_words,
            "total_estimated_duration_seconds": total_words / 4
        }

        return screenplay

    async def _generate_scene_for_plot_point(
        self,
        plot_point: dict,
        plot_point_index: int,
        total_plot_points: int,
        outline: dict,
        characters: dict,
        previous_scenes: List[dict]
    ) -> Optional[dict]:
        """为单个plot_point生成scene（带字数验证和扩写机制）"""

        duration = plot_point.get("estimated_duration_seconds", 30)
        target_narration_words = max(80, int(duration * 4))

        max_attempts = 3
        best_scene = None
        best_word_count = 0

        for attempt in range(max_attempts):
            prompt = self._build_single_scene_prompt(
                plot_point=plot_point,
                plot_point_index=plot_point_index,
                total_plot_points=total_plot_points,
                outline=outline,
                characters=characters,
                previous_scenes=previous_scenes
            )

            try:
                # DEBUG: 保存第一个scene的prompt
                if plot_point_index == 0 and attempt == 0:
                    with open("forclaudeweb/stage3_actual_prompt.txt", "w", encoding="utf-8") as f:
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
                if plot_point_index == 0 and attempt == 0:
                    with open("forclaudeweb/stage3_raw_response.txt", "w", encoding="utf-8") as f:
                        f.write(f"\n=== Raw Response ===\n\n")
                        f.write(content)

                scene = self._extract_json(content)

                if scene:
                    actual_words = len(scene.get("narration", ""))

                    # 记录最佳结果
                    if actual_words > best_word_count:
                        best_scene = scene
                        best_word_count = actual_words

                    # 达标检查（80%容差）
                    if actual_words >= target_narration_words * 0.8:
                        self._validate_scene(scene, plot_point_index + 1)
                        return scene
                    else:
                        if attempt < max_attempts - 1:
                            print(f"(字数:{actual_words}/{target_narration_words})", end=" ")
                            continue  # 重试

            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"(error: {e})", end=" ")

        # 所有尝试都不达标，尝试扩写
        if best_scene and best_word_count < target_narration_words * 0.8:
            print(f"(扩写中)", end=" ")
            best_scene = await self._expand_narration_if_needed(
                scene=best_scene,
                target_words=target_narration_words
            )

        if best_scene:
            self._validate_scene(best_scene, plot_point_index + 1)

        return best_scene

    async def _expand_narration_if_needed(self, scene: dict, target_words: int) -> dict:
        """如果narration太短，调用LLM进行扩写"""

        current_narration = scene.get("narration", "")
        current_words = len(current_narration)

        if current_words >= target_words * 0.8:
            return scene  # 不需要扩写

        expand_prompt = f"""请扩写以下旁白，使其达到{target_words}字以上。

## 场景背景
- 场景: {scene.get('scene_heading', '')}
- 氛围: {scene.get('atmosphere', {}).get('mood', '')}
- 出场角色: {', '.join(scene.get('characters_in_scene', []))}

## 当前旁白（{current_words}字，需要扩展到{target_words}字）
{current_narration}

## 扩写要求
1. 保留原有内容的核心信息和情感基调
2. 增加感官细节（视觉、听觉、触觉、嗅觉）
3. 增加人物内心活动描写
4. 增加环境氛围渲染
5. 语言要有文学性，适合TTS朗读

直接输出扩写后的旁白文本，不要任何解释或标记："""

        try:
            expanded = None

            # 优先使用 Gemini 3 Flash
            if self.gemini_client:
                try:
                    response = await self.gemini_client.aio.models.generate_content(
                        model=self.gemini_model,
                        contents=expand_prompt,
                        config={"max_output_tokens": 8631}
                    )
                    expanded = response.text.strip()
                except Exception:
                    pass

            # Fallback到Claude Haiku
            if expanded is None and self.claude_client:
                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=8631,
                    messages=[{"role": "user", "content": expand_prompt}]
                )
                expanded = response.content[0].text.strip()

            # 验证扩写结果
            if expanded and len(expanded) > current_words:
                scene["narration"] = expanded
                print(f"({current_words}→{len(expanded)}字)", end=" ")

        except Exception as e:
            print(f"(扩写失败)", end=" ")

        return scene

    def _build_single_scene_prompt(
        self,
        plot_point: dict,
        plot_point_index: int,
        total_plot_points: int,
        outline: dict,
        characters: dict,
        previous_scenes: List[dict]
    ) -> str:
        """为单个plot_point构建prompt"""

        scene_id = plot_point_index + 1
        beat_name = plot_point.get("beat", f"plot_{scene_id}")
        description = plot_point.get("description", "")
        duration = plot_point.get("estimated_duration_seconds", 30)

        # 计算目标数量
        target_beats = max(3, int(duration / 6))  # 约6秒一个beat
        target_narration_words = max(80, int(duration * 4))  # 4字/秒

        # 前情提要
        previous_context = ""
        if previous_scenes:
            last_scene = previous_scenes[-1]
            last_narration = last_scene.get("narration", "")
            previous_context = f"""
## 前情提要
上一场景: {last_scene.get('scene_heading', '')}
结束状态: {last_narration[-80:] if len(last_narration) > 80 else last_narration}
"""

        # 简化角色信息 + 提取道具清单
        chars_info = []
        chars_props = []
        for char in characters.get("characters", []):
            char_id = char.get('id')
            char_name = char.get('name')
            chars_info.append(f"- {char_id}: {char_name} ({char.get('role', 'character')})")

            # 提取角色的合法道具/配饰
            clothing = char.get('clothing', {})
            accessories = clothing.get('accessories', [])
            if accessories:
                chars_props.append(f"  - {char_name} ({char_id}): {', '.join(accessories)}")
            else:
                chars_props.append(f"  - {char_name} ({char_id}): 无配饰")

        chars_str = "\n".join(chars_info)
        chars_props_str = "\n".join(chars_props) if chars_props else "  （无角色定义配饰）"

        # 场景位置信息 - 构建详细的location列表
        locations = outline.get("unique_locations", [])
        if locations:
            locations_lines = []
            for loc in locations:
                loc_id = loc.get("location_id", loc.get("id", "unknown"))
                display_name = loc.get("display_name", loc.get("name", "未知场景"))
                loc_type = loc.get("location_type", "")
                locations_lines.append(f"  - {loc_id}: {display_name} ({loc_type})")
            locations_str = "\n".join(locations_lines)
            # 提取第一个location_id作为示例
            first_location_id = locations[0].get("location_id", locations[0].get("id", "L001"))
        else:
            locations_str = "  - default_location: 默认场景"
            first_location_id = "default_location"

        return f"""为以下剧情节点生成一个完整的scene。

═══════════════════════════════════════════════════════════
CRITICAL: CHARACTER CONSISTENCY RULES
═══════════════════════════════════════════════════════════

You MUST only use props and accessories that are DEFINED in the character data.
DO NOT invent new accessories, clothing items, or physical features.

ALLOWED props for each character (from characters.json):
{chars_props_str}

❌ FORBIDDEN:
- Adding glasses, hats, bags, umbrellas, or any item NOT in the character definition
- Changing clothing colors or styles from what is defined
- Adding scars, tattoos, or physical marks not defined
- Inventing props the character carries (phones, keys are OK if plot-essential)

✅ CORRECT approach:
- For wiping face: use "wiped the rain from his face" instead of "took off glasses to wipe"
- For sheltering from rain: use "shielded his face with his hand" instead of "opened umbrella"
- For checking time: use "pulled out phone to check time" or use character's defined watch

═══════════════════════════════════════════════════════════

## 当前任务
生成第 {scene_id} 场戏（共 {total_plot_points} 场）

## 剧情节点
- 节拍类型: {beat_name}
- 描述: {description}
- 目标时长: {duration}秒
{previous_context}
## 角色
{chars_str}

## 可用场景位置
以下是本故事中定义的所有场景位置，你必须从中选择：
{locations_str}

⚠️ 重要：location_id 必须完全匹配上述列表中的值（如 "{first_location_id}"），不要自己编造新的ID。

## 输出要求
这个scene必须包含：
- 至少 {target_beats} 个 action_beats
- 约 {target_narration_words} 字的 narration（有文学性的旁白）

直接输出JSON，不要```json```包裹，不要任何解释文字：
{{
    "scene_id": {scene_id},
    "scene_heading": "EXT/INT. LOCATION - TIME - WEATHER",
    "plot_point": "{beat_name}",
    "location_id": "{first_location_id}",
    "time_of_day": "时间",
    "weather": "天气",
    "lighting_condition": "光线条件",
    "atmosphere": {{
        "mood": "tense / melancholic / hopeful / peaceful (English only, for image generation)",
        "sound_design_hint": "音效提示",
        "temperature_feel": "温度感受"
    }},
    "characters_in_scene": ["char_001"],
    "action_beats": [
        {{"beat_id": "{scene_id}a", "action": "动作描述", "duration_hint": 5, "emotional_note": "情绪"}},
        {{"beat_id": "{scene_id}b", "action": "动作描述", "duration_hint": 5, "emotional_note": "情绪"}},
        {{"beat_id": "{scene_id}c", "action": "动作描述", "duration_hint": 5, "emotional_note": "情绪"}}
    ],
    "narration": "【字数硬性要求：必须≥{target_narration_words}字】这是TTS朗读的旁白，要有文学性。详细描写：人物神态动作、内心活动、环境氛围、情绪变化、感官细节。充分展开，不要惜字如金。写够{target_narration_words}字...",
    "narration_tone": "情绪基调",
    "narration_pace": "节奏"
}}"""

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

    def _validate_scene(self, scene: dict, expected_scene_id: int) -> None:
        """验证单个scene"""
        # 确保scene_id正确
        scene["scene_id"] = expected_scene_id

        # 验证必要字段，设置默认值
        if "action_beats" not in scene:
            scene["action_beats"] = []

        if "narration" not in scene:
            scene["narration"] = ""

        if "characters_in_scene" not in scene:
            scene["characters_in_scene"] = []

        if "location_id" not in scene:
            scene["location_id"] = "unknown"

        # 验证action_beats
        for i, beat in enumerate(scene.get("action_beats", [])):
            if "beat_id" not in beat:
                beat["beat_id"] = f"{expected_scene_id}{chr(97+i)}"
            if "action" not in beat:
                beat["action"] = ""
            if "duration_hint" not in beat:
                beat["duration_hint"] = 5

        # 设置默认atmosphere
        if "atmosphere" not in scene:
            scene["atmosphere"] = {
                "mood": "neutral",
                "sound_design_hint": "",
                "temperature_feel": ""
            }

        if "narration_tone" not in scene:
            scene["narration_tone"] = "neutral"

        if "narration_pace" not in scene:
            scene["narration_pace"] = "steady"


# 便捷函数
async def write_screenplay(outline: dict, characters: dict) -> dict:
    """便捷函数：生成分场剧本"""
    writer = ScreenplayWriter()
    return await writer.write(outline, characters)
