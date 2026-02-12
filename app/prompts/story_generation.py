"""Story generation prompt templates"""

# Style descriptions for visual generation
STYLE_DESCRIPTIONS = {
    "realistic": "写实摄影风格，真实光影，电影质感",
    "illustration": "精美插画风格，色彩丰富，艺术感强",
    "cyberpunk": "赛博朋克风格，霓虹灯光，未来都市",
    "ink": "中国水墨风格，留白意境，传统美学",
    "cartoon": "卡通动画风格，Q版可爱，色彩明快",
    "chinese": "中国风，古典元素，传统配色",
    "manga": "日本漫画风格，分镜感强，情绪张力",
    "oil_painting": "油画风格，厚重笔触，古典美感",
    "watercolor": "水彩风格，透明轻盈，梦幻氛围",
    "pixel": "像素艺术风格，复古游戏感",
    "warm_illustration": "温馨插画风格，柔和色调，治愈系",
}


# 角色类型详细描述模板
CHARACTER_DETAIL_TEMPLATE = """
### 角色描述格式说明

对于每个角色，必须提供极度详细的外貌描述，确保在不同场景中保持视觉一致性。

**人类角色需要包含：**
- 年龄阶段：child/teen/young_adult/adult/middle_aged/elderly
- 性别：male/female
- 体型：身高(tall/medium/short) + 体格(slim/athletic/average/stocky)
- 皮肤：肤色(pale/fair/medium/olive/tan/brown/dark)
- 面部：脸型(oval/round/square/heart)
- 头发：颜色+长度+发型+质地（如：black long straight silky hair with bangs）
- 眼睛：颜色+形状+大小（如：large round dark brown eyes）
- 其他：眉毛、鼻子、嘴唇的特征
- 特殊标记：疤痕、痣、雀斑等
- 服装：上衣+下装+鞋子+配饰+风格

**动物角色需要包含：**
- 物种+品种：如 orange tabby cat, golden retriever dog
- 体型：tiny/small/medium/large + 体形(slim/stocky/round)
- 毛发：颜色+图案+长度+质地（如：bright orange short fur with subtle tabby stripes）
- 眼睛：颜色+形状（如：large round golden-amber eyes）
- 鼻子：颜色（pink/black/brown）
- 耳朵：形状（pointed/floppy/round）
- 尾巴：长度+形态（如：long fluffy tail）
- 特殊标记：白色脚掌、独特花纹等
"""


# 场景位置结构化描述模板
LOCATION_FORMAT_TEMPLATE = """
### 场景位置格式说明（unique_locations）

在生成故事前，先分析故事中出现的所有独特场景位置，输出到 `unique_locations` 数组。

**每个独特场景包含：**
- `location_id`: 唯一标识符（英文+下划线，如 "xiaoming_apartment", "bamboo_forest_1"）
- `display_name`: 场景的显示名称（中文）
- `location_type`: 场景类型
  - "interior_only": 只有室内（如山洞、船舱、电梯内）
  - "exterior_only": 只有室外（如森林、海滩、山顶、街道）
  - "both": 有室内和室外（如便利店、公寓、客栈、飞船）
- `interior_description`: 室内视觉描述（英文，如果有interior）
- `exterior_description`: 室外视觉描述（英文，如果有exterior）
- `key_visual_elements`: 关键视觉元素列表（用于保持一致性）

**重要规则：**
1. 同一栋建筑的不同区域属于同一个location（如便利店的收银台、货架区、门口）
2. 不同人物的家是不同的location（如"小明家"和"小红家"需要分开定义）
3. 描述必须是英文，便于图像生成
4. `key_visual_elements` 用于确保同一场景在不同镜头中保持视觉一致
"""


# 视觉风格详细描述模板
VISUAL_STYLE_TEMPLATE = """
### 视觉风格格式说明

故事有两层视觉风格：

**1. 全局风格（visual_style）- 保持整体一致性：**
- art_style: 艺术风格（illustration/anime/realistic/watercolor/oil_painting/3d_render）
- rendering: 渲染风格（soft/sharp/painterly/cel_shaded）
- detail_level: 细节程度（high/medium/stylized）

**2. 场景风格（scene_style）- 每个场景可独立变化：**
- color_palette: 色调（warm/cool/neutral/vibrant/muted/pastel/dark/golden）
- lighting: 光线类型（soft/dramatic/natural/backlit/dim/harsh/ethereal）
- atmosphere: 氛围（warm/cozy/mysterious/peaceful/melancholic/tense/hopeful/dark/triumphant）
- weather: 天气（clear/cloudy/rainy/stormy/foggy/snowy）
- time_of_day: 时间（dawn/morning/noon/afternoon/golden_hour/dusk/night/midnight）

场景风格应随剧情发展变化：
- 开头铺垫：温暖、明亮、柔和
- 冒险试炼：紧张、神秘、戏剧性光线
- 绝望时刻：阴暗、冷色调、压抑
- 重生结局：金色光芒、希望、温暖回归
"""


def build_story_generation_prompt(
    idea: str,
    style: str,
    chapter_number: int,
    total_chapters: int,
    duration_minutes: int,
    character_count: int,
    language: str,
    previous_summary: str | None = None,
    characters_json: str | None = None,
    min_scenes: int | None = None,
) -> str:
    """
    构建故事生成的prompt

    关键要求：
    1. 生成的故事文本要适合TTS朗读（旁白/对白形式）
    2. 根据时长估算字数（中文约200字/分钟朗读速度）
    3. 故事要有明确的分镜提示（用于后续图像生成）
    4. 如果是续集章节，要衔接前文摘要
    """
    # 中文朗读速度约200字/分钟
    estimated_word_count = duration_minutes * 200

    style_desc = STYLE_DESCRIPTIONS.get(style, style)

    # 计算最少场景数
    if min_scenes:
        scene_requirement = f"**最少场景数**: {min_scenes}个场景（必须达到，非常重要！）"
    else:
        scene_requirement = f"**建议场景数**: 约{max(4, duration_minutes * 2)}个场景"

    prompt = f"""你是一位专业的短视频编剧，擅长创作适合社交媒体传播的短剧内容。

## 创作任务

根据以下创意，创作一个短剧的第{chapter_number}章（共{total_chapters}章）。

**用户创意**: {idea}
**视觉风格**: {style_desc}
**角色数量**: {character_count}个主要角色
**目标时长**: {duration_minutes}分钟
**目标字数**: 约{estimated_word_count}字（旁白+对白总计）
{scene_requirement}
**语言**: {language}

"""

    if previous_summary and chapter_number > 1:
        prompt += f"""
## 前情提要

{previous_summary}

## 已有角色

{characters_json if characters_json else "（根据前情提要中的角色继续）"}

请确保本章与前文剧情连贯，角色性格一致。

"""

    prompt += f"""
## 输出格式要求

请严格按照以下JSON格式输出：

```json
{{
  "title": "本章标题",
  "synopsis": "故事简介（50字以内）",
  "summary": "本章内容摘要（100-150字，用于下一章参考）",

  "visual_style": {{
    "art_style": "illustration",
    "rendering": "soft",
    "color_palette": "warm",
    "primary_colors": ["golden", "cream", "soft orange"],
    "lighting": "soft natural",
    "light_source": "sunlight",
    "time_of_day": "afternoon",
    "atmosphere": "warm and cozy",
    "mood": "heartwarming",
    "detail_level": "high"
  }},

  "unique_locations": [
    {{
      "location_id": "convenience_store_24h",
      "display_name": "24小时便利店",
      "location_type": "both",
      "interior_description": "Typical Asian 24-hour convenience store interior, bright fluorescent lighting, white tile floor, multiple aisles with snacks and drinks, refrigerated section with glass doors along the wall, checkout counter near entrance with cash register",
      "exterior_description": "Modern convenience store exterior at night, illuminated storefront with large glass windows, glowing signage, automatic sliding doors, small parking area with street lamps",
      "key_visual_elements": ["fluorescent lights", "blue-white color tone", "glass refrigerators", "tile floor", "checkout counter"]
    }},
    {{
      "location_id": "bamboo_forest",
      "display_name": "翠竹林",
      "location_type": "exterior_only",
      "interior_description": null,
      "exterior_description": "Dense bamboo forest, tall slender green bamboo stalks reaching toward the sky, filtered sunlight through bamboo leaves creating dappled shadows, misty atmosphere, narrow winding path between bamboo groves",
      "key_visual_elements": ["green bamboo stalks", "filtered light", "mist", "narrow path", "bamboo leaves"]
    }},
    {{
      "location_id": "protagonist_apartment",
      "display_name": "主角的公寓",
      "location_type": "interior_only",
      "interior_description": "Small cozy studio apartment, warm yellow lighting from desk lamp, bookshelf against wall filled with books, worn comfortable sofa, coffee table with scattered papers and a laptop, window with city night view",
      "exterior_description": null,
      "key_visual_elements": ["warm lighting", "bookshelf", "cozy atmosphere", "desk lamp", "city night view"]
    }}
  ],

  "characters": [
    {{
      "id": "char_001",
      "name": "角色中文名",
      "name_en": "Character English Name",
      "role_in_story": "protagonist/supporting/background",
      "character_type": "human/animal/creature",
      "personality_visual": "cheerful/serious/shy/energetic/calm",
      "default_expression": "smiling/neutral/determined/gentle",

      "human": {{
        "gender": "male/female",
        "age_range": "child/teen/young_adult/adult/middle_aged/elderly",
        "height": "tall/medium/short",
        "body_type": "slim/athletic/average/stocky"
      }},

      "physical": {{
        "ethnicity": "East Asian/South Asian/Caucasian/African/Latino/Middle Eastern",
        "skin_tone": "pale/fair/medium/olive/tan",
        "face_shape": "oval/round/square/heart",
        "hair_color": "具体颜色如 jet black, chestnut brown",
        "hair_style": "具体发型如 short messy, long straight with bangs",
        "hair_texture": "silky/fluffy/curly/wavy",
        "eye_color": "具体颜色如 dark brown, bright blue",
        "eye_shape": "round/almond/hooded/upturned",
        "eye_size": "large/medium/small",
        "eyebrows": "thick arched/thin straight/natural",
        "nose": "small upturned/straight/button",
        "lips": "thin/medium/full",
        "distinctive_marks": ["freckles on cheeks", "small mole near left eye"]
      }},

      "animal": {{
        "species": "cat/dog/rabbit/bird",
        "breed": "具体品种如 orange tabby, golden retriever",
        "fur_color": "主要毛色如 bright orange",
        "fur_pattern": "solid/tabby/spotted/striped/bicolor",
        "fur_length": "short/medium/long/fluffy",
        "fur_texture": "smooth/fluffy/silky/soft",
        "body_size": "tiny/small/medium/large",
        "body_shape": "slim/round/stocky/muscular",
        "eye_color": "amber/golden/blue/green/brown",
        "eye_shape": "large round/almond/slanted",
        "nose_color": "pink/black/brown",
        "ear_shape": "pointed/floppy/round/tall",
        "tail": "long fluffy/short/bushy/curled",
        "distinctive_marks": ["white patch on chest", "striped pattern on forehead"]
      }},

      "clothing": {{
        "top": "white button-up shirt with rolled sleeves",
        "bottom": "dark blue jeans",
        "footwear": "white canvas sneakers",
        "accessories": ["round silver-framed glasses", "leather watch"],
        "style": "casual modern"
      }},

      "extra_details": "任何额外的视觉细节"
    }}
  ],

  "scenes": [
    {{
      "scene_id": 1,
      "story_phase": "opening/adventure/crisis/climax/resolution",
      "location_ref": "convenience_store_24h",
      "location_area": "收银台附近",
      "location_type_used": "interior",
      "time": "时间（如：golden hour sunset, early morning）",
      "mood": "氛围（如：tense, heartwarming, mysterious）",
      "scene_style": {{
        "color_palette": "warm/cool/dark/golden/muted",
        "lighting": "soft/dramatic/dim/harsh/ethereal",
        "atmosphere": "cozy/tense/melancholic/hopeful/triumphant",
        "weather": "clear/cloudy/rainy/stormy",
        "time_of_day": "morning/afternoon/golden_hour/night"
      }},
      "characters_in_scene": ["char_001", "char_002"],
      "character_actions": {{
        "char_001": "standing alone, looking lost",
        "char_002": "approaching slowly, head tilted"
      }},
      "visual_description": "完整的画面构图描述（英文），包括环境细节、光线、角色位置和动作。【严格禁止】不要在此字段描述角色的服装颜色/款式！服装信息已在characters.clothing定义，系统会自动注入。只用 (char_001)/(char_002) 等占位符标注角色位置即可",
      "narration": "这个场景的旁白或对白文本（中文，会被TTS朗读）",
      "duration_hint": 15
    }}
  ],

  "total_scenes": 4,
  "word_count": 200
}}
```

{CHARACTER_DETAIL_TEMPLATE}

{VISUAL_STYLE_TEMPLATE}

{LOCATION_FORMAT_TEMPLATE}

## 创作要点

1. **角色一致性（最重要！）**:
   - characters中的每个角色必须有极度详细、精确、固定的外貌描述
   - 人类角色必须填写human字段（包含gender、age_range）和physical字段
   - 动物角色必须填写animal字段
   - 这些描述会被用于所有场景的图像生成，必须具体到每个视觉特征
   - 颜色描述要用具体词汇（如"bright orange"而非"orange"，"jet black"而非"black"）

   **字段命名强制要求（必须严格遵守！）**:
   - 使用 `character_type` 而非 `type`
   - 使用 `role_in_story` 而非 `role`
   - 性别放在 `human.gender` 而非根级 `gender`
   - 年龄放在 `human.age_range` 而非 `age_appearance`

2. **角色视觉差异化（同样重要！）**:
   - **同一故事中的角色必须在外貌上有明显差异，即使是同性别**
   - 发型必须不同：长发/短发/中长、直发/卷发/波浪、扎起/披散
   - 服装风格必须不同：休闲/职业/运动/艺术/优雅
   - 面部特征要有区分：
     - face_shape: 使用不同值（oval/round/square/heart/diamond/oblong）
     - eye_shape: 使用不同值（almond/round/monolid/hooded/upturned）
     - nose: 使用不同值（small straight/prominent/button/aquiline）
     - lips: 使用不同值（thin/full/medium/heart-shaped）
   - **禁止所有角色使用同一套"默认美女/帅哥"模板**
   - 区分度参考：想象观众第一眼就能分辨出"这是A角色"还是"B角色"
   - **种族/民族一致性**：同一故事中的角色应保持种族一致（除非剧情需要）。中国故事的角色应有亚洲面孔特征（如单眼皮/内双、黑发/深棕发、亚洲肤色）

3. **全局风格一致 + 场景风格变化**:
   - visual_style定义整个故事的艺术风格（art_style, rendering），保持统一
   - 每个场景的scene_style可以独立变化，随剧情发展调整色调、光线、氛围

4. **场景拆分原则（重要！短视频节奏关键）**:
   - **每个scene的narration控制在40-80字**（对应10-20秒音频）
   - 如果一个情节单元内容较多，应主动拆分成多个连续scene
   - 拆分依据：地点变化、人物动作变化、镜头切换（全景/中景/特写）、情绪转折
   - 例如"篝火夜谈"可以拆成：全景入场 → 特写讲述者 → 特写倾听者 → 温馨合影
   - **每个scene的visual_description要描述单一画面**，适合直接用于AI图像生成

5. **字数与时长对应**:
   - 中文TTS朗读速度约 **4字/秒**（非200字/分钟！）
   - 40字 ≈ 10秒，80字 ≈ 20秒，120字 ≈ 30秒
   - **duration_hint 应该 = narration字数 ÷ 4**
   - 分镜数量参考：
     - 3分钟视频（180秒）→ 约18-30个scene
     - 5分钟视频（300秒）→ 约30-50个scene
     - 8分钟视频（480秒）→ 约48-80个scene

6. **迪士尼式故事结构**（如果故事较复杂）:
   - **Opening (开头铺垫)**: 建立世界观，展示主角的平凡生活和内心渴望
     - scene_style: warm色调, soft光线, cozy/peaceful氛围
   - **Adventure (冒险试炼)**: 主角踏上旅程，遇到挑战和盟友
     - scene_style: vibrant/cool色调, dramatic光线, adventurous/tense氛围
   - **Crisis (绝望时刻)**: 最大的危机，一切似乎失去希望
     - scene_style: dark/muted色调, dim/harsh光线, melancholic/dark氛围
   - **Climax (高潮)**: 主角找到力量，面对最终挑战
     - scene_style: dramatic对比, 从dark到golden的转变
   - **Resolution (重生结局)**: 胜利、成长、回归，但已不同
     - scene_style: golden/warm色调, ethereal/soft光线, triumphant/hopeful氛围

7. **场景描述（服装一致性关键！）**:
   - visual_description只需描述环境和构图，【严禁描述角色服装颜色/款式】
   - 角色外貌和服装会自动从characters定义注入到image_prompt
   - 用 (char_001) 占位符标注角色位置，如："(char_001) stands near the counter, (char_002) approaches from behind"
   - 错误示范：❌ "a man in burgundy shirt" ← 禁止自创服装颜色
   - 正确示范：✅ "(char_003) holding a beer can" ← 只描述动作和位置
   - characters_in_scene指定场景中出场的角色ID
   - character_actions描述每个角色在该场景的具体动作/表情

8. **故事节奏**: 短视频观众注意力有限，开头3秒必须抓人，每个场景都要有信息增量

9. **旁白风格**: narration要适合朗读，语言流畅自然，情感饱满

10. **场景位置结构化（重要！）**:
    - 先分析故事中的独特场景，填写 `unique_locations` 数组
    - 每个scene使用 `location_ref` 引用 unique_locations 中的 location_id
    - `location_area` 描述该场景在location中的具体区域（如"收银台附近"、"二楼阳台"）
    - `location_type_used` 标明本场景使用室内(interior)还是室外(exterior)
    - 同一栋建筑的不同区域（如便利店收银台、货架区、门口）都引用同一个 location_id
    - 不同人物的家（如"小明家"和"小红家"）必须是不同的 location_id
    - interior_description 和 exterior_description 必须是英文

现在开始创作：
"""

    return prompt
