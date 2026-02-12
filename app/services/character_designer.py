"""
Stage 2: CharacterDesigner

Phase 2.0 第二阶段 - 角色设计器
基于故事大纲，为每个角色生成详细的视觉设计，包含：
- 完整的physical描述
- 详细的clothing描述
- 角色特定的导演指示 (character_specific_directions)
"""

import json
import os
from typing import Optional
import anthropic
from google import genai


class CharacterDesigner:
    """
    角色设计器

    输入: outline.json
    输出: characters.json

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

    async def design(self, outline: dict) -> dict:
        """
        设计角色

        Args:
            outline: Stage 1生成的故事大纲

        Returns:
            characters dict
        """
        characters_overview = outline.get("characters_overview", [])
        visual_tone = outline.get("visual_tone", {})
        title = outline.get("title", "")

        print(f"[CharacterDesigner] 设计{len(characters_overview)}个角色...")

        prompt = self._build_prompt(
            characters_overview=characters_overview,
            visual_tone=visual_tone,
            title=title,
            logline=outline.get("logline", "")
        )

        content = None
        provider = None

        # 优先使用 Gemini 3 Flash
        if self.gemini_client:
            try:
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                    config={"max_output_tokens": 8631}
                )
                content = response.text
                provider = "gemini"
            except Exception as e:
                print(f"  [Gemini失败: {e}，尝试Claude备用]")

        # Fallback到Claude Haiku
        if content is None and self.claude_client:
            try:
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
                print(f"[CharacterDesigner] ❌ Claude也失败: {e}")
                raise

        if content is None:
            raise ValueError("无可用的LLM服务")

        characters = self._extract_json(content)

        if characters:
            self._validate_characters(characters)
            print(f"[CharacterDesigner] ✅ 角色设计完成 (via {provider})")
            for char in characters.get("characters", []):
                print(f"  - {char.get('name', 'N/A')} ({char.get('role', 'N/A')})")
            return characters
        else:
            raise ValueError("无法从LLM响应中提取JSON")

    def _build_prompt(
        self,
        characters_overview: list,
        visual_tone: dict,
        title: str,
        logline: str
    ) -> str:
        """构建角色设计prompt"""

        characters_json = json.dumps(characters_overview, ensure_ascii=False, indent=2)

        return f"""你是一位专业的角色设计师和视觉艺术指导。根据故事大纲中的角色概览，为每个角色设计详细的视觉外观。

## 故事信息
- 标题: {title}
- 梗概: {logline}
- 视觉风调: {json.dumps(visual_tone, ensure_ascii=False)}

## 角色概览
{characters_json}

## 输出要求

请为每个角色生成详细的视觉设计，严格按照以下JSON格式输出：

```json
{{
    "characters": [
        {{
            "id": "char_001",
            "name": "角色中文名",
            "name_en": "Character English Name",
            "role": "protagonist / supporting / background",
            "character_type": "human",
            "gender": "male / female",
            "age_appearance": "child / teen / young_adult / adult / middle_aged / elderly",

            "personality": {{
                "core_trait": "核心性格特质（如: suppressed_dreamer, cheerful_optimist）",
                "surface_behavior": "表面行为特征（如: polite_withdrawn, energetic_talkative）",
                "internal_conflict": "内心冲突（如: career_vs_passion, duty_vs_desire）"
            }},

            "physical": {{
                "height": "tall / average / short",
                "build": "slim / athletic / average / stocky / slim_slightly_hunched",
                "face_shape": "oval / round / square / heart / rectangular / diamond",
                "skin_tone": "pale / fair / medium / olive / tan / dark",
                "hair_color": "具体颜色（如: jet black, chestnut brown, silver gray）",
                "hair_style": "具体发型（如: short messy unbrushed, long straight with bangs）",
                "hair_texture": "silky / fluffy / curly / wavy / coarse",
                "eye_color": "具体颜色（如: dark brown, bright blue, hazel）",
                "eye_shape": "round / almond / hooded / upturned / slightly_downturned",
                "eye_size": "large / medium / small",
                "eye_description": "眼神特质描述（如: tired with dark circles, bright and curious）",
                "eyebrows": "thick arched / thin straight / natural / straight_slightly_furrowed",
                "nose": "straight / button / prominent / aquiline / straight_medium",
                "lips": "thin / medium / full / thin_neutral",
                "distinctive_marks": ["特征1", "特征2"]
            }},

            "clothing": {{
                "top": "上衣详细描述（如: wrinkled white dress shirt with rolled sleeves）",
                "bottom": "下装详细描述（如: navy dress pants with slight creases）",
                "outerwear": "外套（如: damp gray wool overcoat）或 null",
                "footwear": "鞋子（如: scuffed black leather shoes）",
                "accessories": ["配饰1", "配饰2"],
                "style": "整体风格（如: disheveled_salaryman, casual_student）",
                "condition": "当前状态（如: rain-soaked, freshly pressed, worn and faded）"
            }},

            "character_specific_directions": {{
                "default_expression": "默认表情（如: weary_resignation, cheerful_smile）",
                "posture": "默认姿态（如: slightly_slouched, upright_confident）",
                "typical_gestures": ["常见动作1", "常见动作2", "常见动作3"]
            }}
        }}
    ]
}}
```

## 设计原则

1. **视觉差异化**：每个角色必须在外貌上有明显区别
   - 不同的发型/发色
   - 不同的服装风格
   - 不同的面部特征组合
   - **禁止所有角色使用"默认美女/帅哥"模板**

2. **角色一致性**：描述必须具体、固定，便于AI图像生成时保持一致
   - 颜色用具体词（jet black 而非 black）
   - 发型用详细描述（short messy with slight wave 而非 short）

3. **符合故事调性**：角色外观应与visual_tone匹配
   - 如果是melancholic故事，角色可以有疲惫、忧郁的特征
   - 如果是cheerful故事，角色应该有明亮、活泼的特征

4. **种族一致性**：同一故事中的角色应保持种族一致（除非剧情需要）
   - 中国故事的角色应有亚洲面孔特征

5. **服装状态**：clothing.condition应反映角色当前的状态
   - 如雨夜故事中角色应该是"rain-soaked"
   - 如加班后角色应该是"disheveled, tired appearance"

6. **ID规范**：角色id从char_001开始递增

现在开始设计角色：
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

    def _validate_characters(self, characters: dict) -> None:
        """验证角色数据"""
        chars = characters.get("characters", [])

        if len(chars) == 0:
            raise ValueError("characters数组不能为空")

        for i, char in enumerate(chars):
            char_id = char.get("id", f"char_{i+1:03d}")

            # 验证必要字段
            required = ["name", "name_en", "role", "character_type", "gender", "physical", "clothing"]
            missing = [f for f in required if f not in char]
            if missing:
                raise ValueError(f"角色 {char_id} 缺少必要字段: {missing}")

            # 验证physical
            physical = char.get("physical", {})
            physical_required = ["hair_color", "hair_style", "eye_color", "skin_tone", "face_shape"]
            physical_missing = [f for f in physical_required if f not in physical]
            if physical_missing:
                raise ValueError(f"角色 {char_id} physical缺少字段: {physical_missing}")

            # 验证clothing
            clothing = char.get("clothing", {})
            clothing_required = ["top", "bottom", "footwear", "style"]
            clothing_missing = [f for f in clothing_required if f not in clothing]
            if clothing_missing:
                raise ValueError(f"角色 {char_id} clothing缺少字段: {clothing_missing}")

            # 设置默认值
            if "age_appearance" not in char:
                char["age_appearance"] = "adult"

            if "character_specific_directions" not in char:
                char["character_specific_directions"] = {
                    "default_expression": "neutral",
                    "posture": "natural",
                    "typical_gestures": []
                }


# 便捷函数
async def design_characters(outline: dict) -> dict:
    """便捷函数：设计角色"""
    designer = CharacterDesigner()
    return await designer.design(outline)
