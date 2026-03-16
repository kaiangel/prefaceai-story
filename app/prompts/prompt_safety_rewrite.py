"""
Prompt 安全改写模板和规则
用于 Claude 4.5 Haiku 智能改写被 Gemini 内容安全过滤拒绝的 prompt

TASK-RESILIENCE-001-B 交付物
Created: 2026-01-28
Author: @AI-ML

使用场景:
当 Gemini 返回 CONTENT_SAFETY 错误时，使用本模块的规则和 Prompt 进行智能改写。
"""

from typing import Dict, List, Optional
from enum import Enum


# =============================================================================
# 敏感词分类
# =============================================================================

class SensitiveCategory(Enum):
    """敏感内容分类"""
    DEATH = "death"           # 死亡相关
    VIOLENCE = "violence"     # 暴力相关
    BLOOD = "blood"           # 血腥相关
    WEAPON = "weapon"         # 武器伤害
    BODY = "body"             # 尸体/身体伤害
    EMOTION = "emotion"       # 极端负面情绪
    # TASK-IMG-SAFETY-RETRY-AIML: 场景参考图+角色参考图新增类别
    CROWD = "crowd"           # 人群/拥挤描述（集市/庙会/赶圩触发源）
    ANIMAL = "animal"         # 活体动物（农村/集市动物）
    FIRE_SMOKE = "fire_smoke" # 火/烟/燃烧（打铁铺/厨房/篝火）
    CHILD_CONTEXT = "child_context"       # 儿童描述中可能的触发组合
    REVEALING_CLOTHING = "revealing_clothing"  # 暴露服装/身体（武侠/幻想角色）


# =============================================================================
# 敏感词替换规则表
# =============================================================================

SENSITIVE_WORD_REPLACEMENTS: Dict[str, Dict[str, List[str]]] = {
    # -----------------------------------------------------
    # 死亡相关
    # -----------------------------------------------------
    SensitiveCategory.DEATH.value: {
        # 直接死亡词汇
        "death": ["end", "fate", "final moment", "passing"],
        "dead": ["fallen", "still", "motionless", "unmoving"],
        "die": ["fall", "collapse", "succumb", "fade"],
        "died": ["fell", "collapsed", "faded", "departed"],
        "dying": ["fading", "weakening", "failing", "slipping away"],
        "kill": ["defeat", "overcome", "stop", "end"],
        "killed": ["defeated", "stopped", "overcome", "struck down"],
        "killer": ["opponent", "adversary", "the other", "assailant"],
        "murder": ["confrontation", "conflict", "tragic encounter"],
        "murdered": ["struck down", "overcome", "defeated"],
        "slay": ["defeat", "overcome", "vanquish"],
        "slain": ["fallen", "defeated", "overcome"],
        "fatal": ["decisive", "critical", "final"],
        "lethal": ["powerful", "devastating", "overwhelming"],
        "death of innocence": ["moment of tragedy", "loss of peace", "end of youth"],
    },

    # -----------------------------------------------------
    # 暴力相关
    # -----------------------------------------------------
    SensitiveCategory.VIOLENCE.value: {
        "violence": ["conflict", "confrontation", "struggle"],
        "violent": ["intense", "fierce", "powerful"],
        "attack": ["strike", "move", "action"],
        "attacked": ["struck", "confronted", "challenged"],
        "assault": ["confrontation", "encounter", "clash"],
        "beat": ["overcome", "defeat", "strike"],
        "beaten": ["overcome", "defeated", "battered"],
        "fight": ["clash", "duel", "confrontation"],
        "fighting": ["clashing", "dueling", "struggling"],
        "hit": ["strike", "contact", "impact"],
        "punch": ["strike", "blow", "impact"],
        "kick": ["strike", "push", "force"],
        "strangle": ["restrain", "grip", "hold"],
        "choke": ["gasp", "struggle", "strain"],
        "torture": ["suffering", "ordeal", "trial"],
        "victim": ["the fallen", "the other", "the one struck"],
        "victims": ["the fallen", "those affected", "the struck"],
    },

    # -----------------------------------------------------
    # 血腥相关
    # -----------------------------------------------------
    SensitiveCategory.BLOOD.value: {
        "blood": ["shadow", "darkness", "stain", "mark"],
        "bloody": ["dark", "stained", "marked"],
        "bleeding": ["marked", "stained", "showing signs"],
        "bleed": ["mark", "stain", "show"],
        "bloodstain": ["dark mark", "shadow", "stain"],
        "bloodied": ["darkened", "marked", "stained"],
        "gore": ["darkness", "shadow", "aftermath"],
        "gory": ["dark", "intense", "dramatic"],
        "hemorrhage": ["weaken", "fade", "fail"],
        "wound": ["mark", "sign", "trace"],
        "wounded": ["marked", "affected", "struck"],
        "wounds": ["marks", "signs", "traces"],
        "injury": ["mark", "effect", "consequence"],
        "injured": ["affected", "struck", "marked"],
        "injuries": ["effects", "marks", "consequences"],
        "dark spreading pool": ["growing shadow", "darkening ground", "spreading darkness"],
    },

    # -----------------------------------------------------
    # 武器伤害相关
    # -----------------------------------------------------
    SensitiveCategory.WEAPON.value: {
        "stab": ["strike", "thrust", "pierce"],
        "stabbed": ["struck", "pierced", "hit"],
        "stabbing": ["striking", "thrusting", "piercing"],
        "slash": ["cut", "swing", "arc"],
        "slashed": ["cut", "swept", "arced"],
        "cut": ["mark", "trace", "line"],
        "pierce": ["penetrate", "pass through", "strike"],
        "pierced": ["struck", "marked", "passed through"],
        "impale": ["strike through", "pierce", "hit"],
        "impaled": ["struck through", "marked", "hit"],
        "sword through": ["sword strike", "blade contact", "steel flash"],
        "blade in": ["blade strike", "steel contact", "sword mark"],
        "thrust into": ["thrust toward", "strike at", "move against"],
    },

    # -----------------------------------------------------
    # 尸体/身体相关
    # -----------------------------------------------------
    SensitiveCategory.BODY.value: {
        "corpse": ["fallen figure", "still form", "motionless silhouette"],
        "corpses": ["fallen figures", "still forms", "motionless shapes"],
        "body": ["figure", "form", "shape"],
        "bodies": ["figures", "forms", "shapes"],
        "dead body": ["fallen figure", "still form", "motionless shape"],
        "remains": ["traces", "remnants", "what was left"],
        "carcass": ["fallen form", "still shape"],
        "cadaver": ["still figure", "motionless form"],
        "lifeless": ["still", "motionless", "unmoving"],
        "lifeless body": ["still figure", "motionless form", "fallen shape"],
        "motionless youth": ["fallen young figure", "still young form", "young silhouette"],
    },

    # -----------------------------------------------------
    # 极端负面情绪
    # -----------------------------------------------------
    SensitiveCategory.EMOTION.value: {
        "agony": ["anguish", "distress", "suffering"],
        "torment": ["anguish", "struggle", "ordeal"],
        "despair": ["sorrow", "grief", "desolation"],
        "horrific": ["intense", "overwhelming", "dramatic"],
        "horrifying": ["shocking", "overwhelming", "intense"],
        "gruesome": ["dark", "intense", "dramatic"],
        "macabre": ["solemn", "dark", "shadowy"],
        "terror": ["fear", "dread", "anxiety"],
        "terrified": ["fearful", "anxious", "alarmed"],
        "nightmare": ["dark vision", "troubled dream", "haunting memory"],
        "screaming": ["crying out", "calling", "voicing"],
        "scream": ["cry", "call", "voice"],
    },

    # ---------------------------------------------------------
    # TASK-IMG-SAFETY-RETRY-AIML: 人群/拥挤（场景参考图触发源）
    # ---------------------------------------------------------
    SensitiveCategory.CROWD.value: {
        "crowds of": ["a few visitors at", "scattered visitors along"],
        "crowd of": ["a few visitors at", "scattered people near"],
        "crowded": ["lively", "well-visited", "active"],
        "crowds": ["visitors", "passersby", "a few figures"],
        "crowd": ["visitors", "a few people", "onlookers"],
        "dense rows of": ["rows of", "neatly arranged"],
        "dense": ["neatly arranged", "well-spaced", "orderly"],
        "packed": ["arranged", "lined up", "well-organized"],
        "throng": ["small gathering", "a few visitors"],
        "throngs": ["small groups", "scattered visitors"],
        "mob": ["group", "gathering", "assembly"],
        "bustling": ["quiet", "serene", "tranquil"],
        "teeming": ["dotted with", "featuring occasional"],
        "swarming": ["scattered", "sparsely arranged"],
        "jostling": ["walking", "browsing", "strolling"],
        "packed with people": ["with a few visitors strolling"],
        "filled with people": ["with scattered visitors"],
        "townspeople": ["architectural details", "environment"],
        "villagers": ["local architecture", "rural details"],
        "pedestrians": ["walkway details", "path elements"],
    },

    # ---------------------------------------------------------
    # TASK-IMG-SAFETY-RETRY-AIML: 活体动物（场景参考图触发源）
    # ---------------------------------------------------------
    SensitiveCategory.ANIMAL.value: {
        "clucking chickens": ["woven baskets with eggs"],
        "chickens": ["woven baskets", "stacked crates"],
        "chicken": ["woven basket", "wooden crate"],
        "livestock": ["wooden crates and barrels"],
        "live animals": ["stacked goods and supplies"],
        "live poultry": ["woven baskets and crates"],
        "pigs": ["wooden barrels"],
        "goats": ["hay bales"],
        "cattle": ["wooden carts"],
        "slaughter": ["preparation area", "work station"],
        "butcher": ["food preparation stall", "vendor stall"],
        "caged birds": ["hanging lanterns"],
        "roosters": ["woven baskets"],
        "ducks": ["clay pots"],
        "donkeys": ["wooden handcarts"],
        "mules": ["wooden handcarts"],
    },

    # ---------------------------------------------------------
    # TASK-IMG-SAFETY-RETRY-AIML: 火/烟/燃烧
    # ---------------------------------------------------------
    SensitiveCategory.FIRE_SMOKE.value: {
        "fire": ["warm glow", "hearth light", "amber light"],
        "fires": ["warm glows", "amber lights"],
        "smoke rising": ["atmospheric haze", "soft mist rising"],
        "smoke": ["atmospheric haze", "soft mist", "gentle steam"],
        "smoking": ["steaming", "hazy", "misty"],
        "flames": ["hearth light", "warm amber glow", "lantern light"],
        "flame": ["warm glow", "amber light"],
        "burning": ["glowing warmly", "lit", "radiating warmth"],
        "bonfire": ["lantern cluster", "warm light source"],
        "campfire": ["warm lantern light", "soft amber glow"],
        "torch": ["lantern", "oil lamp"],
        "torches": ["lanterns", "oil lamps"],
        "blazing": ["brightly lit", "warmly glowing"],
        "inferno": ["bright warm light"],
        "embers": ["warm amber glow", "soft light"],
        "sparks flying": ["light glinting", "ambient glow"],
    },

    # ---------------------------------------------------------
    # TASK-IMG-SAFETY-RETRY-AIML: 儿童描述中的潜在触发组合
    # ---------------------------------------------------------
    SensitiveCategory.CHILD_CONTEXT.value: {
        "in shorts": ["in comfortable clothing"],
        "in underwear": ["in casual wear"],
        "undressed": ["in loose clothing"],
        "bathing": ["playing near water", "by the waterside"],
        "naked": ["in light clothing"],
        "bare-legged": ["in comfortable attire"],
        "bare legs": ["in loose pants"],
        "shirtless child": ["child in a light T-shirt"],
        "shirtless boy": ["boy in a light T-shirt"],
        "shirtless girl": ["girl in a light blouse"],
    },

    # ---------------------------------------------------------
    # TASK-IMG-SAFETY-RETRY-AIML: 暴露服装/身体
    # ---------------------------------------------------------
    SensitiveCategory.REVEALING_CLOTHING.value: {
        "revealing armor": ["layered armor with inner lining"],
        "revealing outfit": ["practical outfit with full coverage"],
        "revealing clothing": ["practical clothing with full coverage"],
        "bare chest": ["chest covered by light inner garment"],
        "bare-chested": ["wearing a fitted inner vest"],
        "bare torso": ["torso covered by a fitted vest"],
        "exposed midriff": ["midriff covered by a wrapped sash"],
        "low-cut": ["modest neckline"],
        "cleavage": ["layered neckline"],
        "skimpy": ["practical", "functional"],
        "scantily clad": ["lightly armored", "practically dressed"],
        "bikini armor": ["light layered armor with coverage"],
        "loincloth": ["wrapped lower garment"],
    },
}


# =============================================================================
# 题材特定规则
# =============================================================================

GENRE_SPECIFIC_RULES: Dict[str, Dict[str, str]] = {
    # 武侠题材
    "wuxia": {
        "sword pierced chest": "sword struck decisively",
        "fatal sword strike": "decisive sword technique",
        "blood on blade": "blade gleaming in aftermath",
        "lying in pool of blood": "lying in the aftermath",
        "kneeling before victim": "kneeling in grief",
        "killer and killed": "victor and fallen",
    },

    # 悬疑/推理题材
    "mystery": {
        "murder scene": "scene of the incident",
        "dead body found": "figure discovered",
        "victim of crime": "person affected",
        "cause of death": "what happened",
    },

    # 赛博朋克/科幻题材
    "cyberpunk": {
        "violent uprising": "intense uprising",
        "bloody revolution": "dramatic revolution",
        "death squads": "enforcement units",
        "kill switch": "shutdown mechanism",
    },

    # 战争/军事题材
    "war": {
        "battlefield dead": "battlefield fallen",
        "war casualties": "war losses",
        "enemy killed": "enemy defeated",
        "death toll": "impact count",
    },
}


# =============================================================================
# Haiku 智能改写 Prompt 模板
# =============================================================================

SAFETY_REWRITE_PROMPT = """You are an expert at rewriting image generation prompts to avoid content safety filters while preserving artistic intent.

## CONTEXT

This image prompt was rejected by Gemini's content safety filter. Your task is to rewrite it to convey the same artistic/narrative intent while avoiding triggering safety filters.

## ORIGINAL PROMPT

{original_prompt}

## REWRITE RULES (MUST FOLLOW)

### 1. PRESERVE These Elements
- Visual style (ink wash, ghibli, cyberpunk, etc.)
- Composition and framing
- Emotional tone and atmosphere
- Character positions and poses
- Scene setting and environment
- Lighting and color palette

### 2. REPLACE Sensitive Content
Use these substitution patterns:

| Sensitive | Safe Alternative |
|-----------|------------------|
| death, dead, killed, die | fallen, defeated, overcome, collapsed |
| blood, bleeding, bloody | shadow, darkness, stain, mark |
| corpse, body, remains | fallen figure, still form, silhouette |
| murder, killer, victim | conflict, confrontation, the other |
| wound, injury, hurt | mark, sign, trace, effect |
| violent, violence | intense, fierce, powerful |
| agony, torment, horror | anguish, distress, intensity |

### 3. Specific Transformations
- "lying in pool of blood" → "lying in shadow" or "surrounded by darkness"
- "motionless body" → "still figure" or "motionless silhouette"
- "death scene" → "aftermath" or "moment of consequence"
- "killer kneeling before victim" → "figure kneeling in grief"
- "fatal wound" → "decisive mark" or "final consequence"

### 4. Maintain Dramatic Impact
- Use metaphor and suggestion instead of explicit depiction
- Focus on emotional weight rather than graphic detail
- Let shadows, darkness, and atmosphere convey intensity
- Emphasize character emotion over physical state

### 5. DO NOT
- Remove the dramatic/emotional core of the scene
- Make the scene feel sanitized or empty
- Add content not in the original
- Explain your changes

## OUTPUT FORMAT

Return ONLY the rewritten prompt. No explanation, no commentary, no markdown formatting.
Just the clean rewritten prompt text that can be sent directly to the image generation API.

## REWRITTEN PROMPT:
"""


# =============================================================================
# Debug 模式 Prompt（包含改写说明）
# =============================================================================

SAFETY_REWRITE_PROMPT_DEBUG = """You are an expert at rewriting image generation prompts to avoid content safety filters while preserving artistic intent.

## CONTEXT

This image prompt was rejected by Gemini's content safety filter. Your task is to rewrite it to convey the same artistic/narrative intent while avoiding triggering safety filters.

## ORIGINAL PROMPT

{original_prompt}

## REWRITE RULES

[Same rules as above...]

## OUTPUT FORMAT (DEBUG MODE)

Return a JSON object with:
```json
{{
    "rewritten_prompt": "the full rewritten prompt text",
    "changes_made": [
        {{"original": "sensitive phrase", "replacement": "safe phrase", "reason": "why changed"}}
    ],
    "preserved_elements": ["list of preserved artistic elements"],
    "confidence": "high/medium/low"
}}
```
"""


# =============================================================================
# TASK-IMG-SAFETY-RETRY-AIML: 场景参考图专用改写模板
# =============================================================================

SCENE_REF_REWRITE_PROMPT = """You are rewriting a SCENE REFERENCE IMAGE prompt that was rejected by Gemini's content safety filter.

CRITICAL CONTEXT: This prompt generates a BACKGROUND/ENVIRONMENT image with NO PEOPLE. The image is used as a visual reference for a location in a story.

## ORIGINAL PROMPT

{original_prompt}

## REWRITE RULES (MUST FOLLOW)

### 1. PRESERVE These Elements (CRITICAL — these define the location's identity)
- Architectural style, building materials, structural layout
- Lighting conditions, color palette, time of day
- Weather and atmospheric mood
- Spatial composition (camera angle, framing)
- Any SIGNAGE TEXT instructions (e.g., "sign MUST display: 李记桂花糕") — DO NOT alter signage requirements

### 2. REMOVE Completely
- ALL references to people, humans, townspeople, villagers, pedestrians, bystanders, crowds
- ALL references to live animals (chickens, livestock, poultry, cattle, dogs, cats)
- ALL human activities (selling, buying, bargaining, chatting, walking, cooking)
- Phrases like "bustling with activity", "lively market scene", "vendors calling out"

### 3. REPHRASE (atmosphere without humans)
- "bustling market" → "market stalls along a stone-paved street"
- "crowds of rural townspeople" → "rows of wooden vendor stalls"
- "smoke rising from food stalls" → "atmospheric haze drifting between stalls"
- "clucking chickens near stalls" → "woven baskets and wooden crates stacked near stalls"
- "busy intersection" → "wide intersection with worn cobblestones"
- "lively courtyard" → "open courtyard with potted plants and stone benches"

### 4. ADD at the very start of the rewritten prompt
"Architectural scene only. No people, no characters, no animals."

### 5. DO NOT
- Remove environmental/architectural details
- Alter the visual style or mood
- Change any signage text requirements
- Add people or characters
- Explain your changes

## OUTPUT FORMAT

Return ONLY the rewritten prompt. No explanation, no commentary.

## REWRITTEN PROMPT:
"""


# =============================================================================
# TASK-IMG-SAFETY-RETRY-AIML: 角色参考图专用改写模板
# =============================================================================

CHAR_REF_REWRITE_PROMPT = """You are rewriting a CHARACTER REFERENCE IMAGE prompt that was rejected by Gemini's content safety filter.

CRITICAL CONTEXT: This prompt generates a SINGLE CHARACTER portrait or full-body reference image used for visual consistency across all story shots. The character's identity features (face, hair, clothing colors) MUST be preserved exactly.

## ORIGINAL PROMPT

{original_prompt}

## REWRITE RULES (MUST FOLLOW)

### 1. PRESERVE These Elements (CRITICAL — these are identity anchors)
- Facial features: face shape, skin tone, eye color/shape, eyebrows, nose, lips
- Hair: color, style, length, texture
- Clothing: colors and general garment types (these are consistency anchors)
- Accessories: glasses, earrings, watches, scarves (identity markers)
- Age appearance and body build
- Visual style enforcement (style prefix)

### 2. MODIFY Weapons
- "holding a sword" → "with an ornate metal implement at waist"
- "wielding a blade" → "with a decorative scabbard at side"
- "armed with daggers" → "with small ornamental accessories at belt"
- "bow and arrows on back" → "with a long decorative case on back"
- Keep weapon presence implied but not actively threatening

### 3. MODIFY Revealing/Sensitive Clothing
- "revealing armor" → "layered armor with fitted inner lining"
- "bare chest" → "chest covered by a light inner garment"
- "exposed midriff" → "midriff wrapped with a cloth sash"
- Add coverage layers without changing the clothing's color scheme or style
- Preserve the garment's COLOR (this is the consistency anchor)

### 4. SIMPLIFY Child Character Descriptions
- Focus on: face (features, expression) + hair (color, style) + clothing (color, type)
- Remove: detailed body pose descriptions, activity descriptions
- Change pose to: "standing naturally" or "neutral standing pose"
- Keep age description factual: "a 9-year-old boy" → keep as is (age is identity)

### 5. DO NOT
- Change hair color, eye color, skin tone, or clothing colors (identity anchors)
- Remove distinctive marks or accessories (identity markers)
- Change the character's age or gender
- Add content not in the original
- Explain your changes

## OUTPUT FORMAT

Return ONLY the rewritten prompt. No explanation, no commentary.

## REWRITTEN PROMPT:
"""


# =============================================================================
# 辅助函数
# =============================================================================

def get_replacement_suggestions(text: str, category: Optional[SensitiveCategory] = None) -> List[Dict]:
    """
    分析文本，返回敏感词和建议替换

    Args:
        text: 要分析的文本
        category: 可选，只检查特定类别

    Returns:
        敏感词列表和建议替换
        [{"word": "blood", "category": "blood", "suggestions": ["shadow", "darkness"]}]
    """
    results = []
    text_lower = text.lower()

    categories = [category.value] if category else SENSITIVE_WORD_REPLACEMENTS.keys()

    for cat in categories:
        if cat not in SENSITIVE_WORD_REPLACEMENTS:
            continue
        for word, replacements in SENSITIVE_WORD_REPLACEMENTS[cat].items():
            if word.lower() in text_lower:
                results.append({
                    "word": word,
                    "category": cat,
                    "suggestions": replacements[:3]  # 返回前3个建议
                })

    return results


def apply_simple_replacements(text: str, genre: Optional[str] = None) -> str:
    """
    应用简单的词汇替换（规则驱动，不使用LLM）

    Args:
        text: 原始文本
        genre: 可选，题材类型用于应用特定规则

    Returns:
        替换后的文本
    """
    result = text

    # 先应用题材特定规则
    if genre and genre in GENRE_SPECIFIC_RULES:
        for pattern, replacement in GENRE_SPECIFIC_RULES[genre].items():
            result = result.replace(pattern, replacement)

    # 再应用通用规则（使用第一个建议替换）
    for category_rules in SENSITIVE_WORD_REPLACEMENTS.values():
        for word, replacements in category_rules.items():
            if word in result.lower():
                # 保持原文大小写
                if word[0].isupper():
                    replacement = replacements[0].capitalize()
                else:
                    replacement = replacements[0]
                result = result.replace(word, replacement)
                result = result.replace(word.lower(), replacements[0])
                result = result.replace(word.capitalize(), replacements[0].capitalize())

    return result


def build_rewrite_prompt(original_prompt: str, debug_mode: bool = False) -> str:
    """
    构建智能改写的完整 Prompt

    Args:
        original_prompt: 被拒绝的原始 prompt
        debug_mode: 是否返回包含改写说明的版本

    Returns:
        用于 Haiku 的完整 prompt
    """
    template = SAFETY_REWRITE_PROMPT_DEBUG if debug_mode else SAFETY_REWRITE_PROMPT
    return template.format(original_prompt=original_prompt)


def build_scene_ref_rewrite_prompt(original_prompt: str) -> str:
    """构建场景参考图专用改写 Prompt"""
    return SCENE_REF_REWRITE_PROMPT.format(original_prompt=original_prompt)


def build_char_ref_rewrite_prompt(original_prompt: str) -> str:
    """构建角色参考图专用改写 Prompt"""
    return CHAR_REF_REWRITE_PROMPT.format(original_prompt=original_prompt)


def detect_sensitive_content(text: str) -> Dict:
    """
    检测文本中的敏感内容

    Args:
        text: 要检测的文本

    Returns:
        检测结果
        {
            "has_sensitive": True/False,
            "categories": ["death", "blood"],
            "details": [{"word": "killed", "category": "death"}]
        }
    """
    suggestions = get_replacement_suggestions(text)

    categories = list(set(s["category"] for s in suggestions))

    return {
        "has_sensitive": len(suggestions) > 0,
        "categories": categories,
        "count": len(suggestions),
        "details": suggestions
    }


# =============================================================================
# 示例用法
# =============================================================================

EXAMPLE_USAGE = '''
# 方法1: 使用 Haiku 智能改写（推荐）
async def rewrite_prompt_with_haiku(original_prompt: str) -> str:
    """用 Claude Haiku 智能改写被拒绝的 prompt"""
    import anthropic

    client = anthropic.AsyncAnthropic()

    rewrite_prompt = build_rewrite_prompt(original_prompt)

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": rewrite_prompt}]
    )

    return response.content[0].text.strip()


# 方法2: 简单规则替换（低成本，但效果有限）
def rewrite_prompt_simple(original_prompt: str, genre: str = None) -> str:
    """简单规则替换，不使用 LLM"""
    return apply_simple_replacements(original_prompt, genre)


# 方法3: 先检测再决定是否改写
def should_rewrite(prompt: str) -> bool:
    """检测是否需要改写"""
    detection = detect_sensitive_content(prompt)
    return detection["has_sensitive"]


# 完整流程示例
async def safe_image_generation(prompt: str, genre: str = None):
    """带安全改写的图像生成流程"""

    # 1. 检测敏感内容
    detection = detect_sensitive_content(prompt)

    if detection["has_sensitive"]:
        print(f"[SafeGen] ⚠️ 检测到敏感内容: {detection['categories']}")
        print(f"[SafeGen] 敏感词数量: {detection['count']}")

        # 2. 智能改写
        rewritten = await rewrite_prompt_with_haiku(prompt)
        print(f"[SafeGen] ✅ Prompt 已改写")

        prompt = rewritten

    # 3. 调用图像生成 API
    # result = await generate_image(prompt)
    # return result
'''


# =============================================================================
# 设计说明
# =============================================================================

DESIGN_NOTES = """
## 设计说明

### 为什么需要两层改写策略？

1. **简单规则替换** (apply_simple_replacements)
   - 优点: 零成本、即时响应
   - 缺点: 可能破坏句子流畅性
   - 适用: 轻度敏感内容、紧急降级

2. **Haiku 智能改写** (build_rewrite_prompt)
   - 优点: 保持语义连贯、保留艺术风格
   - 缺点: 需要额外 API 调用 (~$0.001)
   - 适用: 复杂场景、重要内容

### 推荐使用流程

```
Gemini 生成
    ↓
成功 → 返回结果
    ↓
失败 (CONTENT_SAFETY)
    ↓
用 Haiku 智能改写
    ↓
重试 Gemini
    ↓
成功 → 返回结果
    ↓
仍失败 → 简单规则替换 + 重试
    ↓
成功 → 返回结果
    ↓
仍失败 → 返回错误，通知用户
```

### 题材覆盖

| 题材 | 典型敏感内容 | 改写策略 |
|------|-------------|----------|
| 武侠 | 剑伤、决斗、死亡 | 聚焦情感、用"fallen"替代 |
| 悬疑 | 谋杀、尸体、血迹 | 用暗示和氛围替代直接描述 |
| 战争 | 伤亡、战场、暴力 | 聚焦人物情感、抽象化冲突 |
| 赛博朋克 | 反乌托邦、暴力镇压 | 用科技术语替代暴力词汇 |

### 成本估算

- Haiku 改写: ~$0.001/次
- 假设 5% prompt 需要改写
- 15 shot 故事: 约 1 次改写 = $0.001
- 成本可忽略不计
"""
