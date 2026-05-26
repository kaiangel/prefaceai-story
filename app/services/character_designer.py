"""
Stage 2: CharacterDesigner

Phase 2.0 第二阶段 - 角色设计器
基于故事大纲，为每个角色生成详细的视觉设计，包含：
- 完整的physical描述
- 详细的clothing描述
- 角色特定的导演指示 (character_specific_directions)
"""

import json
import time
import logging
from typing import Optional
import anthropic
from google import genai
from app.config import settings

logger = logging.getLogger("xuhua")


class CharacterDesigner:
    """
    角色设计器

    输入: outline.json
    输出: characters.json

    模型优先级: Claude Sonnet 4.6 (主) → Gemini 3 Flash (备用)
    """

    # Wave 13 #5e A (2026-05-25): 天然不穿人类衣物的 character_type。
    # 这些 type 的角色 (会说话的钟 / 鱼 / 向日葵 / 蚂蚁 / 火焰 / 车 等) 没有 top/bottom/
    # footwear 概念, LLM 给残缺 clothing 是合理的 → _validate_characters 对它们缺 clothing
    # 子字段降 warning 不 raise (防冲垮 pipeline)。
    # 不含 human / anthropomorphic_animal (穿衣) / 超自然人形 (supernatural/undead/
    # mythological/fantasy_creature 常人形穿衣) / robot / alien / giant / hybrid /
    # miniature / concept_personified / digital_virtual — 这些仍走严格 clothing 校验。
    NON_CLOTHING_TYPES: frozenset[str] = frozenset({
        "animal",            # 真实动物 (四足, 无服装)
        "aquatic",           # 水生 (鱼/章鱼等)
        "plant",             # 植物
        "insect",            # 昆虫
        "object",            # 物件 (钟/灯/书等)
        "elemental",         # 元素体 (火/水/风等)
        "vehicle_character",  # 载具角色 (车/船等)
    })

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

    async def design(self, outline: dict, style_preset: str | None = None) -> dict:
        """
        设计角色

        Args:
            outline: Stage 1生成的故事大纲
            style_preset: 视觉风格预设 ID（如 "gothic", "anime", "realistic"），
                          用于 STYLE_INFUSION_RULES 强制 LLM 输出风格一致的角色描述。
                          可选，默认 None（自动从 visual_tone 推断）。

        Returns:
            characters dict
        """
        characters_overview = outline.get("characters_overview", [])
        visual_tone = outline.get("visual_tone", {})
        title = outline.get("title", "")

        print(f"[CharacterDesigner] 设计{len(characters_overview)}个角色...")
        logger.info(f"[CharacterDesigner] 开始设计 {len(characters_overview)} 个角色")
        logger.info(f"  title: {title}, style_preset: {style_preset}")
        stage_start = time.time()

        prompt = self._build_prompt(
            characters_overview=characters_overview,
            visual_tone=visual_tone,
            title=title,
            logline=outline.get("logline", ""),
            style_preset=style_preset,
        )
        logger.info(f"  prompt 长度: {len(prompt)} chars")

        content = None
        provider = None

        # 优先使用 Claude Sonnet 4.6
        if self.claude_client:
            try:
                llm_start = time.time()
                logger.info(f"  [尝试 Claude Sonnet 4.6]")
                response = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=16384,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
                provider = "claude"
                llm_elapsed = time.time() - llm_start
                logger.info(f"  [Claude] ✅ 响应: {len(content)} chars, 耗时 {llm_elapsed:.1f}s")
            except Exception as e:
                logger.warning(f"  [Claude失败: {e}，尝试Gemini备用]")
                print(f"  [Claude失败: {e}，尝试Gemini备用]")

        # Fallback到Gemini 3 Flash
        if content is None and self.gemini_client:
            try:
                llm_start = time.time()
                logger.info(f"  [尝试 Gemini 3.1 Flash Lite]")
                response = await self.gemini_client.aio.models.generate_content(
                    model=self.gemini_model,
                    contents=prompt,
                    config={"max_output_tokens": 16384}
                )
                content = response.text
                provider = "gemini"
                llm_elapsed = time.time() - llm_start
                logger.info(f"  [Gemini] ✅ 响应: {len(content)} chars, 耗时 {llm_elapsed:.1f}s")
            except Exception as e:
                logger.error(f"[CharacterDesigner] ❌ Gemini也失败: {e}")
                print(f"[CharacterDesigner] ❌ Gemini也失败: {e}")
                raise

        if content is None:
            logger.error("[CharacterDesigner] ❌ 无可用的LLM服务")
            raise ValueError("无可用的LLM服务")

        characters = self._extract_json(content)

        if characters:
            self._validate_characters(characters)
            stage_elapsed = time.time() - stage_start
            char_names = [c.get('name', 'N/A') for c in characters.get("characters", [])]
            print(f"[CharacterDesigner] ✅ 角色设计完成 (via {provider})")
            logger.info(f"[CharacterDesigner] ✅ 角色设计完成 (via {provider}, 总耗时 {stage_elapsed:.1f}s)")
            logger.info(f"  角色: {', '.join(char_names)}")
            for char in characters.get("characters", []):
                print(f"  - {char.get('name', 'N/A')} ({char.get('role', 'N/A')})")
            return characters
        else:
            logger.error(f"[CharacterDesigner] ❌ JSON提取失败, 响应长度: {len(content)} chars, 前200字: {content[:200]}")
            raise ValueError("无法从LLM响应中提取JSON")

    # T20-46: STYLE_INFUSION_RULES — 按 style_preset 强制 LLM 在角色描述中注入风格一致的形容词
    # 目的：防止 CharacterDesigner LLM 对不同角色输出具体性差异过大的描述，导致 Seedream
    # 按描述具体性自由发挥渲染风格（如 gothic 故事中林深 anime / 陈婶 realistic 混杂）。
    # 机制：每个 style_preset 对应一组 style modifier 词典，LLM 在写 physical + clothing 描述时
    # 必须以 "drawn in {style_name} style" 开头，且每个视觉字段加入 ≥1 个 style modifier。
    STYLE_MODIFIER_DICT: dict[str, dict] = {
        "gothic": {
            "style_name": "gothic dark romantic",
            "physical_modifiers": ["pale", "gaunt", "ash-gray", "hollow", "shadow-ringed",
                                   "translucent", "bloodless", "etched-with-sorrow"],
            "clothing_modifiers": ["blood-red", "lace-trimmed", "ornate dark", "tattered velvet",
                                   "iron-buckled", "moth-eaten", "mournful black", "gothic-cut"],
            "tone_hint": "Every character, regardless of age or role, must appear to belong "
                         "to the same gothic dark romantic visual world — pale skin, shadowed "
                         "features, dark clothing with gothic-era details.",
        },
        "anime": {
            "style_name": "Japanese anime",
            "physical_modifiers": ["bright", "expressive", "large-eyed", "sleek", "vibrant",
                                   "clean-lined", "luminous", "sharp-featured"],
            "clothing_modifiers": ["vivid-colored", "anime-styled", "crisp", "fashionable",
                                   "school-uniform-adjacent", "high-contrast"],
            "tone_hint": "Every character must have the clean expressive look of a Japanese "
                         "anime character — large emotive eyes, clean lines, vibrant colors.",
        },
        "realistic": {
            "style_name": "photorealistic",
            "physical_modifiers": ["natural", "proportional", "weathered", "authentic",
                                   "realistically-textured", "age-appropriate", "lifelike"],
            "clothing_modifiers": ["worn", "fabric-textured", "realistically-draped",
                                   "practically-styled", "everyday-authentic"],
            "tone_hint": "Every character must look like a real person photographed in natural "
                         "light — no stylization, proportional features, authentic clothing.",
        },
        "cartoon": {
            "style_name": "3D cartoon",
            "physical_modifiers": ["stylized", "soft-shaded", "friendly", "exaggerated",
                                   "smooth-featured", "rounded", "Pixar-like"],
            "clothing_modifiers": ["colorful", "clean-blocked", "toy-like", "simplified",
                                   "bright-palette", "smooth-fabric"],
            "tone_hint": "Every character must have the rounded friendly look of Pixar/Disney "
                         "3D animation — smooth shading, exaggerated but friendly features.",
        },
        "watercolor": {
            "style_name": "watercolor illustration",
            "physical_modifiers": ["soft-edged", "dreamy", "flowing", "gentle", "ethereal",
                                   "wash-toned", "translucent-skinned"],
            "clothing_modifiers": ["watercolor-washed", "soft-blended", "dreamily-hued",
                                   "flowing", "gentle-palette", "diffuse-edged"],
            "tone_hint": "Every character must have the soft dreamy look of watercolor "
                         "illustration — blurred edges, gentle color washes, ethereal quality.",
        },
        "ghibli": {
            "style_name": "Studio Ghibli",
            "physical_modifiers": ["hand-drawn", "Miyazaki-styled", "warm-toned", "gentle",
                                   "whimsical", "expressive-eyed", "detailed"],
            "clothing_modifiers": ["Studio-Ghibli-designed", "hand-crafted-looking",
                                   "charming-detailed", "folk-inspired", "warm-palette"],
            "tone_hint": "Every character must have the hand-drawn warmth of Studio Ghibli "
                         "animation — detailed, whimsical, with warm gentle tones.",
        },
        "ink": {
            "style_name": "Chinese ink wash",
            "physical_modifiers": ["brush-stroked", "elegant", "minimal", "ink-wash-toned",
                                   "traditional", "austere", "sumi-e-styled"],
            "clothing_modifiers": ["ink-wash-rendered", "traditional-Chinese", "minimal-detail",
                                   "brush-and-ink-suggested", "muted-toned"],
            "tone_hint": "Every character must have the minimal elegant look of Chinese sumi-e "
                         "ink wash painting — simple brush strokes, muted tones, traditional feel.",
        },
        "cyberpunk": {
            "style_name": "cyberpunk neon",
            "physical_modifiers": ["neon-lit", "tech-augmented", "gritty", "futuristic",
                                   "dystopian-styled", "chrome-accented", "synthwave-aesthetic"],
            "clothing_modifiers": ["neon-accented", "tech-embedded", "futuristic", "gritty-worn",
                                   "cyberpunk-designed", "LED-lit", "dystopian"],
            "tone_hint": "Every character must look like they belong in a neon-lit cyberpunk "
                         "dystopia — tech augmentations, neon colors, gritty futuristic clothing.",
        },
    }

    def _get_style_infusion_block(
        self, style_preset: str | None, visual_tone: dict
    ) -> str:
        """
        T20-46: 根据 style_preset（或 visual_tone 推断）生成 STYLE_INFUSION_RULES prompt 块。

        这是 CharacterDesigner prompt 的关键新增部分，强制 LLM 在写每个角色的
        physical + clothing 描述时注入 style-aligned 形容词，防止不同角色风格漂移。

        Args:
            style_preset: 用户选择的风格 ID（如 "gothic"）；None 时从 visual_tone 推断
            visual_tone: Stage 1 的视觉风调 dict

        Returns:
            格式化的 STYLE_INFUSION_RULES prompt 块（英文，可直接嵌入 prompt）
        """
        # 尝试从 style_preset 直接匹配
        style_key = None
        if style_preset:
            preset_lower = style_preset.lower()
            for key in self.STYLE_MODIFIER_DICT:
                if key in preset_lower or preset_lower in key:
                    style_key = key
                    break

        # fallback: 从 visual_tone 推断
        if style_key is None and visual_tone:
            palette_str = " ".join(visual_tone.get("color_palette", [])).lower()
            lighting = visual_tone.get("lighting_style", "").lower()
            mood = visual_tone.get("overall_mood", "").lower()
            composition = visual_tone.get("composition_style", "").lower()

            # 推断规则（按优先级）
            if any(w in palette_str for w in ["shadow", "dark", "pale", "sickly"]) or \
               "chiaroscuro" in lighting or "gothic" in str(style_preset or "").lower():
                style_key = "gothic"
            elif any(w in palette_str for w in ["neon", "cyan", "purple", "electric"]) or \
                 "cyberpunk" in str(style_preset or "").lower():
                style_key = "cyberpunk"
            elif "ink" in str(style_preset or "").lower():
                style_key = "ink"
            elif "ghibli" in str(style_preset or "").lower():
                style_key = "ghibli"
            elif "watercolor" in str(style_preset or "").lower():
                style_key = "watercolor"
            elif "anime" in str(style_preset or "").lower() or "manga" in str(style_preset or "").lower():
                style_key = "anime"
            elif "cartoon" in str(style_preset or "").lower() or "pixar" in str(style_preset or "").lower():
                style_key = "cartoon"

        # 如果没有命中已知风格，返回通用规则（仍然有约束力）
        if style_key is None or style_key not in self.STYLE_MODIFIER_DICT:
            return """
════════════════════════════════════════════════════════════
STYLE INFUSION RULES — CHARACTER DESCRIPTION CONSISTENCY
════════════════════════════════════════════════════════════

CRITICAL REQUIREMENT: All characters in this story MUST belong to the SAME visual style world.
Style consistency across all characters is MANDATORY — not optional.

When writing physical and clothing descriptions for each character:
1. Start each character's description with: "[Character role/age] rendered in [consistent visual style], ..."
2. Use the SAME visual aesthetic vocabulary across ALL characters
3. Every physical field (hair, eyes, skin) and clothing field MUST include style-aligned adjectives
4. NO character should look like they belong to a different art style than the others

SELF-CHECK before outputting: Do all characters look like they come from the same visual world?
If any character's description would produce a different art style when rendered by AI image generation,
revise it to match the established style.
════════════════════════════════════════════════════════════
"""

        config = self.STYLE_MODIFIER_DICT[style_key]
        style_name = config["style_name"]
        physical_mods = ", ".join(config["physical_modifiers"][:5])
        clothing_mods = ", ".join(config["clothing_modifiers"][:5])
        tone_hint = config["tone_hint"]

        return f"""
════════════════════════════════════════════════════════════
STYLE INFUSION RULES (T20-46) — MANDATORY — DO NOT SKIP
════════════════════════════════════════════════════════════

TARGET VISUAL STYLE: {style_name}

CRITICAL REQUIREMENT: Every single character MUST be described as belonging to the
"{style_name}" visual world. This is the most important rule in this prompt.

STYLE-ALIGNED DESCRIPTION PROTOCOL:

1. START each character's physical description with:
   "[age/role] drawn in {style_name} style, ..."

2. PHYSICAL FIELD STYLE MODIFIERS (use at least 3 per character):
   Preferred words: {physical_mods}

3. CLOTHING FIELD STYLE MODIFIERS (use at least 2 per character):
   Preferred words: {clothing_mods}

DESIGN RULE:
{tone_hint}

WRONG PATTERN (DO NOT DO THIS):
   Character A: "60-year-old woman, gray hair, dark red robe"
   → This produces REALISTIC/PHOTOGRAPHIC style, NOT {style_name}

CORRECT PATTERN (DO THIS):
   Character A: "60-year-old woman drawn in {style_name} style, [add {style_key} modifiers
   to EVERY field — hair, skin, eyes, clothing, accessories]"

SELF-CHECK (mandatory before outputting):
   □ Does EVERY character description start with a style reference?
   □ Does EVERY physical field contain at least 1 style modifier word?
   □ Does EVERY clothing field contain at least 1 style modifier word?
   □ Would ALL characters look like they belong to the same visual world if rendered separately?

If any answer is NO — revise that character's description before outputting.
════════════════════════════════════════════════════════════
"""

    def _build_prompt(
        self,
        characters_overview: list,
        visual_tone: dict,
        title: str,
        logline: str,
        style_preset: str | None = None,
    ) -> str:
        """构建角色设计prompt"""

        characters_json = json.dumps(characters_overview, ensure_ascii=False, indent=2)
        style_infusion_block = self._get_style_infusion_block(style_preset, visual_tone)

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
            "character_type": "human / anthropomorphic_animal / animal / fantasy_creature / robot / insect / aquatic / plant / mythological / supernatural / undead / elemental / alien / vehicle_character / digital_virtual / concept_personified / miniature / giant / hybrid / object",
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
            }},

            "description": "角色综合外貌描述（2-3句中英双语，先中文再英文）。必须包含 hair_color/hair_style/eye_color/skin_tone 及服装要点。示例: '二十四岁便利店收银员，扎马尾辫，黑色长发带棕色高光，穿蓝白条纹工作服。A 24-year-old convenience store cashier with high ponytail black hair (brown sheen), wearing blue-white striped polo uniform.'"
        }}
    ]
}}
```

## 角色类型说明（MANDATORY — 必须正确设置 character_type）

- `human`：真实人类角色 → 使用 hair_color / skin_tone / eye_shape 等人类字段
- `anthropomorphic_animal`：拟人化动物（如《动物森友会》《疯狂动物城》风格）→ 有意识、穿服装、直立行走，但保留物种动物外貌（毛皮、耳朵、尾巴、口鼻/喙） → **必须**使用 species / fur_color / ear_style / tail_style 等动物字段；**严禁**用 hair_color / skin_tone 作为身体特征（动物有毛皮，不是头发和皮肤）
- `animal`：真实动物，无服装，四足行走，无意识表达
- 其他类型照常

**anthropomorphic_animal 的 physical 字段必须包含（MANDATORY）**：
```
"physical": {{
    "species": "rabbit / fox / wolf / sparrow / squirrel / bear / ...",
    "fur_color": "毛色描述（如 frost silver grey, warm chestnut brown）",
    "fur_texture": "毛质（如 silky, fluffy, coarse）",
    "fur_pattern": "花纹（可选，如 tawny patches, darker stripe along back）",
    "ear_style": "耳朵（如 very_short, long_upright, pointed）",
    "tail_style": "尾巴（如 bushy, long, small_fluffy）",
    "snout_shape": "口鼻/喙（如 small pointed fox snout, short beak-like）",
    "eye_color": "眼色",
    "eye_shape": "眼形（可选）",
    "height": "身高",
    "build": "体型",
    "distinctive_marks": ["特征1（建议含英文）", "特征2"]
}}
```
**严禁将 hair_color / skin_tone / face_shape / body_type 作为 anthropomorphic_animal 的主要外貌字段 — 这会导致 AI 把动物角色画成人类！**

## NON-CLOTHING CHARACTER TYPES — CLOTHING FIELD RULES (#5e — MANDATORY)

When `character_type` is one of: `object` / `aquatic` / `plant` / `insect` / `animal` / `elemental` / `vehicle_character`,
the character has NO human clothing (a clock / fish / sunflower / ant / flame / car does not wear a top/pants/shoes).

You MUST STILL output a complete `clothing` object with ALL required keys (top, bottom, footwear, style) —
NEVER omit the clothing field or its sub-keys (an incomplete clothing field can break the pipeline).
For these types, fill each clothing key with `"n/a"` OR a short SURFACE-APPEARANCE description instead of a garment:

```
// object (会说话的落地钟):
"clothing": {{
    "top": "n/a (object — described via surface_appearance)",
    "bottom": "n/a",
    "footwear": "n/a",
    "outerwear": null,
    "accessories": ["brass pendulum", "carved oak case"],
    "style": "antique mahogany grandfather clock with patina",
    "condition": "aged with hairline cracks"
}}

// aquatic (clownfish):
"clothing": {{
    "top": "n/a (fish — described via scale pattern)",
    "bottom": "n/a",
    "footwear": "n/a",
    "accessories": [],
    "style": "vivid orange body with three white bands and black edging"
}}
```

RULE: surface/material/pattern goes into `style` (and optionally `accessories`); the literal garment
keys (top/bottom/footwear) get `"n/a"`. This guarantees a schema-valid clothing dict for every type.

{style_infusion_block}

## SUPERNATURAL HUMANOID FIELDS RULES (T20-43 — MANDATORY HARD CONSTRAINTS)

When `character_type` is one of: `supernatural` / `undead` / `mythological` / `fantasy_creature`,
the character JSON MUST follow these rules:

### Rule SHF-1: 优先填种族身份字段 (type-specific identity fields)

Always fill the primary identity field for the given type:

| character_type    | 必填种族字段            | 示例值                                              |
|-------------------|------------------------|-----------------------------------------------------|
| supernatural      | being_type (in physical) | 鬼魂 / 幽灵 / 镜中人 / 山神 / 影子人 / 怨念体      |
| undead            | undead_type + original_form (in physical) | 僵尸 / 复活者 / 怨灵 / 游魂；原本是 人类男性/女性 |
| mythological      | creature_type + origin_culture (in physical) | 狐仙 / 雪女 / 哪吒 / 牛魔王；中国 / 日本 / 北欧 |
| fantasy_creature  | creature_type + base_form (in physical) | 精灵 / 兽人 / 龙族 / 树人；humanoid / beast / spirit |

These fields tell the image model WHAT the entity IS — they are the semantic anchor
for the AI rendering engine. Without them, the model treats the character as a human.

### Rule SHF-2: 人形配置时额外补完整人类外貌字段

If the supernatural/undead/mythological/fantasy_creature character LOOKS LIKE A HUMAN
(e.g. 镜中人 / 鬼魂 that appears as a person / 山神 in human form / 仙人 / 妖 in disguise),
you MUST ALSO fill the full human appearance fields in physical:

```
"physical": {{
    "being_type": "镜中人",                          ← Rule SHF-1 (type identity)
    "hair_color": "ashen gray with faint silver sheen",  ← Rule SHF-2 (human appearance)
    "hair_style": "shoulder-length, unnaturally still",
    "skin_tone": "pale porcelain, slightly translucent",
    "face_shape": "oval",
    "eye_color": "pale silver, iris-less",
    "eye_shape": "almond",
    "height": "average",
    "build": "slim",
    "distinctive_marks": ["reflection always 0.3s delayed", "no breath fog in cold air"]
}}
```

The being_type/undead_type/creature_type tells WHAT it is; the hair/skin/eye fields
tell HOW it looks visually — both are needed for consistent AI-generated imagery.

### Rule SHF-3: 不接受 minimal 输出

The following output is REJECTED — it gives human appearance without type identity:

❌ BAD (missing being_type — schema兜底但语义不准):
```
"character_type": "supernatural",
"physical": {{
    "hair_color": "black",
    "skin_tone": "pale",
    "face_shape": "oval"
    // ← missing being_type, base_form, or any type-identity field
}}
```

✅ GOOD (type identity + human appearance — 完整):
```
"character_type": "supernatural",
"physical": {{
    "being_type": "镜中人",
    "hair_color": "ashen black",
    "skin_tone": "pale translucent",
    "face_shape": "oval",
    "eye_color": "silver-white"
}}
```

### Rule SHF-4: 同一故事内人形超自然角色的外貌必须与人类角色视觉区分

Even if the supernatural character looks human, add at least 1–2 distinctive_marks
that visually signal their non-human nature (e.g. "reflection always delayed",
"casts no shadow", "eyes emit faint glow", "skin slightly translucent").
This ensures Seedream renders them as visually different from the human cast.

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

5. **团队/组织着装一致性**：属于同一团队/组织的角色，制服/统一着装必须在颜色和款式上保持一致
   - 同一球队的球员：球衣颜色、款式相同，仅通过号码和体型区分
   - 同一学校学生：校服相同
   - 同一军队士兵：军装相同
   - 同一公司员工：工装/制服相同
   - 通过球衣号码、臂章、发型、体型、面部特征来区分角色——不要用不同颜色的制服

6. **服装状态**：clothing.condition应反映角色当前的状态
   - 如雨夜故事中角色应该是"rain-soaked"
   - 如加班后角色应该是"disheveled, tired appearance"

7. **ID规范**：角色id从char_001开始递增

现在开始设计角色：
"""

    def _extract_json(self, content: str) -> Optional[dict]:
        """从LLM响应中提取JSON

        B59-hotfix (2026-05-12): 委托给共用 helper，支持未闭合 ``` 容错
        """
        from app.services._llm_helpers import extract_json_from_llm_response
        return extract_json_from_llm_response(content)

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

            # 验证physical — 按 character_type 分类校验
            # T20-23 修复: 只对 human 做严格人类字段检查;
            # 非 human 类型 (animal/robot/fantasy_creature 等 19 种) 由
            # pipeline_orchestrator.py validate_characters() 经 CharacterSchema 完整校验,
            # 此处不重复做，避免两处校验漂移造成误 raise.
            physical = char.get("physical", {})
            char_type_val = char.get("character_type", "human")
            if char_type_val == "human":
                # 人类角色：必须有 hair_color/hair_style/eye_color/skin_tone/face_shape
                physical_required = ["hair_color", "hair_style", "eye_color", "skin_tone", "face_shape"]
                physical_missing = [f for f in physical_required if f not in physical]
                if physical_missing:
                    raise ValueError(f"角色 {char_id} physical缺少字段: {physical_missing}")
            elif char_type_val == "anthropomorphic_animal":
                # 拟人化动物：必须有 species 和 fur_color（动物物种+毛色）
                physical_required = ["species", "fur_color"]
                physical_missing = [f for f in physical_required if not physical.get(f)]
                if physical_missing:
                    # 降级为警告（LLM 可能填在错误字段，_build_anthropomorphic_animal_description 有防御）
                    logger.warning(
                        f"[CharacterDesigner] anthropomorphic_animal '{char_id}' physical 缺少动物字段: {physical_missing}"
                        f" — 请确认 LLM 输出了 species/fur_color 等字段"
                    )
            # else: animal/robot/fantasy_creature 等其他类型 → 跳过此处校验,
            # 由 pipeline_orchestrator.py validate_characters() 负责 (T20-10 已覆盖 19 types)

            # 验证clothing
            # Wave 13 #5e A (2026-05-25): 非穿衣 type 缺 clothing 子字段降 warning 不 raise。
            # 根因: 此处对【所有 type 一刀切】要求 top/bottom/footwear/style, 但真物件(钟)/
            # 鱼/植物/昆虫等天然没衣服, LLM 给残缺 clothing → raise。而本校验在 design()
            # L127 调, 在 LLM fallback try/except (L82-118) 【之外】, orchestrator 调 design()
            # 又【无 retry】→ 一次 raise 直接冲垮整条 pipeline (内测用户选这些 type 角色必崩)。
            # 修法: 与上方 anthropomorphic_animal physical 缺字段降级 (L603-612) 同 pattern —
            # 穿衣 type (human/超自然人形等) 仍严格 raise; 非穿衣 type 降 warning, pipeline 继续。
            clothing = char.get("clothing", {})
            clothing_required = ["top", "bottom", "footwear", "style"]
            clothing_missing = [f for f in clothing_required if f not in clothing]
            if clothing_missing:
                if char_type_val in self.NON_CLOTHING_TYPES:
                    # 非穿衣 type: 残缺 clothing 是天然合理 (物件/鱼/植物/昆虫等无人类衣物)
                    logger.warning(
                        f"[CharacterDesigner] #5e A: 非穿衣 type '{char_type_val}' 角色 {char_id} "
                        f"clothing 缺字段 {clothing_missing} — 降级为警告不 raise (天然无衣物), "
                        f"pipeline 继续。下游 _build_character_description 兜底处理。"
                    )
                else:
                    # 穿衣 type (human / 超自然人形 / 机器人 等): 仍严格要求, 缺字段是真问题
                    raise ValueError(f"角色 {char_id} clothing缺少字段: {clothing_missing}")

            # B56: description 字段缺失时自动 fallback 生成（确保 Stage 4 有字段可读）
            if not char.get("description", "").strip():
                _physical = char.get("physical", {})
                _clothing = char.get("clothing", {})
                _hair = f"{_physical.get('hair_color', '')} {_physical.get('hair_style', '')}".strip()
                _top = _clothing.get("top", "")
                _desc_parts = [p for p in [_hair, _physical.get("skin_tone", ""), _top] if p]
                char["description"] = ", ".join(_desc_parts) if _desc_parts else char.get("name_en", "")
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    f"[CharacterDesigner] B56: {char_id} description 为空，自动生成 fallback: {char['description'][:60]}"
                )

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
