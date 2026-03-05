# Shot间自然过渡改善方案 — 给Claude Code的完整指令

> **问题**：条漫形式（连续静态图+BGM）中，前后shot在场景和角色方面的过渡变化生硬，不像专业分镜师的镜头调度，更像是同一张图上贴了不同的人物。
>
> **目标**：让每个shot既保持场景/角色一致性，又像真正的分镜大师一样，镜头语言随叙事自然流动。

---

## 一、问题本质

当前系统生成的相邻shot存在"构图复制"现象：前序shot传入作为参考时，模型倾向于复制它的角度、构图、色调，导致：
- 新角色像被PS进场景的
- 相邻镜头几乎是同一张图的微调版
- 缺乏专业影视作品中镜头语言的节奏感和呼吸感

根本原因：**系统只告诉模型"保持一致"，没有告诉模型"如何变化"**。

---

## 二、需要改善的维度全景（12大类）

### 2.1 镜头语言维度（Camera Language）

这是最核心的过渡手段。相邻shot之间，以下元素**必须**根据叙事需要变化：

**景别变化（Shot Size）**——不能连续多个shot都是同一景别：
- `extreme_wide_shot` → 强调环境，人物渺小，适合开场/转场/表达孤独
- `wide_shot` → 展示人物与环境关系，适合动作场景
- `medium_wide_shot` (cowboy shot) → 膝盖以上，适合走动/对话
- `medium_shot` → 腰部以上，标准对话景别
- `medium_close_up` → 胸部以上，强调表情同时保留手势
- `close_up` → 面部特写，强调情绪
- `extreme_close_up` → 眼睛/手部/物品细节，关键时刻

**景别过渡规则**：
- 一般不做超过两级的跳切（如wide直接跳extreme_close_up），除非是刻意的戏剧效果
- 情感递进时景别应逐步推近（wide → medium → close_up）
- 场景切换/时间跳跃时可以用wide重新建立场景
- 连续3个以上相同景别 = 节奏死板，必须避免

**机位角度变化（Camera Angle）**：
- `eye_level` → 中性，观众与角色平等
- `high_angle` → 俯拍，被摄者显得弱小、脆弱、被压迫
- `low_angle` → 仰拍，被摄者显得强大、威严、有希望
- `birds_eye` → 鸟瞰，上帝视角，命运感
- `worms_eye` → 极低角度，戏剧化、不稳定感
- `dutch_angle` → 倾斜，不安、紧张、异常
- `over_the_shoulder` → 过肩，对话场景主观视角

**角度过渡规则**：
- 对话场景应交替使用不同角色的视角（正反打）
- 情绪转折时角度应配合变化（角色从强势变弱势 → 从low_angle切到high_angle）
- 不要连续多个shot都是eye_level，这是最常见的"平淡"原因

### 2.2 构图维度（Composition）

**主体位置（Subject Position）**——不能每张图主角都站在画面正中央：
- 三分法：主体放在三分线交点（左三分/右三分）
- 视线方向（Look Room）：角色看向的方向留出空间
- 引导线（Leading Lines）：利用场景中的线条引导视线
- 前景/中景/背景层次：增加画面纵深感
- 负空间（Negative Space）：大面积留白强调孤独或重要性

**构图过渡规则**：
- 相邻shot的主体位置应该变化（shot N角色在左三分 → shot N+1角色在右三分）
- 前景元素应该变化（shot N前景是雨滴 → shot N+1前景是栏杆）
- 画面重心的移动应该和叙事焦点的转移一致

### 2.3 光影维度（Lighting）

同一场景内光影基调保持一致，但光影的**强调方式**应随情绪变化：
- `high_key` → 明亮均匀，积极向上
- `low_key` → 强烈明暗对比，戏剧性、神秘
- 侧光 → 强调轮廓和质感
- 逆光 → 剪影效果，神秘或浪漫
- `practical_lights` → 场景中的实际光源（路灯、霓虹灯）增加真实感

**光影过渡规则**：
- 同一场景内色温和光源方向必须一致（MUST MAINTAIN）
- 但光影的对比度、明暗分布可以随镜头角度自然变化（SHOULD VARY）
- 特写镜头的光影通常比全景更戏剧化（面部有更强的明暗对比）

### 2.4 角色状态维度（Character Dynamics）

角色外观的**身份锚点**必须锁死，但**叙事变量**必须动态变化：

**身份锚点（Identity Anchors）= 锁死不动**：
- 面部结构、体型比例、肤色
- 标志性特征（疤痕、胎记、独特花纹）
- 基础服装设计的款式和颜色

**叙事变量（Narrative Variables）= 必须随剧情变化**，共六层：

1. **情绪层**：表情、眼神、气质、肢体语言的情绪倾向
2. **物理状态层**：疲劳度、伤痕、汗水、温度反应（脸红、起鸡皮疙瘩）
3. **装备层**：服装的增减和状态变化（室内脱外套、淋雨后衣服湿透）、道具的持有和位置（眼镜摘下来挂领口、武器从背后拔出握手中）、配饰佩戴与否
4. **环境交互层**：光影投射在角色身上的变化、天气痕迹（雪落肩上、风吹乱头发）、环境附着物（泥巴、灰尘）
5. **可见性层**：全身/半身/局部、正面/侧面/背影、遮挡/反射/剪影
6. **时间层**：跨时间线时的胡茬、伤口结痂、晒黑、消瘦

**角色过渡规则**：
- 相邻shot中角色的姿态、表情必须配合叙事变化，不能保持同一个pose
- 角色在画面中的位置（左/中/右、前景/背景）应该随镜头视角自然变化
- 多人场景中角色的空间关系（面对面/背对/并肩/包围）应反映情感关系

### 2.5 场景连续性维度（Environment Continuity）

**必须保持一致的（MUST MAINTAIN）**：
- 场景的建筑结构和空间布局
- 光线方向和色温
- 天气条件（雨的强度、湿地面、雾的密度）
- 时间氛围（白天/黄昏/夜晚）
- 环境中的关键道具和标志物

**应该自然变化的（SHOULD VARY）**：
- 场景在画面中的呈现角度（同一个公交站，换个方向拍）
- 前景/背景元素的可见性（换角度后某些元素被遮挡/暴露）
- 环境细节的强调点（shot N强调霓虹灯，shot N+1强调湿地面的反光）

### 2.6 叙事节奏维度（Narrative Pacing）

**每个shot对应6-8秒的旁白内容**，镜头语言应该服务于叙事节奏：

- 开场/建立场景：wide shot，展示环境
- 对话/互动：medium shot交替，正反打
- 情感递进：景别逐步推近，从medium到close_up
- 高潮/转折：extreme_close_up或dutch_angle，打破常规
- 结束/余韵：拉回wide shot或留白

**节奏过渡规则**：
- 紧张感递增时，镜头切换频率应该加快（更短的shot）
- 舒缓/沉思时，可以用更长的停留和更宽的景别
- 情绪转折点前后的景别跳跃可以更大（增加冲击力）

### 2.7 镜头衔接维度（Shot Continuity）

相邻shot之间应遵循专业影视制作的衔接规则：

- **30度规则（30-Degree Rule）**：相邻两个shot的机位至少移动30度。如果移动不足30度，观众会感觉像"跳切"（jump cut），非常生硬。这是当前条漫生硬的核心原因之一——模型复制前序shot的构图时，相当于0度变化，严重违反此规则。配合使用的是**20mm/30度规则**：要么改变焦距至少20mm，要么改变角度至少30度，两者至少满足一个。但也不能走极端——从wide直接跳到extreme_close_up而没有中间过渡，同样会让观众不适。
- **180度规则**：对话场景中，摄像机不要越过两个角色之间的假想线。三人场景会产生三条假想轴线，需要把其中两个角色分组到画面一侧来简化。
- **Match on Action**：上一个shot中角色正在做的动作，在下一个shot中应该有逻辑延续
- **视线匹配（Eyeline Match）**：如果shot N中角色看向画面右侧，shot N+1应该展示他看到的东西（从画面左侧出现）
- **Screen Direction**：角色退出画面的方向应该和进入下一个shot的方向保持逻辑一致（右出左入）

这些信息应该写入 `shot_continuity_notes` 字段：
```json
{
  "from_shot": 4,
  "to_shot": 5,
  "continuity_type": "match_on_action",
  "note": "Old Zhou is pouring tea in shot 4; shot 5 should show the cup being placed down"
}
```

### 2.8 空间纵深维度（Spatial Depth & Staging）

这是被忽略但对"自然感"影响极大的一个维度——画面的三维纵深感。

**深层调度（Deep Staging）vs 扁平调度（Flat Staging）**：
- **Deep Staging**：在前景、中景、背景都放置有意义的元素，制造三维纵深感。适合戏剧性场景、强调人物与环境的关系、表达孤独或权力感。经典案例：《公民凯恩》的深焦摄影。
- **Flat Staging**：所有元素摆在同一个平面上，消除纵深感。适合喜剧、荒诞场景、表达角色被困住的感觉。Wes Anderson的标志性风格。

**纵深过渡规则**：
- 相邻shot的纵深层次应该有变化——shot N是扁平的双人正面对话，shot N+1可以切到有纵深的过肩镜头
- 前景元素（foreground）是制造纵深感最有效的手段：虚化的栏杆、雨滴、窗框、肩膀
- 当角色从背景走向前景（或反之），制造Z轴运动感，画面立刻活起来

### 2.9 角色空间关系维度（Character Blocking）

角色在画面中的相对位置直接传达情感关系，这不能是随机的：

**垂直关系**：
- 一个角色站着、另一个坐着（或蹲着）→ 权力/地位差异
- 从楼梯上方俯视 → 压迫感、掌控感
- 蹲下来和孩子平视 → 平等、温柔

**水平关系**：
- 角色占据画面两端 → 对立、冲突、距离感
- 角色紧挨在一起 → 亲密、脆弱、共情
- 一个角色在前景大、另一个在背景小 → 心理距离、主次关系

**朝向关系**：
- 面对面 → 对话、对峙
- 背对背 → 分歧、冷战
- 并肩同向 → 同盟、共同面对
- 一人看另一人、另一人看别处 → 单方面的关注/忽视

**过渡规则**：
- 相邻shot中角色的空间关系应该反映叙事的情感进展
- 同一对话场景中，角色间距逐渐缩小 = 关系拉近；逐渐拉大 = 关系疏远
- 角色在画面中的位置变化应该有叙事动机，不能无理由跳位

### 2.10 镜头焦距维度（Lens & Focal Length）

**这是被严重低估的prompt控制工具。** Google官方文档明确指出，Gemini对摄影和电影术语有很强的理解力，"wide-angle shot, macro shot, low-angle perspective, 85mm portrait lens, Dutch angle"都能精确控制构图。焦距不仅影响视野范围，更直接影响画面的空间压缩感、景深、以及角色面部比例。

**焦距与叙事功能的对应关系**：

| 焦距 | 视觉效果 | 叙事用途 | 适用shot_type |
|------|----------|----------|--------------|
| 24mm 广角 | 夸张透视、空间感开阔、前景变大 | 建立场景、展示环境规模、制造压迫感 | extreme_wide, wide_shot |
| 35mm 标准广角 | 自然透视、环境+人物兼顾 | 街拍、行走场景、环境人像 | wide_shot, medium_wide |
| 50mm 标准 | 最接近人眼视角、自然纪实感 | 日常对话、中性叙事、纪录片感 | medium_shot |
| 85mm 人像 | 面部比例最自然、背景柔化 | 情感特写、角色内心、重要对话 | medium_close_up, close_up |
| 135mm 长焦 | 强烈背景压缩、空间距离感消失 | 孤独感、被监视感、远距离窥视 | close_up, extreme_close_up |
| 200mm+ 超长焦 | 极度压缩、前后景几乎叠合 | 人群中的孤立、城市压迫感 | 特殊效果 |

**Prompt中的焦距写法**（Gemini实测有效）：
- `"shot with an 85mm portrait lens, shallow depth of field, f/1.8"` — 柔和人像
- `"24mm wide-angle, deep focus, expansive perspective"` — 开阔环境
- `"135mm telephoto, compressed background, bokeh"` — 压缩长焦

**过渡规则**：
- 焦距变化应该配合景别变化：wide_shot配24-35mm，close_up配85-135mm
- 不要在相邻shot中使用相同焦距+相同景别——这会让画面看起来几乎一样
- 情感递进时焦距应该同步推近：24mm → 50mm → 85mm → 135mm
- 每个shot的prompt应该包含焦距信息，**这是防止Gemini生成默认eye-level中景的最有效手段**

### 2.11 色调一致性维度（Color Grading Consistency）

**同一个故事中，色调漂移会严重破坏沉浸感。** 就像专业电影的调色是全片统一的基调+局部情绪变化，AI生成的sequential images也需要锁定一个基础色调。

**基础色调锁定**（在StyleEnforcer或场景级别设定）：
- **暖色调**（warm tones）：橙、黄、棕 → 温馨、怀旧、亲密
- **冷色调**（cool tones）：蓝、灰、青 → 疏离、紧张、悬疑
- **低饱和**（muted/desaturated）：真实感、沉重、严肃
- **高饱和**（vibrant/saturated）：活力、童话、梦幻
- **橙青对比**（teal and orange）：好莱坞经典，人物突出、画面有层次

**色调过渡规则**：
- 同一场景内的色调**必须一致**——这应该写入MUST MAINTAIN
- 跨场景可以有色调变化，但要有叙事动机（从温暖的家切到冷调的雨夜）
- 情绪转折时色调可以渐变：暖色调故事中，冲突场景微妙偏冷
- **在prompt中明确色调词汇**比期待模型自行推断更可靠：
  - `"warm golden hour lighting, amber tones"` 比 `"warm"` 精确得多
  - `"cool blue-grey color palette, desaturated"` 比 `"cold atmosphere"` 好

**Prompt色调模板**：
```
COLOR DIRECTION for this story:
- Base palette: warm amber tones with soft golden highlights
- Shadow color: warm brown (not cool grey)
- Highlight color: soft peach/cream
- Saturation: medium (not oversaturated, not muted)
- Contrast: medium-low (soft, cinematic feel)
This color direction applies to ALL shots unless narrative requires shift.
```

### 2.12 Gemini模型的Prompt最佳实践（Model-Specific）

基于Google官方文档和社区实测，以下是针对Gemini Pro/Flash图像生成的关键实践：

**参考图使用原则**：
- Gemini Pro最多支持14张参考图（5张人物 + 6张物体）
- **每次prompt都要重复完整的角色描述**——模型不会"记住"之前的prompt
- 传入参考图时，使用显式指令：`"Use Image 1 as a reference for how Character X should look"` 而不是只传图不说明
- **每次只改变一个变量**（姿势、光线、或背景）——多变量同时变会导致一致性下降
- 如果角色特征开始漂移，使用hard negatives锁定：`"no bangs, no beard, no eye color change"`

**摄影语言在Prompt中的位置**：
- 角度和焦距放在prompt**开头**，风格描述放在**后面**
- 正面描述（"empty street with no traffic"）比负面描述（"no cars"）效果好
- 使用具体的摄影术语而不是文学描述：
  - ✅ `"medium close-up, 85mm portrait lens, slight low angle, soft window light from camera-left"`
  - ❌ `"a close and intimate view of the character looking pensive in soft light"`

**前序shot图像作为参考的正确使用方式**：
- 明确告诉模型这是环境参考而非构图模板
- 必须配合具体的THIS shot指令（新的角度、新的构图）
- 如果前序shot和当前shot的prompt太相似，模型更倾向于复制——所以prompt越具体越不同越好

---

## 三、技术实现方案

### 3.1 Stage 4 (StoryboardDirector) 改进

**核心改动**：让LLM在生成分镜时，**显式规划相邻shot之间的镜头变化**。

在Stage 4的system prompt中增加以下规则：

```
SHOT TRANSITION RULES (CRITICAL FOR NATURAL FLOW):

Reference framework: The Five C's of Cinematography (Mascelli)
- Camera Angles, Continuity, Cutting, Close-ups, Composition
Every shot transition must satisfy ALL five dimensions.

0. THE 30-DEGREE RULE (MOST IMPORTANT):
   - Between ANY two consecutive shots of the same subject/location,
     the camera must move at least 30 degrees from its previous position
   - Violating this creates a "jump cut" — the #1 cause of unnatural transitions
   - Combined with the 20mm/30-degree rule: change focal length by 20mm OR angle by 30 degrees
   - In practice: if shot N is a medium shot from the front,
     shot N+1 MUST be from a significantly different angle (side, over-shoulder, higher, lower)
   - Exception: intentional axial cuts for dramatic emphasis (e.g., sudden zoom to extreme_close_up)

1. SHOT SIZE VARIATION:
   - Never use the same shot_size for more than 2 consecutive shots
   - Emotional progression: gradually push closer (wide → medium → close_up)
   - Scene establishment: start with wide_shot, then diversify
   - After a close_up, pull back to at least medium_shot before next close_up
   - Avoid jumping more than 2 levels at once (e.g., wide → extreme_close_up)
     unless cutting on action or for deliberate dramatic impact

2. CAMERA ANGLE VARIATION:
   - Alternate angles in dialogue scenes (over_the_shoulder / reverse)
   - Match angle to character power dynamics (dominant = low_angle, vulnerable = high_angle)
   - Use eye_level as neutral reset, not as default for every shot
   - 180-degree rule: stay on one side of the axis line in dialogue scenes

3. COMPOSITION VARIATION:
   - Alternate subject position (left_third → center → right_third)
   - Vary foreground elements between shots
   - Use negative space strategically for emotional beats
   - Alternate between deep staging (foreground/middleground/background layers)
     and flat staging based on emotional needs

4. CHARACTER BLOCKING:
   - Each shot's character state must reflect narrative progression
   - Extract specific body positions from narration (蜷缩 → curled up, not standing)
   - Show environmental effects on characters (rain-soaked, wind-blown hair)
   - Character spatial relationships must reflect emotional dynamics:
     * Vertical: standing vs sitting = power difference
     * Horizontal: far apart = conflict, close together = intimacy
     * Orientation: facing = engagement, back-turned = rejection

5. SPATIAL DEPTH:
   - Vary depth staging between shots — not every shot should be flat
   - Use foreground elements (blurred objects, rain, window frames) for depth
   - Place characters at different depth planes in multi-person scenes
   - General rule: deep space for drama, flat space for comedy/absurdity

6. CONTINUITY NOTES:
   - For each shot transition, specify:
     * continuity_type: match_on_action | eyeline_match | scene_change | time_jump
     * what carries over from previous shot
     * what changes and why
     * estimated camera angle change in degrees (must be ≥30°)

7. LENS & FOCAL LENGTH:
   - Every shot MUST specify a focal length that matches its shot_type:
     * extreme_wide / wide_shot: 24mm or 35mm
     * medium_wide / medium_shot: 35mm or 50mm
     * medium_close_up / close_up: 85mm
     * extreme_close_up: 100mm or 135mm
   - Adjacent shots should not use the same focal length + shot_type combination
   - Emotional progression = focal length progression: 24mm → 50mm → 85mm → 135mm
   - Include lens info in image_prompt: "shot with 85mm portrait lens, f/1.8, shallow depth of field"

8. COLOR GRADING CONSISTENCY:
   - Define a base color palette for the entire story at the story level
   - All shots in the same scene MUST share the same color temperature and palette
   - Color shifts between scenes need narrative justification
   - Use specific color vocabulary in image_prompt, not vague mood words:
     * ✅ "warm amber tones, golden hour lighting, soft peach highlights"
     * ❌ "warm and cozy atmosphere"
   - Shadow and highlight colors should be consistent within a scene
```

### 3.2 Stage 5 (ShotImageGenerator) 改进

> ⚠️ **DEC-014 (2026-03-03)**: previous_shot_image 已移除（Plan A）。以下 VISUAL CONTINUITY REFERENCE 代码块已废弃。环境连续性改由场景参考图 (interior/exterior anchor) + 文字 prompt 保障。保留原内容作为历史参考。

**~~修改 `build_continuity_context_phase2()`~~**（DEC-014 后此函数中 previous_shot 相关逻辑已移除）：

~~当前的VISUAL CONTINUITY REFERENCE指令块需要更精确地区分"保持"和"变化"~~：

```python
if has_previous_shot_image:
    # 获取当前shot和前一个shot的景别差异
    current_shot_size = current_shot.get('shot_type', 'medium_shot')
    previous_shot_size = previous_shot.get('shot_type', 'medium_shot') if previous_shot else None
    
    context_parts.append(f"""
VISUAL CONTINUITY REFERENCE:
A previous shot image is provided showing the same location.

MUST MAINTAIN (environment continuity):
- Location identity and architectural details
- Lighting direction and color temperature  
- Weather conditions (rain intensity, wet surfaces, fog density)
- Time-of-day atmosphere
- Key environmental props and landmarks

MUST VARY (cinematic storytelling):
- Camera angle and shot size: Previous was {previous_shot_size}, THIS shot is {current_shot_size}
- Character positioning and poses: Follow THIS shot's action description
- Composition and framing: Vary subject position, foreground elements, depth layers
- Visual focus point: Based on THIS shot's narrative emphasis

CRITICAL: The previous shot is for ENVIRONMENT reference only.
You are a professional cinematographer — each shot must have its own unique 
camera perspective, composition, and character staging.
Do NOT replicate the previous shot's framing.
Imagine you are physically moving the camera to a new position in the same location.
""".strip())
```

### 3.3 参考图标注最佳实践（Reference Image Labeling）

**来源**：Google官方prompting指南 + Scenario.com的多角色prompt工程实践（2025-2026）

> ⚠️ **DEC-014 (2026-03-03)**: previous_shot_image 已移除。当前 IMAGE 编号从角色参考图开始（Image 1 = 第一个角色参考图），无 previous_shot 占位。以下标注方案中 previous_shot 相关部分已废弃，但角色/场景参考图标注方案仍然适用。

~~当前系统在prompt中通过IMAGE编号映射（Image 1 = previous_shot, Image 2 = char_ref_001...）来告诉模型每张参考图的角色。~~ DEC-014 后 IMAGE 编号已简化（无 previous_shot 占位）。标注方案的核心价值——消除编号错位风险——仍然成立：

**更优方案：直接在参考图上标注角色身份**

核心思路：在上传给模型的参考图上叠加文字标签，让模型"看到"每张图的身份信息，而不是靠prompt文本描述"Image 3 is character X"。

**实现方式**：

```python
from PIL import Image, ImageDraw, ImageFont

def label_reference_image(image_path: str, label: str, output_path: str):
    """在参考图左上角叠加角色身份标签"""
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # 半透明背景条 + 白色文字，不遮挡主体
    font_size = max(20, img.width // 20)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padding = 8
    
    # 绘制半透明背景
    draw.rectangle(
        [4, 4, text_w + padding * 2 + 4, text_h + padding * 2 + 4],
        fill=(0, 0, 0, 180)
    )
    draw.text((padding + 4, padding + 4), label, fill=(255, 255, 255), font=font)
    
    img.save(output_path)
    return output_path
```

**标注规则**：

- **角色参考图（fullbody）**：标注 `Character: {name_en}` — 如 `Character: Su Chen`
- **场景参考图（interior）**：标注 `Scene: {location_name} Interior`
- **场景参考图（exterior）**：标注 `Scene: {location_name} Exterior`
- ~~**前序shot图（previous_shot）**：标注 `Previous Shot (env reference only)`~~ （DEC-014: 已移除，不再传入 previous_shot）

**在prompt中的配合写法变化**：

之前（纯文本映射，容易错位）：
```
IMAGE REFERENCE MAPPING:
- Image 1: Previous shot — use ONLY for environment continuity  ← DEC-014: 已移除
- Image 2: Character fullbody reference — Su Chen (苏晨)        ← DEC-014 后变为 Image 1
- Image 3: Character fullbody reference — Li Wei (李维)          ← DEC-014 后变为 Image 2
- Image 4: Scene interior reference — Coffee shop                ← DEC-014 后变为 Image 3
```

之后（图上有标签，prompt只需声明规则）：
```
CHARACTER & SCENE REFERENCES:
Each reference image is labeled directly on the image.
- Images labeled "Character: XXX" → use to maintain that character's appearance
- Images labeled "Scene: XXX" → use to maintain environment consistency
# DEC-014: "Previous Shot" 标签已废弃，不再传入 previous_shot 图像
```

**为什么这样更好**：

1. **消除编号错位风险**：不再依赖Image N与contents数组的精确对应，模型直接从图上读取身份
2. **多角色场景更清晰**：6人场景传入6张参考图时，模型不用在prompt和图之间来回对照
3. **Google官方推荐**：Gemini的图像理解能力本身就支持读取图上文字，这是模型的原生能力而非hack
4. **降低prompt长度**：不再需要冗长的IMAGE REFERENCE MAPPING块

**关键代码修改点**：

| 文件 | 修改 | 风险 |
|------|------|------|
| `reference_image_manager.py` | 生成fullbody参考图后调用`label_reference_image()` | 🟢 低 |
| `scene_reference_manager.py` | 生成场景图后调用`label_reference_image()` | 🟢 低 |
| ~~`image_generator.py`~~ | ~~previous_shot传入前先标注~~ （DEC-014: 已移除） | — |
| `storyboard_prompts.py` | `build_character_reference_mapping_phase2()` 简化为基于标签的声明式prompt | 🟡 中 |

**⚠️ 注意事项**：
- 标签不能太大遮挡角色关键特征（尤其fullbody参考图的面部区域）
- 标签位置统一放**左上角**，不要放中间
- 用英文标注（模型对英文文字的OCR更准确）
- 建议先在3-5个shot上A/B测试：有标签 vs 无标签，对比角色一致性和角色识别准确率
- 标注后的参考图只用于传入模型，不覆盖原始参考图文件（保留无标注版本）

### 3.4 新增：Shot Transition Validator

在Stage 4输出后，增加一个验证步骤，检查相邻shot的镜头语言是否有足够变化：

```python
def validate_shot_transitions(shots: list) -> list[str]:
    """检查相邻shot之间的镜头语言变化是否足够"""
    warnings = []
    
    for i in range(1, len(shots)):
        prev = shots[i-1]
        curr = shots[i]
        
        # 检查景别是否连续相同
        if prev.get('shot_type') == curr.get('shot_type'):
            if i >= 2 and shots[i-2].get('shot_type') == curr.get('shot_type'):
                warnings.append(
                    f"Shot {curr['shot_id']}: 3+ consecutive {curr['shot_type']} — "
                    f"vary shot size for rhythm"
                )
        
        # 检查角度是否连续相同
        if prev.get('camera_angle') == curr.get('camera_angle'):
            if i >= 2 and shots[i-2].get('camera_angle') == curr.get('camera_angle'):
                warnings.append(
                    f"Shot {curr['shot_id']}: 3+ consecutive {curr['camera_angle']} — "
                    f"vary angle for visual interest"
                )
        
        # 30度规则检查：景别和角度都没变 = 接近0度变化 = 跳切
        same_size = prev.get('shot_type') == curr.get('shot_type')
        same_angle = prev.get('camera_angle') == curr.get('camera_angle')
        same_scene = prev.get('original_scene_id') == curr.get('original_scene_id')
        
        if same_size and same_angle and same_scene:
            warnings.append(
                f"⚠️ Shot {curr['shot_id']}: LIKELY 30-DEGREE RULE VIOLATION — "
                f"same shot_type ({curr.get('shot_type')}) AND same camera_angle "
                f"({curr.get('camera_angle')}) as previous shot in same scene. "
                f"This will produce a jump cut. Change at least one."
            )
        
        # 检查是否从wide直接跳到extreme_close_up（超过两级）
        size_order = ['extreme_wide_shot', 'wide_shot', 'medium_wide_shot', 
                      'medium_shot', 'medium_close_up', 'close_up', 'extreme_close_up']
        prev_idx = size_order.index(prev.get('shot_type', 'medium_shot')) if prev.get('shot_type') in size_order else 3
        curr_idx = size_order.index(curr.get('shot_type', 'medium_shot')) if curr.get('shot_type') in size_order else 3
        
        if abs(prev_idx - curr_idx) > 2:
            warnings.append(
                f"Shot {curr['shot_id']}: Large jump from {prev.get('shot_type')} to "
                f"{curr.get('shot_type')} — consider intermediate shot size "
                f"(unless this is an intentional dramatic cut)"
            )
        
        # 检查构图主体位置是否连续相同（如果有此字段）
        prev_pos = prev.get('composition', {}).get('subject_position')
        curr_pos = curr.get('composition', {}).get('subject_position')
        if prev_pos and curr_pos and prev_pos == curr_pos and same_scene:
            warnings.append(
                f"Shot {curr['shot_id']}: Same subject_position ({curr_pos}) as "
                f"previous shot — vary composition for visual flow"
            )
    
    return warnings
```

### 3.5 Storyboard数据结构增强

每个shot应包含更丰富的镜头信息：

```json
{
  "shot_id": 5,
  "scene_id": 2,
  "shot_type": "medium_close_up",
  "camera_angle": "slight_low_angle",
  "focal_length": "85mm",
  
  "composition": {
    "subject_position": "right_third",
    "foreground": "rain_droplets_on_glass",
    "background": "blurred_neon_signs",
    "depth_layers": "3_layers",
    "depth_style": "deep"
  },
  
  "color_direction": {
    "palette": "cool_blue_grey",
    "color_temperature": "cool",
    "saturation": "low",
    "contrast": "medium_high",
    "narrative_reason": "isolation and loneliness in urban rain"
  },
  
  "character_direction": {
    "char_001": {
      "position_in_frame": "right_third",
      "depth_plane": "middleground",
      "body_posture": "leaning_against_shelter_wall",
      "facial_expression": "pensive_looking_down",
      "eye_line": "downward_at_phone",
      "clothing_state": "coat_collar_turned_up_rain_drops_on_shoulders"
    }
  },
  
  "character_blocking": {
    "spatial_relationship": "isolated_single_character",
    "vertical_dynamic": "neutral",
    "horizontal_dynamic": "off_center_right",
    "orientation": "facing_away_from_camera_3/4_profile"
  },
  
  "transition_from_previous": {
    "continuity_type": "match_on_action",
    "shot_size_change": "medium_shot → medium_close_up (pushing closer)",
    "angle_change": "eye_level → slight_low_angle (building empathy)",
    "focal_length_change": "50mm → 85mm (isolating subject, compressing background)",
    "estimated_angle_change_degrees": 40,
    "composition_change": "subject moves from left_third to right_third",
    "depth_change": "flat → deep (adding foreground rain element)",
    "color_shift": "none (same cool_blue_grey palette)",
    "narrative_reason": "Transitioning from establishing the waiting scene to focusing on character's inner state"
  },
  
  "image_prompt": "...",
  "narration_segment": "..."
}
```

---

## 四、关键文件修改清单

| 文件 | 修改内容 | 风险 |
|------|----------|------|
| `storyboard_director.py` (Stage 4) | System prompt增加Shot Transition Rules | 🟡 中 — 影响LLM输出结构 |
| `storyboard_prompts.py` | `build_continuity_context_phase2()` 增强MUST VARY指令 | 🔴 高 — 直接影响图像生成 |
| `storyboard_prompts.py` | `build_character_reference_mapping_phase2()` 改为基于标签的声明式prompt | 🟡 中 |
| ~~`image_generator.py`~~ | ~~传递previous_shot的shot_type/camera_angle + previous_shot标注~~ （DEC-014: previous_shot 已移除） | — |
| `reference_image_manager.py` | 生成fullbody参考图后叠加角色身份标签 | 🟢 低 — 新增后处理步骤 |
| `scene_reference_manager.py` | 生成场景图后叠加场景类型标签 | 🟢 低 — 新增后处理步骤 |
| `storyboard_service.py` | 新增 `validate_shot_transitions()` | 🟢 低 — 仅验证 |

---

## 五、验证标准

修改后的测试验证：

1. **30度规则**：同一场景内相邻shot不得同时共享shot_type和camera_angle（=接近0度变化=跳切）
2. **景别变化**：相邻3个shot不出现完全相同的shot_type
3. **角度变化**：相邻3个shot不出现完全相同的camera_angle
4. **焦距匹配**：每个shot的image_prompt包含焦距信息，且焦距与景别匹配（wide≠135mm，close_up≠24mm）
5. **色调一致**：同一场景内色调词汇一致，不出现无理由的冷暖跳变
6. **构图变化**：肉眼对比相邻shot，主体位置、前景元素有明显不同
7. **角色自然融入**：角色不像被"贴"进场景，而是自然存在于画面中
8. **场景一致性不降级**：同一地点的建筑结构、光线、天气仍然一致
9. **角色一致性不降级**：角色外观、服装、配饰仍然一致（回归测试必须通过）
10. **过渡元数据完整**：每个shot的transition_from_previous字段完整填充

---

## 六、注意事项

- **角色一致性是产品生命线**，任何镜头变化的优化都不能破坏角色一致性
- Shot生成默认使用 Nano Banana 2（`use_pro_model=False`），Pro 仅作 Premium 储备
- 改动后必须跑完整的角色一致性回归测试
- 先在3-5个shot的小样本上验证效果，再推广到完整故事

---

## 七、技术储备：Seedance 2.0 的 Multi-Shot 生成模式

> **状态**：仅作为未来Phase 7-8视频生成的技术参考，当前阶段不实施。

**背景**：ByteDance于2026年2月10日发布Seedance 2.0，基于Seedream 5.0架构，是第一个真正实现"单prompt生成多shot叙事序列"的视频模型。它的设计思路对序话Story未来从静态图序列过渡到动态视频有直接参考价值。

### 7.1 Seedance 2.0 的核心能力

**Multi-Shot Narrative Generation**：单个prompt可以生成包含多个镜头切换的15秒视频，角色在不同shot间保持视觉一致，镜头角度自然切换。

**关键prompt技巧——"lens switch"触发词**：在prompt中使用"lens switch"关键词触发镜头切换。例如：
```
Shot 1: side angle, a donkey rides a motorcycle bursting through a barn fence, chickens scatter. 
Shot 2: close-up of spinning tires on sand, then aerial shot of the donkey doing donuts, dust clouds rising. 
Shot 3: snow mountain backdrop, the donkey launches off a hillside.
```
模型会在一次生成中创建这三个shot的序列，同时维持主体、风格和场景的连续性。

**Character Lock机制**：Seedance 2.0使用"Character Lock"引擎，为角色创建临时的"数字护照"，AI在每一个新shot中引用这份护照来保持角色身份一致。这与我们当前的参考图传递链思路类似，但在视频维度上实现。

**统一的多模态输入**：支持最多12个同时引用输入（图像、视频、音频），通过@标签系统控制每个输入的角色：
- `@Image` → 风格/角色参考
- `@Video` → 运动/镜头参考  
- `@Audio` → 节奏/对白参考

### 7.2 对序话Story的启示

| Seedance 2.0做法 | 序话Story当前做法 | 未来可能的融合 |
|-----------------|-----------------|---------------|
| 单prompt描述多shot结构 | Stage 4逐shot生成prompt | Stage 4可生成"shot组"prompt，一次描述3-5个连续shot的完整镜头调度 |
| "lens switch"触发镜头切换 | 每个shot独立生成静态图 | 未来视频生成时，用shot组prompt作为视频模型的输入 |
| Character Lock | 参考图传递链 | 视频模型的character lock + 静态图的参考图传递，双重保障 |
| @标签引用系统 | IMAGE编号映射 + 图上标注 | @标签理念与我们的参考图标注方案异曲同工 |
| 音视频联合生成 | TTS + Whisper对齐 + 图片序列 | 未来可用视频模型的原生音视频同步替代当前的后期对齐流程 |

### 7.3 落地路径（Phase 7-8规划参考）

**Phase 7（首尾帧视频）**：用当前系统生成的shot静态图作为首帧/尾帧，输入Seedance 2.0或同类视频模型，生成shot内的微动效（呼吸、风吹、水面波动）。

**Phase 8（完整视频化）**：
1. Stage 4输出"shot组"prompt（包含多shot的镜头调度描述）
2. 用shot组prompt + 角色参考图 + 场景参考图，输入视频模型
3. 视频模型一次生成多shot的连续视频片段
4. 用TTS音频引导视频节奏（Seedance 2.0的@Audio模式）

**当前不实施的原因**：
- Seedance 2.0的全球API尚未完全开放，主要通过第三方平台有限访问
- 15秒最大时长限制，长故事需要拼接多段，连续性会降级
- 多角色复杂场景仍有约10%的失败率
- 成本模型尚不明确，无法进行ROI评估

**关注信号**（出现以下情况时重新评估）：
- Seedance 2.0 或同类模型开放稳定API + 合理定价
- 单次生成时长突破30秒
- 多角色一致性达到95%以上
- Google Flow整合Nano Banana 2的视频生成能力成熟
