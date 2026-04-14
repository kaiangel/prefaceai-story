"""
Stage 3: ScreenplayWriter

Phase 2.0 第三阶段 - 分场剧本生成器（分批生成模式）
基于故事大纲和角色设计，按plot_point分批生成详细的分场剧本。

核心改进：
- 每个plot_point独立生成一个scene
- 避免LLM"篇幅恐惧"导致的截断
- 传入previous_scenes保证叙事连贯性
"""

import asyncio
import json
import time
import logging
from typing import Optional, List
import anthropic
from google import genai
from app.config import settings

logger = logging.getLogger("xuhua")


class ScreenplayWriter:
    """
    分场剧本生成器（分批模式）

    输入: outline.json + characters.json
    输出: screenplay.json

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

    async def write(self, outline: dict, characters: dict, family_relationships: list = None, progress_callback=None) -> dict:
        """
        生成分场剧本（B-3: 自适应 batch 模式）

        策略:
        - ≤8 scenes: 全 batch，一次 API 调用
        - 9-15 scenes: 分 2 批
        - batch 失败: fallback 到逐 scene 模式

        Args:
            outline: Stage 1生成的故事大纲
            characters: Stage 2生成的角色设计
            family_relationships: T32 — Stage 1 输出的家庭/人物关系列表（可选）
            progress_callback: 进度回调函数

        Returns:
            screenplay dict
        """
        self._family_relationships = family_relationships or []
        plot_points = outline.get("plot_points", [])
        target_metrics = outline.get("target_metrics", {})
        target_seconds = target_metrics.get("target_duration_seconds", 180)

        print(f"[ScreenplayWriter] 生成分场剧本...")
        print(f"  剧情节点数: {len(plot_points)}")
        print(f"  目标时长: {target_seconds}秒")
        logger.info(f"[ScreenplayWriter] 开始生成分场剧本")
        logger.info(f"  剧情节点数: {len(plot_points)}, 目标时长: {target_seconds}s")
        stage_start = time.time()

        all_scenes = []
        n = len(plot_points)

        # B-3: 自适应 batch 策略
        if n <= 8:
            # 全 batch: 一次 API 调用
            print(f"  [B-3] 全 batch 模式 ({n} scenes ≤ 8)")
            try:
                all_scenes = await self._generate_all_scenes_batch(
                    plot_points=plot_points,
                    outline=outline,
                    characters=characters,
                    previous_scenes=[],
                )
                if all_scenes:
                    print(f"  [B-3] ✅ 全 batch 成功: {len(all_scenes)} scenes")
                    # B-4: batch 完成后一次性更新进度
                    if progress_callback:
                        await progress_callback("screenplay", 35, f"剧本编写完成 ({len(all_scenes)} 场戏)...")
                else:
                    print(f"  [B-3] ⚠️ 全 batch 返回空，fallback 到逐 scene")
                    all_scenes = []
            except Exception as e:
                print(f"  [B-3] ⚠️ 全 batch 失败 ({e})，fallback 到逐 scene")
                all_scenes = []

        elif n <= 15:
            # 分 2 批
            mid = (n + 1) // 2
            print(f"  [B-3] 分 2 批模式 ({n} scenes: 前 {mid} + 后 {n - mid})")
            try:
                batch1 = await self._generate_all_scenes_batch(
                    plot_points=plot_points[:mid],
                    outline=outline,
                    characters=characters,
                    previous_scenes=[],
                )
                if batch1:
                    all_scenes.extend(batch1)
                    print(f"  [B-3] ✅ 第 1 批成功: {len(batch1)} scenes")
                    if progress_callback:
                        await progress_callback("screenplay", 22, f"剧本编写中 (第 1 批完成)...")

                    batch2 = await self._generate_all_scenes_batch(
                        plot_points=plot_points[mid:],
                        outline=outline,
                        characters=characters,
                        previous_scenes=all_scenes,
                        scene_id_offset=mid,
                    )
                    if batch2:
                        all_scenes.extend(batch2)
                        print(f"  [B-3] ✅ 第 2 批成功: {len(batch2)} scenes")
                        if progress_callback:
                            await progress_callback("screenplay", 35, f"剧本编写完成 ({len(all_scenes)} 场戏)...")
                    else:
                        print(f"  [B-3] ⚠️ 第 2 批失败，fallback 剩余到逐 scene")
                        all_scenes = []  # 重置，全部 fallback
                else:
                    print(f"  [B-3] ⚠️ 第 1 批失败，fallback 到逐 scene")
                    all_scenes = []
            except Exception as e:
                print(f"  [B-3] ⚠️ 分批失败 ({e})，fallback 到逐 scene")
                all_scenes = []

        # Fallback: 逐 scene 模式（原始逻辑）
        if not all_scenes:
            print(f"  [B-3] 逐 scene 模式 ({n} scenes)")
            for i, plot_point in enumerate(plot_points):
                beat_name = plot_point.get("beat", f"plot_{i+1}")
                print(f"  生成 Scene {i+1}/{n} [{beat_name}]...", end=" ")

                scene = await self._generate_scene_for_plot_point(
                    plot_point=plot_point,
                    plot_point_index=i,
                    total_plot_points=n,
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

                # B-4: 逐 scene 进度回调
                if progress_callback:
                    p = 10 + int((i + 1) / n * 25)
                    await progress_callback(
                        "screenplay", p,
                        f"剧本编写中 (Scene {i+1}/{n})..."
                    )

        if not all_scenes:
            raise ValueError("无法生成任何scene")

        # 统计
        total_beats = sum(len(s.get("action_beats", [])) for s in all_scenes)
        total_words = sum(len(s.get("narration", "")) for s in all_scenes)

        stage_elapsed = time.time() - stage_start
        print(f"[ScreenplayWriter] ✅ 剧本生成完成")
        print(f"  场景数: {len(all_scenes)}")
        print(f"  动作节拍: {total_beats}个")
        print(f"  旁白字数: {total_words}字 (≈{total_words/4:.0f}秒)")
        logger.info(f"[ScreenplayWriter] ✅ 剧本生成完成 (总耗时 {stage_elapsed:.1f}s)")
        logger.info(f"  场景数: {len(all_scenes)}, 动作节拍: {total_beats}, 旁白字数: {total_words}")

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

                content = await self._call_llm_with_retry(prompt, max_tokens=8631)

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

    async def _generate_all_scenes_batch(
        self,
        plot_points: list,
        outline: dict,
        characters: dict,
        previous_scenes: list = None,
        scene_id_offset: int = 0,
    ) -> Optional[List[dict]]:
        """
        B-3: 全 batch 模式 — 一次 API 调用生成多个 scenes 的 JSON 数组。

        Args:
            plot_points: 要生成的 plot_point 列表
            outline: Stage 1 大纲
            characters: Stage 2 角色
            previous_scenes: 前序 scenes（用于第 2 批的上下文）
            scene_id_offset: scene_id 起始偏移（第 2 批 = 第 1 批数量）

        Returns:
            scenes 列表，或 None（失败时）
        """
        n = len(plot_points)
        if n == 0:
            return []

        # 动态 max_tokens: scenes * 1500 * 2，上限 64000
        dynamic_max_tokens = min(n * 1500 * 2, 64000)

        # 构建 batch prompt
        prompt = self._build_batch_prompt(
            plot_points=plot_points,
            outline=outline,
            characters=characters,
            previous_scenes=previous_scenes or [],
            scene_id_offset=scene_id_offset,
        )

        # B-7: 使用带重试的 LLM 调用
        try:
            content = await self._call_llm_with_retry(prompt, max_tokens=dynamic_max_tokens)
        except Exception as e:
            print(f"  [B-3] batch LLM 调用异常: {e}")
            return None

        # B-2 诊断: 保存 batch 原始响应便于 debug
        try:
            import os
            os.makedirs("forclaudeweb", exist_ok=True)
            with open("forclaudeweb/stage3_batch_raw_response.txt", "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  [B-3] batch 原始响应已保存 (长度: {len(content)} 字符)")
        except Exception:
            pass

        # 解析 JSON 数组
        scenes = self._extract_batch_json(content)
        if not scenes:
            print(f"  [B-3] batch JSON 解析失败，content 前 500 字: {content[:500]}")
            return None

        # 验证每个 scene
        validated = []
        for i, scene in enumerate(scenes):
            expected_id = scene_id_offset + i + 1
            self._validate_scene(scene, expected_id)
            validated.append(scene)

        return validated if validated else None

    def _build_batch_prompt(
        self,
        plot_points: list,
        outline: dict,
        characters: dict,
        previous_scenes: list,
        scene_id_offset: int = 0,
    ) -> str:
        """构建 batch 模式的 prompt"""
        n = len(plot_points)

        # 角色信息
        chars_info = []
        chars_props = []
        for char in characters.get("characters", []):
            char_id = char.get('id')
            char_name = char.get('name')
            chars_info.append(f"- {char_id}: {char_name} ({char.get('role', 'character')})")
            clothing = char.get('clothing', {})
            accessories = clothing.get('accessories', [])
            if accessories:
                chars_props.append(f"  - {char_name} ({char_id}): {', '.join(accessories)}")
            else:
                chars_props.append(f"  - {char_name} ({char_id}): 无配饰")

        chars_str = "\n".join(chars_info)
        chars_props_str = "\n".join(chars_props) if chars_props else "  （无角色定义配饰）"

        # 关系块
        relationships_block = ""
        if self._family_relationships:
            rel_lines = []
            for rel in self._family_relationships:
                if isinstance(rel, dict):
                    from_char = rel.get("from", "")
                    to_char = rel.get("to", "")
                    relation = rel.get("relationship", "")
                    if from_char and to_char and relation:
                        rel_lines.append(f"  - {from_char} → {to_char}: {relation}")
                elif isinstance(rel, str):
                    rel_lines.append(f"  - {rel}")
            if rel_lines:
                relationships_block = (
                    "\n\n## CHARACTER RELATIONSHIPS\n"
                    "Use these relationships to inform dialogue tone, forms of address, "
                    "and emotional dynamics between characters:\n"
                    + "\n".join(rel_lines)
                )

        # 场景位置
        locations = outline.get("unique_locations", [])
        if locations:
            locations_lines = []
            for loc in locations:
                loc_id = loc.get("location_id", loc.get("id", "unknown"))
                display_name = loc.get("display_name", loc.get("name", "未知场景"))
                loc_type = loc.get("location_type", "")
                locations_lines.append(f"  - {loc_id}: {display_name} ({loc_type})")
            locations_str = "\n".join(locations_lines)
            first_location_id = locations[0].get("location_id", locations[0].get("id", "L001"))
        else:
            locations_str = "  - default_location: 默认场景"
            first_location_id = "default_location"

        # 构建 plot_points 描述
        pp_lines = []
        for i, pp in enumerate(plot_points):
            sid = scene_id_offset + i + 1
            beat = pp.get("beat", f"plot_{sid}")
            desc = pp.get("description", "")
            dur = pp.get("estimated_duration_seconds", 30)
            target_words = max(80, int(dur * 4))
            # B-3: 旧公式 int(dur/6) 产出 5 beats/scene → 30 shots/短篇
            # DEC-011 短篇~18 shots ÷ 6 scenes ≈ 3 beats/scene
            target_beats = max(2, int(dur / 10))
            pp_lines.append(
                f"### Scene {sid}\n"
                f"- 节拍类型: {beat}\n"
                f"- 描述: {desc}\n"
                f"- 目标时长: {dur}秒\n"
                f"- 目标旁白字数: ≥{target_words}字\n"
                f"- 目标 action_beats 数: ≥{target_beats}"
            )
        pp_block = "\n\n".join(pp_lines)

        # 前情提要
        previous_context = ""
        if previous_scenes:
            last = previous_scenes[-1]
            last_narration = last.get("narration", "")
            previous_context = f"""
## 前情提要（前序 {len(previous_scenes)} 场已完成）
上一场景: {last.get('scene_heading', '')}
结束状态: {last_narration[-80:] if len(last_narration) > 80 else last_narration}
"""

        return f"""一次性生成 {n} 个 scenes 的完整分场剧本。

═══════════════════════════════════════════════════════════
CRITICAL: CHARACTER CONSISTENCY RULES
═══════════════════════════════════════════════════════════

You MUST only use props and accessories that are DEFINED in the character data.
DO NOT invent new accessories, clothing items, or physical features.

ALLOWED props for each character (from characters.json):
{chars_props_str}

❌ FORBIDDEN: Adding glasses, hats, bags, umbrellas, or any item NOT in the character definition
✅ CORRECT: Use only defined accessories, use natural alternatives for plot needs

═══════════════════════════════════════════════════════════

## 角色
{chars_str}
{relationships_block}

## 可用场景位置
{locations_str}

⚠️ location_id 必须完全匹配上述列表中的值（如 "{first_location_id}"）。
{previous_context}

## 需要生成的 {n} 个 Scenes

{pp_block}

═══════════════════════════════════════════════════════════
## 对话与内心独白要求（CRITICAL）
═══════════════════════════════════════════════════════════

每个 action_beat 必须有至少 1 个对应的 dialogue_beat（对话或内心独白）。
dialogue_beats 中 thought 类型 ≥20%。
对话必须简洁有力，每句≤20字。
thought 类型用括号包裹：line="（内心独白内容）"

### DIALOGUE NATURALNESS RULES
1. Dialogue should not contradict common knowledge
2. Each line should have an unambiguous subject
3. Dialogue tone should match speaker's age and identity
4. Use natural spoken language, not written prose
5. Use correct kinship terms based on CHARACTER RELATIONSHIPS

═══════════════════════════════════════════════════════════

## 输出格式

直接输出 JSON 数组（不要```json```包裹，不要任何解释文字）。
每个元素是一个 scene 对象，格式如下：

[
    {{
        "scene_id": {scene_id_offset + 1},
        "scene_heading": "EXT/INT. LOCATION - TIME - WEATHER",
        "plot_point": "beat_name",
        "location_id": "{first_location_id}",
        "time_of_day": "时间",
        "weather": "天气",
        "lighting_condition": "光线条件",
        "atmosphere": {{
            "mood": "English only mood word",
            "sound_design_hint": "音效提示",
            "temperature_feel": "温度感受"
        }},
        "characters_in_scene": ["char_001"],
        "action_beats": [
            {{"beat_id": "1a", "action": "动作描述", "duration_hint": 5, "emotional_note": "情绪"}}
        ],
        "dialogue_beats": [
            {{"beat_id": "1a_dialogue", "type": "dialogue", "speaker": "char_001", "line": "对话≤20字", "emotion": "情绪"}}
        ],
        "narration": "TTS朗读旁白，有文学性，详细描写人物神态动作、内心活动、环境氛围...",
        "narration_tone": "情绪基调",
        "narration_pace": "节奏"
    }}
]

必须输出 {n} 个 scene 对象，scene_id 从 {scene_id_offset + 1} 到 {scene_id_offset + n}。"""

    def _extract_batch_json(self, content: str) -> Optional[List[dict]]:
        """
        从 batch 模式的 LLM 响应中提取 JSON 数组。

        RB-2: 增强解析逻辑 — 处理 markdown 代码块、trailing comma、
        注释行、BOM、以及各种 LLM 输出格式偏差。
        """
        import re

        def _try_parse_array(text: str) -> Optional[List[dict]]:
            """尝试解析 JSON 数组，包含自动修复常见格式问题"""
            if not text or not text.strip():
                return None

            text = text.strip()

            # 去除 BOM
            if text.startswith('\ufeff'):
                text = text[1:]

            # 移除 // 行注释（JSON 不支持但 LLM 常输出）
            text = re.sub(r'//[^\n]*', '', text)

            # 移除 /* ... */ 块注释
            text = re.sub(r'/\*[\s\S]*?\*/', '', text)

            # 直接尝试解析
            try:
                result = json.loads(text)
                if isinstance(result, list) and len(result) > 0:
                    return result
            except json.JSONDecodeError:
                pass

            # 修复 trailing comma: },] 或 }, ]
            fixed = re.sub(r',\s*(\])', r'\1', text)
            # 修复 trailing comma in objects: ,}
            fixed = re.sub(r',\s*(\})', r'\1', fixed)
            try:
                result = json.loads(fixed)
                if isinstance(result, list) and len(result) > 0:
                    print(f"  [RB-2] JSON trailing comma 已修复")
                    return result
            except json.JSONDecodeError:
                pass

            # R4-4: 修复 LLM 在 JSON 字符串值中输出未转义的双引号
            # 例如: "emotion": "声音在"走"字上轻微破碎"
            # 策略: 遍历字符，在字符串内部检测到的 " 如果后面不是 JSON 分隔符 (,}]:)
            # 则替换为中文引号 \u201c（左双引号）
            def _fix_inner_quotes(src: str) -> str:
                out = []
                i = 0
                in_str = False
                while i < len(src):
                    ch = src[i]
                    if ch == '\\' and in_str and i + 1 < len(src):
                        out.append(ch)
                        out.append(src[i + 1])
                        i += 2
                        continue
                    if ch == '"':
                        if not in_str:
                            in_str = True
                            out.append(ch)
                        else:
                            # Is this the real end of the string?
                            rest = src[i + 1:].lstrip()
                            if not rest or rest[0] in ',}]:':
                                in_str = False
                                out.append(ch)
                            else:
                                # Unescaped inner quote — replace with Chinese left quote
                                out.append('\u201c')
                    else:
                        out.append(ch)
                    i += 1
                return ''.join(out)

            quote_fixed = _fix_inner_quotes(fixed)
            if quote_fixed != fixed:
                try:
                    result = json.loads(quote_fixed)
                    if isinstance(result, list) and len(result) > 0:
                        print(f"  [R4-4] JSON 未转义内部引号已修复")
                        return result
                except json.JSONDecodeError:
                    pass

            return None

        # 策略 1: 提取 ```json ... ``` 代码块（支持 ```JSON 和 ``` 无标签）
        code_block_patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```JSON\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
        ]
        for pattern in code_block_patterns:
            match = re.search(pattern, content)
            if match:
                result = _try_parse_array(match.group(1))
                if result:
                    print(f"  [RB-2] ✅ 从 markdown 代码块中提取 JSON 数组 ({len(result)} scenes)")
                    return result

        # 策略 2: 直接解析整个内容
        result = _try_parse_array(content)
        if result:
            print(f"  [RB-2] ✅ 直接解析 JSON 数组 ({len(result)} scenes)")
            return result

        # 策略 3: 提取最外层 [ ... ]（处理 LLM 在 JSON 前后添加解释文字的情况）
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start:
            extracted = content[start:end + 1]
            result = _try_parse_array(extracted)
            if result:
                print(f"  [RB-2] ✅ 从 [...] 范围提取 JSON 数组 ({len(result)} scenes)")
                return result

            # 策略 3b: 如果提取后仍失败，尝试逐层剥离修复
            # 有时 LLM 输出的 JSON 数组中间有截断，尝试找到最后一个完整的 }
            # 然后截断到那里加 ]
            last_complete = extracted.rfind('}')
            if last_complete > 0:
                truncated = extracted[:last_complete + 1] + ']'
                result = _try_parse_array(truncated)
                if result:
                    print(f"  [RB-2] ✅ 截断修复后提取 JSON 数组 ({len(result)} scenes)")
                    return result

        print(f"  [RB-2] ❌ 所有 JSON 提取策略均失败，content 前 200 字: {content[:200]}")
        return None

    async def _call_llm_with_retry(self, prompt: str, max_tokens: int = 8631) -> str:
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
                    logger.warning(f"[ScreenplayWriter] ⚠️ 529 overloaded 重试 {retry}/3，等待 {wait}s")
                else:
                    if retry > 2:
                        break  # 非 529 最多 3 次尝试
                    wait = 2 ** retry  # 2s, 4s
                    print(f"    [RB-3] LLM 重试 {retry}/2，等待 {wait}s...")
                    logger.warning(f"[ScreenplayWriter] ⚠️ LLM 重试 {retry}/2，等待 {wait}s, 上次错误: {last_error}")
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
                            messages=[{"role": "user", "content": prompt}]
                        )
                        content = response.content[0].text
                        call_elapsed = time.time() - call_start
                        logger.info(f"[ScreenplayWriter] Claude 响应: {len(content)} chars, 耗时 {call_elapsed:.1f}s")
                    except Exception as ce:
                        last_error = ce
                        # 检测 529 状态码
                        error_str = str(ce)
                        if '529' in error_str or 'overloaded' in error_str.lower():
                            is_529 = True
                            max_retries = 4
                            print(f"    [RB-3] ⚠️ Claude 529 overloaded")
                            logger.warning(f"[ScreenplayWriter] ⚠️ Claude 529 overloaded")
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
                            config={"max_output_tokens": max_tokens}
                        )
                        content = response.text
                        call_elapsed = time.time() - call_start
                        logger.info(f"[ScreenplayWriter] Gemini 响应: {len(content)} chars, 耗时 {call_elapsed:.1f}s")
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
        logger.error(f"[ScreenplayWriter] ❌ LLM 调用失败 ({retry + 1} 次尝试, 总耗时 {total_elapsed:.1f}s): {last_error}")
        raise ValueError(f"LLM 调用失败（{retry + 1} 次尝试）: {last_error}")

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
        # B-3: DEC-011 短篇~18 shots ÷ 6 scenes ≈ 3 beats/scene
        target_beats = max(2, int(duration / 10))
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

        # T32: 构建家庭/人物关系块（格式参考 T24 在 Stage 4 的注入方式）
        relationships_block = ""
        if self._family_relationships:
            rel_lines = []
            for rel in self._family_relationships:
                if isinstance(rel, dict):
                    from_char = rel.get("from", "")
                    to_char = rel.get("to", "")
                    relation = rel.get("relationship", "")
                    if from_char and to_char and relation:
                        rel_lines.append(f"  - {from_char} → {to_char}: {relation}")
                elif isinstance(rel, str):
                    rel_lines.append(f"  - {rel}")
            if rel_lines:
                relationships_block = (
                    "\n\n## CHARACTER RELATIONSHIPS\n"
                    "Use these relationships to inform dialogue tone, forms of address, "
                    "and emotional dynamics between characters:\n"
                    + "\n".join(rel_lines)
                )

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

═══════════════════════════════════════════════════════════
PLOT POINT COVERAGE (MANDATORY):
Every plot_point from the outline MUST map to exactly one scene.
Do NOT merge, skip, or omit any plot_point.
This is scene {scene_id} of {total_plot_points} — you MUST generate this scene fully.
═══════════════════════════════════════════════════════════

## 剧情节点
- 节拍类型: {beat_name}
- 描述: {description}
- 目标时长: {duration}秒
{previous_context}
## 角色
{chars_str}
{relationships_block}
## 可用场景位置
以下是本故事中定义的所有场景位置，你必须从中选择：
{locations_str}

⚠️ 重要：location_id 必须完全匹配上述列表中的值（如 "{first_location_id}"），不要自己编造新的ID。

═══════════════════════════════════════════════════════════
## 对话与内心独白要求（CRITICAL）
═══════════════════════════════════════════════════════════

每个 action_beat 必须有至少 1 个对应的 dialogue_beat（对话或内心独白）。
不允许 action_beat 没有任何 dialogue_beat 对应（"裸奔"）。

每个 dialogue_beat 必须有 `type` 字段区分类型：
- "dialogue": 外部对话（角色对别人说的话）
- "thought": 内心独白（角色的内心想法/感受/回忆）

dialogue_beats 分布目标：
- dialogue 类型: 60-70%（对话是推动故事的主要方式）
- thought 类型: 20-30%（内心独白让读者进入角色内心）
- thought 占比 ≥20%（5 beats 场景至少 1 个 thought，6+ beats 场景至少 2 个 thought）

对话写作原则：
- 对话必须简洁有力，每句≤20字，像真实漫画气泡中的文字
- 体现角色性格差异（粗犷vs温柔、直白vs含蓄）
- 包含情绪标注，便于后续分镜确定气泡类型
- 独处场景：自言自语、内心独白、回忆中的对话、电话/短信
- thought 类型用括号包裹：line="（内心独白内容）"

### 对话明确化规则（CRITICAL — NO VAGUE REFERENCES）

关键剧情词必须在对话中**显式表达**，禁止使用模糊代称：
❌ 模糊: "那个行业"、"那件事"、"你知道的"、"那个考试"、"那边的情况"
✅ 明确: "公务员考试"、"父亲的葬礼"、"转学手续"、"店铺三年租约"

前30%对话必须完成核心冲突定义：
- 第1-2组 dialogue_beats 必须让观众明确理解：谁要什么？谁反对什么？矛盾焦点是什么？
- 使用具体的事件、术语、地名、人名，不要留给观众猜测
- 例: 故事关于"女儿不愿考公"→ 前2组对话必须出现"公务员"、"报名表"、"体制内"等具体词

### DIALOGUE NATURALNESS RULES (IMPORTANT)

When writing dialogue_beats, you SHOULD follow these guidelines to ensure natural, believable dialogue:

1. **LOGICAL COMMON SENSE**: Dialogue should not contradict common knowledge or physical reality.
   Actions and references in dialogue should make sense in context.
   ❌ BAD: "这西瓜趁热吃！" (watermelon is eaten cold, not hot)
   ❌ BAD: "快把冰淇淋放微波炉热一下" (ice cream is not meant to be heated)
   ✅ GOOD: "这西瓜冰过了，快来吃！"
   ✅ GOOD: "汤趁热喝，凉了就不好喝了"

2. **CLEAR SUBJECT**: Each line of dialogue should have an unambiguous subject.
   Avoid omitting subjects when it could cause confusion about who is doing what.
   ❌ BAD: "去拿一下" (who should go? unclear)
   ❌ BAD: "不是说好了吗" (who agreed? about what?)
   ✅ GOOD: "小糖，帮奶奶去拿一下碗筷"
   ✅ GOOD: "建国，我们不是说好让她自己选吗"

3. **AGE AND IDENTITY MATCH**: Dialogue tone, vocabulary, and references should match
   the speaker's age, education, and social role. A child should not speak like an adult professor;
   an elderly person should not use teen slang (unless intentionally for comedic effect).
   ❌ BAD: 6-year-old says "从辩证法的角度来看..."
   ✅ GOOD: 6-year-old says "可是为什么呀？"
   ❌ BAD: elderly grandfather says "这也太绝了吧 yyds"
   ✅ GOOD: elderly grandfather says "这个味道，和你奶奶当年做的一模一样"

4. **COLLOQUIAL NATURALNESS**: Dialogue should sound like real spoken language,
   not written prose or formal essays. Use contractions, sentence fragments, and
   natural speech rhythms that people actually use in daily conversation.
   ❌ BAD: "我认为我们应该对此事进行深入的探讨与分析"
   ✅ GOOD: "我觉得这事儿得好好聊聊"
   ❌ BAD: "此刻我的内心充满了感动与温暖"
   ✅ GOOD: "（鼻子一酸，说不出话来）"

5. **KINSHIP ADDRESS CLARITY**: In multi-generational family stories, each character
   SHOULD use kinship terms that unambiguously identify the person being addressed,
   from the SPEAKER's perspective. Refer to the CHARACTER RELATIONSHIPS data (if provided
   above) to determine the correct form of address between any two characters.
   - A child calling their parent's parent: "爷爷"/"奶奶"/"外公"/"外婆" (NOT "爸"/"妈")
   - A parent talking to their child: use the child's name or "儿子"/"女儿"/"闺女"
   - When "妈" could refer to multiple women (grandmother, mother, aunt), add the
     character's name or a distinguishing word to disambiguate: "你妈" vs "奶奶" vs "婶婶"
   - Narrator (旁白) SHOULD also use unambiguous references: "陈晓桐的母亲" rather than
     just "妈妈" when both a grandmother and a mother are present
   ❌ BAD: (3-generation story) child says "妈，你看" — unclear if addressing mother or grandmother
   ✅ GOOD: (3-generation story) child says "妈妈，你看" to mother; says "奶奶，你看" to grandmother
   ❌ BAD: narrator says "妈妈走了过来" when both mother and grandmother are in the scene
   ✅ GOOD: narrator says "林秀梅走了过来" or "晓桐的母亲走了过来"

═══════════════════════════════════════════════════════════

## 输出要求
这个scene必须包含：
- 至少 {target_beats} 个 action_beats
- 每个 action_beat 必须有至少 1 个对应的 dialogue_beat（dialogue 或 thought 类型）
- dialogue_beats 中 thought 类型 ≥20%（5 beats 至少 1 个，6+ beats 至少 2 个）
- 每个 dialogue_beat 必须有 type 字段（"dialogue" 或 "thought"）
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
    "dialogue_beats": [
        {{"beat_id": "{scene_id}a_dialogue", "type": "dialogue", "speaker": "char_001", "line": "对话内容（≤20字）", "emotion": "情绪标注"}},
        {{"beat_id": "{scene_id}a_dialogue_2", "type": "dialogue", "speaker": "char_002", "line": "回应内容（≤20字）", "emotion": "情绪标注"}},
        {{"beat_id": "{scene_id}b_thought", "type": "thought", "speaker": "char_001", "line": "（角色内心独白≤20字）", "emotion": "情绪标注"}}
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
async def write_screenplay(outline: dict, characters: dict, family_relationships: list = None) -> dict:
    """便捷函数：生成分场剧本"""
    writer = ScreenplayWriter()
    return await writer.write(outline, characters, family_relationships=family_relationships)
