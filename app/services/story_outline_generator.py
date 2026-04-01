"""
Stage 1: StoryOutlineGenerator

Phase 2.0 第一阶段 - 故事大纲生成器
将用户idea转化为结构化的故事大纲，包含：
- 情感弧线 (emotional_arc)
- 叙事节奏 (narrative_pace)
- 视觉风调 (visual_tone)
- 角色概览 (characters_overview)
- 情节节拍 (plot_points)
- 场景列表 (unique_locations)
"""

import json
import logging
from typing import Optional
import anthropic
from google import genai
from app.config import settings

logger = logging.getLogger("xuhua")


class StoryOutlineGenerator:
    """
    故事大纲生成器

    输入: idea, style_preset, target_duration_minutes
    输出: outline.json

    模型优先级: Claude Sonnet 4.6 (主) → Gemini 3 Flash (备用)
    """

    def __init__(self):
        # 主模型: Claude Sonnet 4.6
        self.claude_client = None
        self.claude_model = "claude-sonnet-4-6"
        if settings.ANTHROPIC_API_KEY:
            self.claude_client = anthropic.AsyncAnthropic(
                api_key=settings.ANTHROPIC_API_KEY
            )

        # 备用模型: Gemini 3 Flash
        self.gemini_client = None
        self.gemini_model = "gemini-3.1-flash-lite-preview"
        if settings.GEMINI_API_KEY:
            self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def _build_user_reference_context(
        character_refs_analysis: list[dict] | None = None,
        scene_refs_analysis: list[dict] | None = None,
        custom_style_name: str | None = None,
    ) -> str:
        """构建用户参考图上下文段，追加到 _build_prompt 末尾。
        当所有参考为空时返回空字符串。"""
        sections = []

        if character_refs_analysis:
            char_lines = []
            for i, char in enumerate(character_refs_analysis, 1):
                desc = char.get("description_zh", "未知角色")
                char_lines.append(f"- 角色{i}: {desc}")
            sections.append(
                f"""### 用户提供的角色参考（共 {len(character_refs_analysis)} 个）
{chr(10).join(char_lines)}
请确保 characters_overview 中的角色设定贴合这些参考的外貌和气质。角色数量可以多于参考数（系统会补充原创角色），但参考中的角色必须出现且描述一致。"""
            )

        if scene_refs_analysis:
            scene_lines = []
            for i, scene in enumerate(scene_refs_analysis, 1):
                desc = scene.get("description_zh", "未知场景")
                scene_lines.append(f"- 场景{i}: {desc}")
            sections.append(
                f"""### 用户提供的场景参考（共 {len(scene_refs_analysis)} 个）
{chr(10).join(scene_lines)}
请确保 unique_locations 中至少包含这些场景或与之高度相似的场景。可以添加额外场景以丰富故事。"""
            )

        if custom_style_name:
            sections.append(
                f"""### 用户选择的自定义视觉风格
用户上传了风格参考图，期望的视觉风格为: {custom_style_name}
请确保 visual_tone 的 color_palette 和整体氛围与此风格一致。"""
            )

        if not sections:
            return ""

        return """

## 用户提供的视觉参考（IMPORTANT: 大纲必须贴合这些参考）

""" + "\n\n".join(sections)

    async def generate(
        self,
        idea: str,
        style_preset: str,
        target_duration_minutes: int = 3,
        language: str = "zh-CN",
        character_count: int = 3,
        character_refs_analysis: list[dict] | None = None,
        scene_refs_analysis: list[dict] | None = None,
        custom_style_name: str | None = None,
    ) -> dict:
        """
        生成故事大纲

        Args:
            idea: 用户创意
            style_preset: 视觉风格预设 (realistic, illustration, ink, etc.)
            target_duration_minutes: 目标时长（分钟）
            language: 语言
            character_count: 角色数量
            character_refs_analysis: 用户角色参考图分析结果
            scene_refs_analysis: 用户场景参考图分析结果
            custom_style_name: 用户自定义风格名

        Returns:
            outline dict
        """
        # 计算目标指标
        min_shots = max(23, target_duration_minutes * 8)  # 每分钟约8个shot
        target_seconds = target_duration_minutes * 60

        prompt = self._build_prompt(
            idea=idea,
            style_preset=style_preset,
            target_duration_minutes=target_duration_minutes,
            min_shots=min_shots,
            target_seconds=target_seconds,
            language=language,
            character_count=character_count
        )

        # 追加用户参考图上下文（Prompt 4）
        ref_context = self._build_user_reference_context(
            character_refs_analysis=character_refs_analysis,
            scene_refs_analysis=scene_refs_analysis,
            custom_style_name=custom_style_name,
        )
        if ref_context:
            prompt = prompt.rstrip() + "\n" + ref_context + "\n\n现在开始生成故事大纲："
        else:
            prompt = prompt.rstrip() + "\n\n现在开始生成故事大纲："

        logger.info(f"[StoryOutlineGenerator] 生成故事大纲...")
        logger.info(f"  idea: {idea[:80]}{'...' if len(idea) > 80 else ''}")
        logger.info(f"  style: {style_preset}")
        logger.info(f"  target: {target_duration_minutes}分钟, ≥{min_shots} shots")

        content = None
        provider = None

        # System prompt (AI-ML 设计)
        system_prompt = """You are a professional story planner and visual director for an AI-powered webtoon/short video generation system.

Always respond with valid JSON only. No markdown code blocks, no explanation, no text before or after the JSON. Output a single JSON object starting with { and ending with }.

Critical rules:
- Chinese text for: title, logline, summary, character names, display_name, plot descriptions, mood, ending descriptions, signage_text, description, personality, emotional_journey
- English text for: title_en, name_en, emotional_arc values, narrative_pace, visual_tone fields, color_palette, archetype, interior_description, exterior_description, key_visual_elements
- All ending_options must have 3 distinct options with meaningful differences
- All characters_overview entries must include description (20-30 Chinese chars, appearance) and personality (10-20 Chinese chars, traits)
- mood must be exactly one of: 感人 / 治愈 / 热血 / 悬疑 / 浪漫 / 温馨"""

        # 优先使用 Claude Sonnet 4.6
        if self.claude_client:
            try:
                logger.info(f"  [尝试 Claude Sonnet 4.6]")
                response = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=16384,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    system=system_prompt,
                )
                content = response.content[0].text
                provider = "claude"
            except Exception as e:
                logger.info(f"  [Claude失败: {e}，尝试Gemini备用]")

        # Fallback到Gemini 3 Flash
        if content is None and self.gemini_client:
            try:
                logger.info(f"  [尝试 Gemini 3.1 Flash Lite]")
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                    config={"max_output_tokens": 8631}
                )
                content = response.text
                provider = "gemini"
            except Exception as e:
                logger.info(f"[StoryOutlineGenerator] ❌ Gemini也失败: {e}")
                raise

        if content is None:
            raise ValueError("无可用的LLM服务")

        # 提取JSON
        outline = self._extract_json(content)

        if outline:
            # 验证必要字段
            self._validate_outline(outline, min_shots)
            logger.info(f"[StoryOutlineGenerator] ✅ 大纲生成成功 (via {provider})")
            logger.info(f"  title: {outline.get('title', 'N/A')}")
            logger.info(f"  characters: {len(outline.get('characters_overview', []))}个")
            logger.info(f"  plot_points: {len(outline.get('plot_points', []))}个")
            logger.info(f"  locations: {len(outline.get('unique_locations', []))}个")
            return outline
        else:
            logger.info(f"[StoryOutlineGenerator] ❌ JSON提取失败")
            logger.info(f"  provider: {provider}")
            logger.info(f"  response length: {len(content)} chars")
            logger.info(f"  response preview: {content[:500]}")
            raise ValueError("无法从LLM响应中提取JSON")

    def _build_prompt(
        self,
        idea: str,
        style_preset: str,
        target_duration_minutes: int,
        min_shots: int,
        target_seconds: int,
        language: str,
        character_count: int
    ) -> str:
        """构建故事大纲生成prompt"""

        style_descriptions = {
            "realistic": "写实摄影风格，电影质感，真实光影",
            "illustration": "精美插画风格，色彩丰富，艺术感强",
            "ink": "中国水墨风格，留白意境，传统美学",
            "cyberpunk": "赛博朋克风格，霓虹灯光，未来都市",
            "cartoon": "3D卡通风格，色彩明快，Pixar质感",
            "anime": "日本动画风格，精致线条，情感表达",
            "watercolor": "水彩画风格，柔和渲染，梦幻氛围",
            "ghibli": "吉卜力风格，手绘质感，温暖治愈"
        }

        style_desc = style_descriptions.get(style_preset, style_preset)

        return f"""你是一位专业的故事策划师和视觉导演。根据用户创意，生成一个结构化的故事大纲。

## 用户创意
{idea}

## 项目参数
- 视觉风格: {style_desc}
- 目标时长: {target_duration_minutes}分钟 ({target_seconds}秒)
- 最少镜头数: {min_shots}个shots
- 角色数量: {character_count}个主要角色
- 语言: {language}

## 输出要求

请严格按照以下JSON格式输出故事大纲：

```json
{{
    "title": "故事标题（中文）",
    "title_en": "Story Title in English",
    "logline": "一句话故事梗概（50字以内）",
    "summary": "故事简介（100-200字，用2-3句话描述核心故事情节，比logline更详细但比plot_points更精炼）",

    "ending_options": [
        {{"id": "ending_1", "description": "结局选项1描述（1句话）"}},
        {{"id": "ending_2", "description": "结局选项2描述（1句话）"}},
        {{"id": "ending_3", "description": "结局选项3描述（1句话）"}}
    ],

    "mood": "从以下选一个最匹配的: 感人 / 治愈 / 热血 / 悬疑 / 浪漫 / 温馨",

    "emotional_arc": {{
        "opening": "情感起点（如: isolated_melancholy, peaceful_ordinary, excited_anticipation）",
        "midpoint": "情感转折（如: tentative_connection, growing_tension, unexpected_discovery）",
        "climax": "情感高潮（如: emotional_revelation, confrontation, breakthrough）",
        "resolution": "情感终点（如: bittersweet_hope, warm_closure, open_ended）"
    }},

    "narrative_pace": "slow_burn / steady / fast_paced",

    "visual_tone": {{
        "overall_mood": "整体情绪基调（如: melancholic_intimate, warm_nostalgic, tense_mysterious）",
        "lighting_style": "光影风格（如: low_key_dramatic, high_key_bright, natural_soft, chiaroscuro）",
        "color_palette": ["primary color in English", "secondary color in English", "accent color in English"],
        "composition_style": "构图风格（如: negative_space_isolation, dynamic_diagonal, symmetrical_formal）"
    }},

    "target_metrics": {{
        "min_shots": {min_shots},
        "target_duration_seconds": {target_seconds},
        "max_seconds_per_shot": 8
    }},

    "characters_overview": [
        {{
            "role": "protagonist / supporting / background",
            "name_suggestion": "建议的角色中文名",
            "name_en": "English Name",
            "description": "外貌简述，20-30字中文（如：28岁程序员，戴黑框眼镜，穿灰色卫衣，背双肩包）",
            "personality": "性格简述，10-20字中文（如：内向沉稳，不善表达但心思细腻）",
            "archetype": "角色原型（如: exhausted_office_worker, cheerful_student, wise_elder）",
            "age_range": "young_adult / adult / middle_aged / elderly / child / teen",
            "gender": "male / female",
            "family_role": "grandfather / grandmother / father / mother / son / daughter / granddaughter / grandson / uncle / aunt / friend / colleague / stranger / none",
            "emotional_journey": "角色的情感变化轨迹"
        }}
    ],

    "family_relationships": [
        {{
            "from": "char_name_1",
            "to": "char_name_2",
            "relationship": "grandfather_of / mother_of / father_of / sibling_of / spouse_of / friend_of / colleague_of"
        }}
    ],

    "plot_points": [
        {{
            "beat": "inciting_incident / first_turn / midpoint / crisis / climax / resolution",
            "description": "情节点描述",
            "estimated_duration_seconds": 30
        }}
    ],

    "unique_locations": [
        {{
            "location_id": "location_id_snake_case",
            "display_name": "场景显示名称（中文）",
            "location_type": "interior / exterior / both",
            "time_of_day": "night / dawn / morning / afternoon / golden_hour / dusk",
            "weather": "clear / cloudy / rainy / stormy / foggy / snowy",
            "atmosphere": "desolate_urban / cozy_warm / mysterious_quiet / tense_suspenseful",
            "interior_description": "English description of interior (if has interior)",
            "exterior_description": "English description of exterior (if has exterior)",
            "key_visual_elements": ["visual element 1 in English", "visual element 2 in English"],
            "signage_text": "店铺/建筑招牌上实际显示的文字（中文），无招牌则为空字符串"
        }}
    ]
}}
```

## 创作要点

1. **情感弧线**：故事需要有明确的情感起伏，opening→midpoint→climax→resolution
2. **视觉风调**：visual_tone会影响后续所有镜头的光影、色彩、构图
3. **角色差异**：每个角色必须有明显的视觉差异和性格特点
4. **场景利用**：unique_locations应该覆盖故事的主要发生地
5. **时长控制**：plot_points的estimated_duration_seconds总和应接近{target_seconds}秒
6. **家庭关系**：如果故事涉及家庭成员，characters_overview中的family_role必须准确标注，family_relationships必须完整记录角色间关系
7. **招牌文字**：如果 unique_location 是店铺、餐馆、客栈等有招牌的场所，signage_text 应填写该店铺在故事世界中的真实招牌名称（如 "李记桂花糕"、"百味居"）。signage_text 是用于图像生成的店铺招牌文字，不是开发标签。如果场所没有招牌（如街道、公园、家中），signage_text 为空字符串 ""。
8. **故事简介**：summary 要比 logline 更详细，但不是 plot_points 的罗列，是对故事核心情节的概括描述（100-200字）
9. **结局选项**：ending_options 三个选项应有明显差异（如：温馨/开放/反转），让用户有真实的选择感
10. **情绪基调**：mood 从6个预设值（感人/治愈/热血/悬疑/浪漫/温馨）中选最匹配的一个
11. **角色简述**：description 和 personality 是给前端用户看的中文简述，不是给图像生成用的英文描述。description 聚焦外貌特征（年龄、穿着、显著特征），personality 聚焦性格特点

## TITLE CONSISTENCY (IMPORTANT)

The story title SHOULD be consistent with the actual characters and their roles:
- If the title mentions a family role (e.g. "爷爷", "奶奶", "妈妈", "外婆"), at least one character
  in characters_overview MUST have the matching family_role and gender
- If the title implies a specific gender (e.g. "她的..." implies female), the relevant character
  SHOULD match that gender
- If the title references a specific relationship (e.g. "父子", "母女"), the family_relationships
  array MUST contain a matching relationship entry

Examples:
❌ BAD: title="外婆的抽屉" but no character has family_role="grandmother"
✅ GOOD: title="外婆的抽屉" with a character having family_role="grandmother", age_range="elderly", gender="female"
❌ BAD: title="父子对弈" but characters are mother and daughter
✅ GOOD: title="父子对弈" with family_relationships containing {{"from": "father_name", "to": "son_name", "relationship": "father_of"}}

## RELATIONSHIP CONSISTENCY RULES (IMPORTANT)

The family_relationships array SHOULD be logically consistent. When multiple relationships
are defined, they must form a coherent family tree — no contradictions.

### Triangle Consistency:
If A is grandfather_of C, and B is father_of C, then A SHOULD be father_of B (not grandfather_of B).
All three-way relationships must be transitively correct.

❌ BAD:
  {{"from": "陈守正", "to": "陈建国", "relationship": "grandfather_of"}}
  {{"from": "陈守正", "to": "陈晓桐", "relationship": "grandfather_of"}}
  {{"from": "陈建国", "to": "陈晓桐", "relationship": "father_of"}}
  (陈守正 cannot be grandfather_of his own son 陈建国 — should be father_of)

✅ GOOD:
  {{"from": "陈守正", "to": "陈建国", "relationship": "father_of"}}
  {{"from": "陈守正", "to": "陈晓桐", "relationship": "grandfather_of"}}
  {{"from": "陈建国", "to": "陈晓桐", "relationship": "father_of"}}
  (陈守正 is father of 陈建国, grandfather of 陈晓桐 — transitively correct)

### Spouse Transitivity:
If A is spouse_of B, and A is parent_of C, then B SHOULD also be parent_of C
(unless explicitly stated otherwise, e.g. step-parent).

### Self-Check Before Output:
Review all family_relationships entries together. For each person mentioned:
- Count how many generations separate them from the oldest character
- Verify that relationship labels match the generational distance
  (1 generation = parent_of, 2 generations = grandparent_of)

## 注意事项

- visual_tone.color_palette 中的颜色名必须是**英文**（如 "warm amber", "deep navy", "muted sage green"），不要使用中文颜色名
- 所有location的interior_description和exterior_description必须是**英文**
- 所有location的key_visual_elements必须是**英文**（用于图像生成）
- characters_overview只是概览，详细外貌在Stage 2生成
- plot_points要足够细致，每个情节点对应故事的一个关键转折
"""

    @staticmethod
    def _fix_unescaped_quotes(text: str) -> str:
        """修复 JSON 字符串内部未转义的 ASCII 双引号（状态机方案）。

        逐字符遍历，跟踪 in_string 状态。遇到 " 时用前瞻判断：
        - 跳过空白后下一个字符是 : , } ] 之一 → JSON 结构引号，保留
        - 否则 → 字符串内容引号，替换为中文弯引号
        """
        result = []
        i = 0
        in_string = False
        n = len(text)

        while i < n:
            ch = text[i]

            # 处理转义序列：\x 原样保留
            if in_string and ch == '\\' and i + 1 < n:
                result.append(ch)
                result.append(text[i + 1])
                i += 2
                continue

            if ch == '"':
                if not in_string:
                    # 进入字符串
                    in_string = True
                    result.append(ch)
                else:
                    # 在字符串内遇到 " — 前瞻判断是否为 JSON 结构关闭引号
                    j = i + 1
                    while j < n and text[j] in ' \t\r\n':
                        j += 1
                    next_ch = text[j] if j < n else ''

                    if next_ch in ':,}]' or j >= n:
                        # JSON 结构引号（后跟 : , } ] 或到末尾）→ 关闭字符串
                        in_string = False
                        result.append(ch)
                    else:
                        # 字符串内容引号 → 替换为左弯引号，找配对的右弯
                        result.append('\u201c')
                        # 向前找下一个 " 作为配对右弯引号
                        k = i + 1
                        while k < n and text[k] != '"':
                            result.append(text[k])
                            k += 1
                        if k < n:
                            # 找到配对 " → 替换为右弯引号
                            result.append('\u201d')
                            i = k + 1
                            continue
                        # 没找到配对 → 跳过已扫描的部分，避免二次追加
                        i = k
                        continue
            else:
                result.append(ch)

            i += 1

        return ''.join(result)

    def _extract_json(self, content: str) -> Optional[dict]:
        """从LLM响应中提取JSON"""
        import re

        # 预处理: 修复 JSON 字符串值中未转义的 ASCII 双引号
        content = self._fix_unescaped_quotes(content)

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

    def _validate_outline(self, outline: dict, min_shots: int) -> None:
        """验证大纲必要字段"""
        required_fields = [
            "title", "logline", "emotional_arc", "narrative_pace",
            "visual_tone", "characters_overview", "plot_points", "unique_locations"
        ]

        missing = [f for f in required_fields if f not in outline]
        if missing:
            raise ValueError(f"大纲缺少必要字段: {missing}")

        # 验证emotional_arc
        arc = outline.get("emotional_arc", {})
        arc_required = ["opening", "midpoint", "climax", "resolution"]
        arc_missing = [f for f in arc_required if f not in arc]
        if arc_missing:
            raise ValueError(f"emotional_arc缺少字段: {arc_missing}")

        # 验证visual_tone
        tone = outline.get("visual_tone", {})
        tone_required = ["overall_mood", "lighting_style", "color_palette"]
        tone_missing = [f for f in tone_required if f not in tone]
        if tone_missing:
            raise ValueError(f"visual_tone缺少字段: {tone_missing}")

        # 验证角色数量
        if len(outline.get("characters_overview", [])) == 0:
            raise ValueError("characters_overview不能为空")

        # 验证场景数量
        if len(outline.get("unique_locations", [])) == 0:
            raise ValueError("unique_locations不能为空")

        # 设置target_metrics（如果没有）
        if "target_metrics" not in outline:
            outline["target_metrics"] = {
                "min_shots": min_shots,
                "target_duration_seconds": min_shots * 6,  # 平均每shot 6秒
                "max_seconds_per_shot": 8
            }


# 便捷函数
async def generate_story_outline(
    idea: str,
    style_preset: str,
    target_duration_minutes: int = 3,
    language: str = "zh-CN",
    character_count: int = 3
) -> dict:
    """便捷函数：生成故事大纲"""
    generator = StoryOutlineGenerator()
    return await generator.generate(
        idea=idea,
        style_preset=style_preset,
        target_duration_minutes=target_duration_minutes,
        language=language,
        character_count=character_count
    )
