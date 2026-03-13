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
import os
from typing import Optional
import anthropic
from google import genai


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
        if os.getenv("ANTHROPIC_API_KEY"):
            self.claude_client = anthropic.Anthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )

        # 备用模型: Gemini 3 Flash
        self.gemini_client = None
        self.gemini_model = "gemini-3-flash-preview"
        if os.getenv("GEMINI_API_KEY"):
            self.gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    async def generate(
        self,
        idea: str,
        style_preset: str,
        target_duration_minutes: int = 3,
        language: str = "zh-CN",
        character_count: int = 3
    ) -> dict:
        """
        生成故事大纲

        Args:
            idea: 用户创意
            style_preset: 视觉风格预设 (realistic, illustration, ink, etc.)
            target_duration_minutes: 目标时长（分钟）
            language: 语言
            character_count: 角色数量

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

        print(f"[StoryOutlineGenerator] 生成故事大纲...")
        print(f"  idea: {idea}")
        print(f"  style: {style_preset}")
        print(f"  target: {target_duration_minutes}分钟, ≥{min_shots} shots")

        content = None
        provider = None

        # 优先使用 Claude Sonnet 4.6
        if self.claude_client:
            try:
                print(f"  [尝试 Claude Sonnet 4.6]")
                response = self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=8631,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
                provider = "claude"
            except Exception as e:
                print(f"  [Claude失败: {e}，尝试Gemini备用]")

        # Fallback到Gemini 3 Flash
        if content is None and self.gemini_client:
            try:
                print(f"  [尝试 Gemini 3 Flash]")
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                    config={"max_output_tokens": 8631}
                )
                content = response.text
                provider = "gemini"
            except Exception as e:
                print(f"[StoryOutlineGenerator] ❌ Gemini也失败: {e}")
                raise

        if content is None:
            raise ValueError("无可用的LLM服务")

        # 提取JSON
        outline = self._extract_json(content)

        if outline:
            # 验证必要字段
            self._validate_outline(outline, min_shots)
            print(f"[StoryOutlineGenerator] ✅ 大纲生成成功 (via {provider})")
            print(f"  title: {outline.get('title', 'N/A')}")
            print(f"  characters: {len(outline.get('characters_overview', []))}个")
            print(f"  plot_points: {len(outline.get('plot_points', []))}个")
            print(f"  locations: {len(outline.get('unique_locations', []))}个")
            return outline
        else:
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

现在开始生成故事大纲：
"""

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
