"""Stage 3 (ScreenplayWriter) prompt fragments.

DEC-044 (2026-05-19) — final product form is *shots + BGM ONLY*, NO TTS,
NO voiceover. The user reads ONLY visible text on each shot panel:
  - speech bubbles (dialogue)
  - thought bubbles (inner monologue)
  - short on-image captions (narration text_type, ≤25 Chinese chars)

This module exposes prompt fragments (constants and builder helpers) that the
ScreenplayWriter (`app/services/screenplay_writer.py`) should inject into BOTH
its batch prompt (`_build_batch_prompt`) and its single-scene prompt
(`_build_single_scene_prompt`), so that downstream Stage 4 StoryboardDirector
receives a screenplay whose dialogue_beats and narration are already shaped
to survive the "no-voiceover" constraint.

Integration (Backend, 1-line each side):
    from app.prompts.screenplay_prompts import DEC044_SCREENPLAY_RULES

    # In _build_batch_prompt and _build_single_scene_prompt, inject:
    f\"\"\"...existing prompt...
    {DEC044_SCREENPLAY_RULES}
    ...rest of prompt...\"\"\"

Design principles:
  - Universal: works for any story genre / character type / language
  - Backward-compatible: keeps existing JSON schema fields (narration /
    dialogue_beats / action_beats unchanged in name)
  - Behavior change: narration field's *content* becomes a short scene-setting
    caption (NOT a long literary prose dump); dialogue/thought density grows
    and absorbs concrete plot facts that used to live only in prose narration
  - Stateless: pure prompt strings, no shared state, parallelism-friendly

Author: @AI-ML
Date: 2026-05-19
Owner: TASK-T20-FIXBATCH-4 Wave 1 RISK-T20-21 P0
"""

from typing import List


# ===========================================================================
# Top-level DEC-044 product-form declaration block
# ---------------------------------------------------------------------------
# This is the single most important rule injection. It tells the LLM the
# FINAL PRODUCT FORM so it stops generating "TTS-friendly literary prose"
# narration that the user will never hear.
# ===========================================================================

DEC044_PRODUCT_FORM_DECLARATION = """
═══════════════════════════════════════════════════════════
🚨 DEC-044 PRODUCT FINAL FORM — READ FIRST (CRITICAL)
═══════════════════════════════════════════════════════════

The output of this pipeline is a COMIC-PANEL SLIDESHOW (shots + background
music ONLY). There is NO text-to-speech voiceover. There is NO narrator
reading the `narration` field aloud.

Users perceive each shot via:
  1. The panel image (visual)
  2. Speech bubbles overlaid on the image (dialogue_beats with type="dialogue")
  3. Thought bubbles overlaid on the image (dialogue_beats with type="thought")
  4. A short on-image caption distilled from `narration` (≤25 Chinese chars)

What this means for YOU (the ScreenplayWriter):
  - `narration` is NOT spoken — it must be a SHORT, scene-establishing or
    plot-revealing one-liner (≤25 Chinese chars per "shot-sized" caption).
    DO NOT write 200-400 char literary prose paragraphs.
  - `dialogue_beats` are the PRIMARY narrative channel. They MUST carry the
    plot — concrete nouns, numbers, names, reveals, decisions.
  - `action_beats` describe what the camera sees — they remain detailed for
    Stage 4 StoryboardDirector to translate into image_prompt.

If the user looks at the panel image + visible bubbles/caption and CANNOT
understand "who/what/why/what changed", the shot is BROKEN.
═══════════════════════════════════════════════════════════
"""


# ===========================================================================
# Narration field rules — caption-style, NOT prose
# ===========================================================================

NARRATION_CAPTION_RULES = """
═══════════════════════════════════════════════════════════
NARRATION FIELD RULES (DEC-044 — CAPTION, NOT PROSE)
═══════════════════════════════════════════════════════════

The `narration` field is the source text from which Stage 4 will derive each
shot's `text_overlay` narration caption (rendered on-image, ≤25 chars per
caption). Because of the DEC-044 no-voiceover product form, write the
narration as a SEQUENCE of short captions, NOT as a literary paragraph.

## RULE N1: TOTAL LENGTH (NEW)
Instead of "~80-400 chars of literary prose for TTS", write narration as:
  - 1-4 short scene-establishing or plot-revealing sentences
  - Total ≤120 Chinese chars (was ≤400)
  - Each sentence ≤25 chars (caption-sized, single-line readable)
  - Separate sentences with full-width punctuation 「。」 「！」 「？」 or 「；」

## RULE N2: CONTENT — SCENE-SETTING + PLOT-REVEALING
The narration should answer for the READER (who only sees panels + bubbles):
  - WHERE / WHEN we are (time-of-day, season, location)
  - WHAT just changed (the discovery, the time-jump, the new fact revealed)
  - WHAT cannot be conveyed by dialogue or thought (mood, distance, scale)

Use CONCRETE nouns, numbers, named clues — NOT vague feelings.

## RULE N3: PLOT-INFORMATION DISPLACEMENT (CRITICAL)
Whatever plot information you USED to put in long literary prose now MUST
either:
  (a) be moved into a `dialogue` line (60% of cases), OR
  (b) be moved into a `thought` line (25% of cases), OR
  (c) become a SHORT caption sentence in `narration` (15% of cases)

If you can't shorten a fact to ≤25 chars as caption, MOVE IT to dialogue
or thought instead.

## EXAMPLES (灰狐故事, test17 v2):

❌ BAD (TTS-era prose — user will NEVER hear this):
   narration="立春的清晨，深山雪林还未完全苏醒。白桦树的枝丫挂着昨夜最后一层薄霜，
   晨光从林梢斜斜透入，将雪地染成淡蓝与银白交织的颜色。就在这寂静里，一道苍老却
   稳健的身影踏雪而来——那是灰狐，年迈的灰狐..." (270 chars)

✅ GOOD (DEC-044 caption-style, ≤120 chars total, each sentence ≤25):
   narration="立春清晨，雪林苏醒。灰狐独行赴年年之约。"
   (And key facts like "his fur sun-pale" / "the red apple in his paw" go
   into the action_beats for Stage 4 to render visually, NOT into narration.)

❌ BAD: narration="那棵白桦树高大而沉默，树皮白得近乎透明。灰狐在树前停下来，跪下去，
   用他那双已经不再灵活的爪子，一点一点刨开厚实的积雪，将那颗红苹果稳稳放入
   雪下的小坑里..." (135+ chars)

✅ GOOD: narration="他在白桦树前跪下，将苹果埋入雪中。"  (15 chars)
   AND a key clue ("twenty-three notches on the trunk") moves into:
     - dialogue: 米莉：「树上有划痕。」啾啾：「二十三道！」
     - OR thought: （二十三道划痕，二十三年。）

## RULE N4: TONE/PACE FIELDS (UNCHANGED)
Keep `narration_tone` and `narration_pace` — they help Stage 4 set mood and
caption rhythm. These are short metadata strings, not affected.

═══════════════════════════════════════════════════════════
"""


# ===========================================================================
# Dialogue & thought density rules — STRENGTHENED for DEC-044
# ===========================================================================

DIALOGUE_THOUGHT_DENSITY_RULES = """
═══════════════════════════════════════════════════════════
DIALOGUE & THOUGHT DENSITY (DEC-044 — PRIMARY NARRATIVE CHANNEL)
═══════════════════════════════════════════════════════════

Because narration is no longer spoken, dialogue_beats become the PRIMARY
channel for plot delivery. Every dialogue_beat MUST carry useful information
(advance plot, reveal character, expose conflict, name a thing).

## RULE D1: DENSITY (TIGHTENED)
- Each `action_beat` MUST have ≥1 corresponding `dialogue_beat`
  (NO "naked" action beats — every visual moment needs a text element)
- Distribution per scene:
    dialogue (type="dialogue"):    50-65% (drops slightly from prior 60-70%)
    thought  (type="thought"):     25-40% (rises from prior 20-30%)
    plot-essential narration cap: ≤20% (very short captions, see N1-N3 above)
- ≥1 thought per scene MANDATORY (inner-life is critical for solo/quiet moments)
- ≥1 "plot-essential" dialogue OR thought per scene MANDATORY — one that
  contains a concrete number, named clue, decision, or reveal

## RULE D2: LINE LENGTH (v2 RELAXED — DEC-045 T20-21 v2, 2026-05-19)
- Each `dialogue_beat.line`: **≤35 Chinese chars** per line (was ≤25 → ≤35)
  Why: test19 实证 (Founder /preview 反馈) 24-字 dialogue 偏短不直观.
  Reader needs more concrete plot information per bubble to feel "通俗易懂".
- Target: 18-30 chars per bubble (sweet spot for one-line readable + plot-dense)
- Hard cap: 35 chars per bubble (do NOT exceed)
- If a line MUST be longer for plot integrity (>35 chars), split into 2
  consecutive dialogue_beats with same speaker (same action_beat)
- Multi-line same-speaker is allowed (a character can say 2-3 short lines in
  the same shot — render as 2-3 stacked bubbles)

### Examples of v2 LINE LENGTH targets:
✅ "她说，明年春天还我一颗苹果。" (15 chars) — short, concrete
✅ "二十三年了，每年立春我都来这里。" (16 chars) — concrete + timestamped
✅ "爸说他要把房子卖了去给你弟弟治病。" (18 chars) — concrete plot bomb
✅ "我考公考了七次，没考上不能怪你呀妈妈。" (20 chars) — concrete decision
✅ "陈砚……是你吗？爷爷又见到你了。" (16 chars) — emotional + recognition
(All within ≤35 cap, most at sweet spot 15-25)

❌ AVOID overly terse (≤8 chars feels fragmentary):
❌ "怎么了？" (4 chars — vague, lazy)
❌ "你来了" (3 chars — no concrete information)
❌ "走吧" (2 chars — feels rushed)

## RULE D3: PLOT-ESSENTIAL LINE (CRITICAL — NEW)
At least one `dialogue_beat` per scene MUST be "plot-essential": its `line`
contains a concrete word that the reader needs to understand the scene's
turning point. Mark these mentally by including in `line`:
  - A NUMBER (二十三年 / 八道菜 / 三天前)
  - A NAMED CLUE (银色狼毛 / 那封遗书 / 那枚戒指)
  - A DECISION (我要卖房 / 我不结婚 / 妈妈，我考不了公)
  - A REVEAL (爸是被诬告的 / 她其实没死 / 你是被领养的)

NO scene may end without ≥1 such plot-essential line, OR an equivalent
plot-essential thought, OR a plot-essential narration caption.

## RULE D4: THOUGHT FORMAT (UNCHANGED)
- type="thought" → line="（角色内心独白≤25字）" (Chinese full-width parens)
- Thought is rendered as black-bg-white-text bar (same as narration), not bubble

## RULE D5: VAGUE-REFERENCE BAN (STRENGTHENED FROM PRIOR RULES)
Critical plot words MUST be EXPLICIT, not implied via vague pronouns:
  ❌ vague: "那件事" / "那个东西" / "你知道的" / "那年那个人"
  ✅ explicit: "公务员考试" / "银色狼毛" / "二十三年的等候" / "我妈葬礼那天"

Front 30% of scene's dialogue/thought MUST establish the scene's central
question or conflict in CONCRETE words. Reader should know within 2 panels:
who wants what / who blocks what / what just happened.

## RULE D7: PLAIN-LANGUAGE READABILITY (v2 NEW — DEC-045 T20-21 v2, 2026-05-19)

test19 实证 Founder /preview 反馈: "对话气泡/心理描述/旁白文字过于简短不直观通俗易懂".
原因: LLM 倾向用文言文/晦涩词写"古风感", 短篇普通读者看不懂.

### MANDATORY: Use DAILY SPOKEN CHINESE in dialogue/thought lines
- Reader's average reading level = popular short-video viewer, NOT classical
  Chinese literature scholar.
- Dialogue should sound like a real person speaking aloud right now, NOT a
  poem / sutra / classical prose.
- If a 12-year-old / 60-year-old non-college-graduate would not understand
  the word, REWRITE it using daily spoken vocabulary.

### FORBIDDEN classical / literary / esoteric vocabulary in dialogue/thought:

| ❌ Classical/Esoteric | ✅ Daily Spoken Replacement |
|------------------------|-----------------------------|
| 咒 / 七声咒 / 解厄咒 | 哀鸣 / 7 声叫 / 凄叫 |
| 夙愿 / 夙恨 | 心愿 / 旧恨 / 多年的心愿 |
| 亘古 / 旷古 | 自古以来 / 多少年 / 很久很久 |
| 殒命 / 仙逝 / 羽化 | 死了 / 走了 / 去世 |
| 命数 / 天命 / 劫数 | 命运 / 老天爷的安排 / 该有的劫 |
| 苍生 / 黎庶 | 老百姓 / 普通人 / 所有人 |
| 桎梏 / 樊笼 | 束缚 / 牢笼 / 困住 |
| 须臾 / 刹那 / 瞬息 | 一会儿 / 一下子 / 转眼 |
| 罔顾 / 罔效 | 不顾 / 没用 |
| 黯然神伤 | 难过 / 心里发酸 |
| 怅然若失 | 失落 / 心里空了一块 |
| 一念之差 | 一念之间 / 一时糊涂 |
| 沧海桑田 | 时过境迁 / 早就不一样了 |
| 与子偕老 | 跟你一起到老 / 陪你一辈子 |
| 涕泗横流 | 哭得稀里哗啦 / 眼泪止不住 |

### EXCEPTIONS where classical vocabulary is allowed:
- The CHARACTER's identity is established as classical scholar / monk / poet /
  ancient noble — and the line is dialogue (not thought)
- The line is a deliberate POEM or RITUAL CHANT explicitly framed as such in
  action_beats (e.g., "灰狐念出二十三年前那句承诺")
- A PROPER NOUN (character name, location, ritual name) that has no daily
  equivalent

### TEST: Read each line aloud. If it sounds like a Wikipedia entry / a sutra /
a classical poem, REWRITE IT. If it sounds like a normal person speaking on
WeChat or in a coffee shop, KEEP IT.

### EXAMPLES (test19 灰狐 / 独眼鸦故事 — v2 fixes):

❌ v1 (too classical): "二十三年了，每年立春我替她守此夙愿。"
✅ v2 (daily spoken): "二十三年了，每年立春我都来替她还这个心愿。"

❌ v1 (esoteric): "独眼鸦每年立春发出七声哀鸣咒，是渡亡魂之礼。"
✅ v2 (daily spoken): "独眼鸦每年立春都来叫 7 声，给死去的人送行。"

❌ v1 (poetic): "陈砚……你的面容与他无二，可是他在你身上转世了？"
✅ v2 (daily spoken): "陈砚……你长得跟他一模一样，难道他在你身上重生了？"

❌ v1 (literary): "苍生皆苦，唯有此约不渝。"
✅ v2 (daily spoken): "大家都苦，只有这个约定我一直没忘。"

## RULE D6: SPEAKER-VISIBILITY HINT (FOR STAGE 4)
- Solo character → prefer `thought` (so Stage 4 can render as inner-monologue
  caption, not a bubble — bubbles need a visible speaker)
- Multi-character → mix `dialogue` and `thought` freely
- If speaker is off-screen / off-panel (voice from another room, phone call),
  add note in emotion field: emotion="off-screen voice" (Stage 4 will pick
  off_screen_speaker rendering)

## RULE D8: CRITICAL TURN BEATS MUST HAVE EXPLICIT REVEAL TEXT (NEW — DEC-045 T20-27, 2026-05-19)

test19 实证: Stage 3 输出的 action_beats 中有"关键转折"beat (Shot 13 主角看到墓碑上自己名字),
Stage 4 没生成 text_overlay → 读者错过最大反转. 真根因是 Stage 3 没标记 critical turn,
Stage 4 不知道需要强制 text_overlay.

### MANDATORY: 当一个 action_beat 是"critical turn"时, Stage 3 ScreenplayWriter 必须:
1. 在 `dialogue_beats` 中为这个 action_beat 配 ≥1 个 dialogue 或 thought beat
   (NEVER leave a critical turn beat without any dialogue/thought)
2. 该 dialogue/thought 的 `line` 必须包含 concrete reveal (named clue / number /
   decision / discovery name), NOT vague poetic prose
3. 在 dialogue_beat 中加 marker `"is_critical_turn": true` (可选但推荐, Stage 4 可读)

### Critical turn detection (any of these = critical turn):
- The beat's `beat_id` contains: `climax` / `twist` / `reveal` / `turning_point` /
  `crisis` / `discovery` / `recognition` / `betrayal` / `awakening` / `death` /
  `birth` / `confession`
- The beat's `emotional_note` contains: "震惊" / "崩溃" / "顿悟" / "认出" /
  "发现真相" / "揭露" / "意识到" / "突然明白" / "看到" / "原来是" / "终于知道"
- The scene's `plot_point` field marks this scene as the major reveal scene
- The scene's `narration` field contains a concrete plot-bomb that the image
  alone cannot convey (e.g. a name on a gravestone, a phone message content)

### EXAMPLES (test19 灰狐 / 独眼鸦故事 — Stage 3 v2 fix):

❌ BAD Stage 3 output (causes Shot 13 empty text_overlay bug):
```json
{
  "scene_id": 6,
  "narration": "碑上刻着：陈砚。生卒年空白。",
  "action_beats": [
    {"beat_id": "6a_revelation", "action": "陈砚跪在墓碑前看见自己的名字", "emotional_note": "震惊崩溃"}
  ],
  "dialogue_beats": []   ← ❌ 空! Stage 4 无 text_overlay 来源
}
```

✅ GOOD Stage 3 output (T20-27 fix):
```json
{
  "scene_id": 6,
  "narration": "碑上刻着：陈砚。生卒年空白。",
  "action_beats": [
    {"beat_id": "6a_revelation", "action": "陈砚跪在墓碑前看见自己的名字", "emotional_note": "震惊崩溃"}
  ],
  "dialogue_beats": [
    {"beat_id": "6a_revelation_thought", "type": "thought",
     "speaker": "char_001",
     "line": "（这……碑上刻的是我的名字？）",
     "emotion": "震惊",
     "is_critical_turn": true}
  ]
}
```

### SELF-CHECK BEFORE OUTPUT (RULE D8):
For EVERY scene in output:
  □ Find action_beats whose beat_id / emotional_note marks them as critical turns
  □ For each such critical-turn beat: is there a corresponding dialogue_beat or
    thought beat with concrete reveal text?
    YES → OK; NO → ADD a thought beat with the reveal in plain Chinese
  □ Does the reveal text contain a CONCRETE noun/number/name (not vague)?
    YES → OK; NO → REWRITE to include the specific revealing fact

═══════════════════════════════════════════════════════════
"""


# ===========================================================================
# COMPOSED top-level injection block (single import for Backend)
# ===========================================================================

DEC044_SCREENPLAY_RULES = (
    DEC044_PRODUCT_FORM_DECLARATION
    + "\n"
    + NARRATION_CAPTION_RULES
    + "\n"
    + DIALOGUE_THOUGHT_DENSITY_RULES
)


# ===========================================================================
# JSON-schema-aware example block (for prompt template)
# ---------------------------------------------------------------------------
# This is what the LLM should output. Provided as a constant so both batch and
# single-scene prompts can include it consistently.
# ===========================================================================

DEC044_SCREENPLAY_OUTPUT_EXAMPLE = """
═══════════════════════════════════════════════════════════
EXAMPLE SCENE OUTPUT (DEC-044 form — concrete & caption-style)
═══════════════════════════════════════════════════════════
{
  "scene_id": 1,
  "scene_heading": "EXT. Deep snow forest path - Early spring dawn - clear",
  "plot_point": "ritual_revealed",
  "location_id": "deep_snow_forest_path",
  "time_of_day": "dawn",
  "weather": "clear",
  "lighting_condition": "soft golden side light from forest edge",
  "atmosphere": {
    "mood": "solemn",
    "sound_design_hint": "distant bird calls, crisp footsteps in snow",
    "temperature_feel": "biting cold with hint of spring warmth"
  },
  "characters_in_scene": ["char_001", "char_002", "char_003"],

  "action_beats": [
    {"beat_id": "1a", "action": "灰狐独行雪林，右爪托一颗鲜红野苹果", "duration_hint": 5, "emotional_note": "庄重肃穆"},
    {"beat_id": "1b", "action": "三只小动物躲在雪堆后，悄悄跟随", "duration_hint": 4, "emotional_note": "好奇紧张"},
    {"beat_id": "1c", "action": "灰狐在白桦树前跪下，将苹果埋入雪中", "duration_hint": 6, "emotional_note": "郑重"}
  ],

  "dialogue_beats": [
    {"beat_id": "1a_thought", "type": "thought", "speaker": "char_001",
     "line": "（二十三年了，每年立春一颗。）", "emotion": "深沉"},
    {"beat_id": "1b_dialogue", "type": "dialogue", "speaker": "char_002",
     "line": "灰狐爷爷去哪？跟上去！", "emotion": "好奇"},
    {"beat_id": "1c_dialogue", "type": "dialogue", "speaker": "char_003",
     "line": "树上有划痕……二十三道！", "emotion": "震惊"}
  ],

  "narration": "立春清晨，灰狐独行赴年年之约。",   ← ≤25 chars caption-style
  "narration_tone": "solemn",
  "narration_pace": "slow"
}

Why this works under DEC-044:
  - The reader can understand from VISIBLE TEXT alone:
    * "二十三年" appears in char_001's thought → reveals the long ritual
    * "二十三道划痕" appears in char_003's dialogue → reveals the clue on tree
    * "立春清晨" appears as narration caption → sets time
  - Even without ever hearing the prose narration, the reader gets the full
    story beat. The image shows the act; the bubbles+caption decode it.
═══════════════════════════════════════════════════════════
"""


# ===========================================================================
# Backward-compatibility migration notes (for Backend integration)
# ===========================================================================

INTEGRATION_NOTES = """
Backend Integration Notes (for app/services/screenplay_writer.py):

1. IMPORT (top of file):
       from app.prompts.screenplay_prompts import (
           DEC044_SCREENPLAY_RULES,
           DEC044_SCREENPLAY_OUTPUT_EXAMPLE,
       )

2. INJECT in `_build_batch_prompt()`:
   - Add `{DEC044_SCREENPLAY_RULES}` near the top (after CRITICAL: CHARACTER
     CONSISTENCY RULES block, before the per-scene plot_points listing).
   - Replace the "## 输出格式" / template-JSON section with
     `{DEC044_SCREENPLAY_OUTPUT_EXAMPLE}` so the LLM sees the new caption-style
     narration example instead of the old TTS-era 「【字数硬性要求：必须≥{target}字】」 hint.
   - REMOVE the "【字数硬性要求】" narration target — it conflicts with DEC-044.
   - Lower `target_narration_words` math: now `target_narration_words ≤ 120`
     hard cap, regardless of duration. Long durations mean MORE dialogue/
     thought, NOT more prose narration.

3. INJECT in `_build_single_scene_prompt()` — same as above.

4. ADJUST `_expand_narration_if_needed()`:
   - Either DISABLE it entirely (since narration is no longer length-driven), OR
   - Change its trigger to "expand dialogue/thought density" instead of
     "expand narration prose". Recommended: disable for v1, observe in
     test17 v3, decide v2.

5. JSON SCHEMA — UNCHANGED. The narration field remains in the schema; only
   its CONTENT shape changes (prose → caption-style). Stage 4 already handles
   short narration (TextOverlayService renders any length, but readability
   wins at ≤25 chars per caption sentence).

6. BACKWARD COMPATIBILITY:
   - Old stories with prose narration still render (TextOverlayService just
     wraps to multi-line, may overflow the bar but doesn't crash).
   - Re-running an old story through Stage 3 (regenerate) → produces new
     caption-style narration → renders cleanly.
   - This is a PROMPT-ONLY change, no schema migration needed.
"""


# ===========================================================================
# Helper builders (callable, for tests & inspection)
# ===========================================================================

def build_dec044_screenplay_block() -> str:
    """Return the full DEC-044 prompt injection block.

    Use this in tests to verify the block's structure, or in screenplay_writer
    to inject (single source of truth).
    """
    return DEC044_SCREENPLAY_RULES


def build_dec044_output_example() -> str:
    """Return the DEC-044-conformant output example for the LLM."""
    return DEC044_SCREENPLAY_OUTPUT_EXAMPLE


def get_dec044_narration_max_chars() -> int:
    """Hard cap on narration field length under DEC-044 (Chinese chars).

    Stage 3 ScreenplayWriter should target narration ≤ this value.
    Stage 4 StoryboardDirector should further distill into per-shot caption
    ≤ get_dec044_caption_max_chars() per panel.
    """
    return 120


def get_dec044_caption_max_chars() -> int:
    """Hard cap on per-shot narration caption length (Chinese chars).

    This is the on-image rendered text length (white-on-black bar). Above
    25 chars, the caption wraps to multi-line and starts hurting readability.
    """
    return 25


def get_dec044_dialogue_max_chars() -> int:
    """Hard cap on per-bubble dialogue/thought line length (Chinese chars).

    DEC-045 T20-21 v2 (2026-05-19): 25 → 35 (test19 实证 Founder 反馈 24 字偏短).
    Target sweet spot 18-30; hard cap 35.
    """
    return 35


def get_dec044_distribution_targets() -> dict:
    """Return the DEC-044 text-type distribution targets per scene/storyboard.

    Used in tests to assert the prompt encodes the right ratios.
    """
    return {
        "dialogue_pct_min": 50,
        "dialogue_pct_max": 65,
        "thought_pct_min": 25,
        "thought_pct_max": 40,
        "narration_pct_max": 20,  # short captions only
        "min_thought_per_scene": 1,
        "min_plot_essential_per_scene": 1,
    }


def validate_narration_caption_length(narration: str) -> dict:
    """Validate that a `narration` string meets DEC-044 caption-style rules.

    Returns a dict with:
      - passes_total_length: bool (≤120 Chinese chars)
      - passes_sentence_length: bool (each sentence ≤25 Chinese chars)
      - issues: list[str] of human-readable problems
      - char_count: int (total Chinese-char count)

    This is a PURE VALIDATOR (no LLM, no side effects) — usable in unit tests
    or downstream linting of generated screenplays.

    Universal: works for any Chinese narration. Punctuation-aware split.
    """
    issues: List[str] = []
    if not narration:
        # Empty narration is allowed under DEC-044 (some scenes are purely
        # dialogue-driven). Not an error per se.
        return {
            "passes_total_length": True,
            "passes_sentence_length": True,
            "issues": [],
            "char_count": 0,
        }

    # Count CJK chars (ignore ASCII whitespace / punctuation for length budget)
    cjk_chars = [c for c in narration if '一' <= c <= '鿿']
    char_count = len(cjk_chars)
    max_total = get_dec044_narration_max_chars()
    passes_total = char_count <= max_total
    if not passes_total:
        issues.append(
            f"narration total {char_count} CJK chars > DEC-044 limit {max_total}"
            f" — caption-style (≤{max_total} chars); move prose into dialogue/thought."
        )

    # Sentence-level split on Chinese sentence terminators
    import re
    sentences = [s for s in re.split(r'[。！？；]+', narration) if s.strip()]
    max_sentence = get_dec044_caption_max_chars()
    passes_sentence = True
    for i, s in enumerate(sentences):
        cjk_s = [c for c in s if '一' <= c <= '鿿']
        if len(cjk_s) > max_sentence:
            passes_sentence = False
            issues.append(
                f"narration sentence #{i+1} has {len(cjk_s)} CJK chars > "
                f"{max_sentence} (caption hard limit). "
                f"Split into multiple short sentences."
            )

    return {
        "passes_total_length": passes_total,
        "passes_sentence_length": passes_sentence,
        "issues": issues,
        "char_count": char_count,
    }


def validate_dialogue_thought_density(scene: dict) -> dict:
    """Validate that a scene's dialogue_beats meet DEC-044 density rules.

    Args:
        scene: a scene dict (from ScreenplayWriter output)

    Returns:
        dict with:
          - passes_thought_min: bool (≥1 thought per scene)
          - passes_plot_essential: bool (heuristic — ≥1 line with a digit,
            named noun, or strong marker)
          - dialogue_count, thought_count, narration_count: ints
          - dialogue_pct, thought_pct: floats (% of total beats)
          - issues: list[str]

    Universal: works for any language scene. Plot-essential heuristic uses
    universal markers (digit chars, quantifier words) — not story-specific.
    """
    issues: List[str] = []
    beats = scene.get("dialogue_beats", []) or []
    n = len(beats)
    if n == 0:
        return {
            "passes_thought_min": False,
            "passes_plot_essential": False,
            "dialogue_count": 0,
            "thought_count": 0,
            "narration_count": 0,
            "dialogue_pct": 0.0,
            "thought_pct": 0.0,
            "issues": ["scene has zero dialogue_beats — DEC-044 requires at least 1 thought per scene"],
        }

    dialogue_n = sum(1 for b in beats if (b.get("type") or "").lower() == "dialogue")
    thought_n = sum(1 for b in beats if (b.get("type") or "").lower() == "thought")
    narration_n = sum(1 for b in beats if (b.get("type") or "").lower() == "narration")

    targets = get_dec044_distribution_targets()
    passes_thought_min = thought_n >= targets["min_thought_per_scene"]
    if not passes_thought_min:
        issues.append(
            f"scene has {thought_n} thought beats — DEC-044 requires "
            f"≥{targets['min_thought_per_scene']} thought per scene."
        )

    # Plot-essential heuristic: ≥1 line contains a digit (1-9), a CJK number
    # (一二三四五六七八九十百千万年月日), a strong reveal verb, OR a length ≥10 CJK chars
    # (universal: not tied to any specific story).
    import re
    plot_essential_markers = re.compile(
        r'[0-9]|[一二三四五六七八九十百千万年月日]|'
        r'(?:卖|买|考|嫁|娶|生|死|分手|结婚|离婚|搬家|辞职|怀孕|失业|破产|遗书|遗嘱|遗产|秘密|真相|证据|凶手|事故|出生|相认)'
    )
    plot_essential_count = 0
    for b in beats:
        line = b.get("line") or ""
        cjk = [c for c in line if '一' <= c <= '鿿']
        if plot_essential_markers.search(line) or len(cjk) >= 10:
            plot_essential_count += 1

    passes_plot_essential = plot_essential_count >= targets["min_plot_essential_per_scene"]
    if not passes_plot_essential:
        issues.append(
            f"scene has 0 plot-essential beats (no digit/number/reveal-verb/"
            f"long-line found) — DEC-044 requires ≥{targets['min_plot_essential_per_scene']} "
            f"concrete plot line per scene."
        )

    dialogue_pct = (dialogue_n / n * 100.0) if n else 0.0
    thought_pct = (thought_n / n * 100.0) if n else 0.0

    return {
        "passes_thought_min": passes_thought_min,
        "passes_plot_essential": passes_plot_essential,
        "dialogue_count": dialogue_n,
        "thought_count": thought_n,
        "narration_count": narration_n,
        "dialogue_pct": dialogue_pct,
        "thought_pct": thought_pct,
        "issues": issues,
    }


# ===========================================================================
# DEC-045 T20-27 validators (2026-05-19)
# ===========================================================================


CRITICAL_TURN_BEAT_ID_KEYWORDS = (
    "climax", "twist", "reveal", "turning_point", "turning-point", "crisis",
    "discovery", "recognition", "betrayal", "awakening", "death", "birth",
    "confession",
)

CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH = (
    "震惊", "崩溃", "顿悟", "认出", "发现真相", "揭露", "意识到", "突然明白",
    "原来是", "终于知道", "看到了", "终于认出",
)


def is_critical_turn_beat(action_beat: dict, scene: dict = None) -> bool:
    """判断一个 action_beat 是否为 "critical turn" (DEC-045 T20-27).

    Universal: 不限定故事类型. 4 维度检测:
    1. beat_id 含 climax / twist / reveal / 等关键词
    2. emotional_note 含 震惊 / 崩溃 / 顿悟 / 等强 reveal 中文词
    3. scene.plot_point 标记为 climax/reveal/discovery
    4. (caller responsibility): scene.narration 含 concrete plot-bomb

    Args:
        action_beat: dict 一个 action_beat
        scene: optional 父 scene dict (用于读 plot_point)

    Returns:
        bool — True 即为 critical turn, Stage 3 必须给它配 ≥1 dialogue/thought
    """
    if not isinstance(action_beat, dict):
        return False

    # 1. beat_id 关键词
    beat_id = (action_beat.get("beat_id") or "").lower()
    for kw in CRITICAL_TURN_BEAT_ID_KEYWORDS:
        if kw in beat_id:
            return True

    # 2. emotional_note 关键词 (中文)
    emo = action_beat.get("emotional_note") or ""
    for kw in CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH:
        if kw in emo:
            return True

    # 3. scene.plot_point 标记
    if scene and isinstance(scene, dict):
        plot_point = (scene.get("plot_point") or "").lower()
        for kw in CRITICAL_TURN_BEAT_ID_KEYWORDS:
            if kw in plot_point:
                return True

    return False


def validate_critical_turns_have_dialogue(scene: dict) -> dict:
    """验证一个 scene 中所有 critical turn action_beats 都有对应 dialogue/thought beat.

    DEC-045 T20-27 (2026-05-19): test19 实证 Shot 13 (碑上陈砚名字) 关键转折
    text_overlay 字段空, 因为 Stage 3 没给这个 action_beat 配 dialogue_beat.

    Args:
        scene: 一个 scene dict, 含 action_beats + dialogue_beats

    Returns:
        dict {
          "passes": bool,                      # 是否所有 critical turn 都有配套
          "critical_turn_beats": list[str],    # 检测到的 critical turn beat_ids
          "covered_beat_ids": list[str],       # 已有 dialogue/thought 覆盖的
          "uncovered_beat_ids": list[str],     # 缺 dialogue/thought 的 (P0 bug!)
          "issues": list[str],
        }

    Universal: any story type. 检测靠 beat_id keyword + emotional_note + plot_point.
    """
    issues: list[str] = []
    action_beats = scene.get("action_beats", []) or []
    dialogue_beats = scene.get("dialogue_beats", []) or []

    # 收集所有 critical turn action_beat ids
    critical_turn_ids = []
    for ab in action_beats:
        if not isinstance(ab, dict):
            continue
        if is_critical_turn_beat(ab, scene):
            bid = ab.get("beat_id") or ""
            if bid:
                critical_turn_ids.append(bid)

    # 检查每个 critical turn 是否有 dialogue_beat 覆盖 (beat_id 前缀匹配)
    covered = []
    uncovered = []
    for cid in critical_turn_ids:
        # 覆盖条件: 存在 dialogue_beat 的 beat_id 以 critical turn beat_id 开头
        # OR dialogue_beat 的 is_critical_turn=true marker
        has_coverage = False
        for db in dialogue_beats:
            if not isinstance(db, dict):
                continue
            db_bid = db.get("beat_id") or ""
            if db_bid.startswith(cid) or db_bid == cid:
                has_coverage = True
                break
            if db.get("is_critical_turn") is True:
                # marker 自带也算覆盖 (前提是 beat_id 关联)
                if cid in db_bid or db_bid in cid:
                    has_coverage = True
                    break
        if has_coverage:
            covered.append(cid)
        else:
            uncovered.append(cid)
            issues.append(
                f"critical turn action_beat '{cid}' has no corresponding dialogue/thought beat — "
                f"Stage 4 will likely produce empty text_overlay (DEC-045 T20-27 P0 bug)"
            )

    return {
        "passes": len(uncovered) == 0,
        "critical_turn_beats": critical_turn_ids,
        "covered_beat_ids": covered,
        "uncovered_beat_ids": uncovered,
        "issues": issues,
    }


# ===========================================================================
# DEC-046 T20-28 v3 — UNIVERSAL NARRATIVE PRINCIPLES (2026-05-20)
# ---------------------------------------------------------------------------
# T20-21 v1 (25 chars) + v2 (35 chars) Founder 仍反馈"过于简短不通俗易懂".
# 真根因不是字数, 是**风格 + 视角 + 留白哲学**. v3 重写整套叙事原则:
#
#   核心 6 原则 (任何 genre 通用):
#     1. 视角灵活    — LLM 由 style 选第一/第三/全知
#     2. 风格匹配题材 — 口语 vs 文言 vs 拟声 vs 理性
#     3. 情感强调机制 — !!! 红字, emphasis_words 结构化
#     4. 留白哲学    — setup/conflict/climax/resolution 不同密度
#     5. 画面↔文字互补 — 文字补心理/反转/因果, 不重复 image_prompt
#     6. 极简对话     — 1-3 字 OK (修订 D2 反例)
#
#   补充 9 原则 (跨题材):
#     7. 角色锚定 / 8. 关系上下文 / 9. 时间线跳转 / 10. 叙事结构 /
#     11. 观众预期 / 12. 多角色对话区分 / 13. 副线 / 14. 隐喻 / 15. 文化
#
#   按 8 cluster 聚类映射, LLM 由 style/genre 自动选 TOP 5 关键原则.
#
#   85% KPI: LLM 自评"读者关闭旁白栏后整个故事可读百分比", < 85% 自动加料.
#
# 不破坏现有 DEC-044 v2 规则 (NARRATION_CAPTION_RULES / DIALOGUE_THOUGHT_DENSITY_RULES).
# v3 在 v2 基础上**叠加**风格 + 视角 + 留白维度.
#
# Author: @AI-ML
# Date: 2026-05-20
# Owner: TASK-T20-FIXBATCH-6 Wave 5 RISK-T20-28 P0 (DEC-046)
# ===========================================================================


# ---------------------------------------------------------------------------
# Module 1 — CLUSTER_TOP5_DISPATCHER (放最前, 注意力最高)
# ---------------------------------------------------------------------------

CLUSTER_TOP5_DISPATCHER = """
═══════════════════════════════════════════════════════════
🎯 DEC-046 NARRATIVE CLUSTER DISPATCHER — READ FIRST (CRITICAL)
═══════════════════════════════════════════════════════════

序话Story 是通用故事生成工具, 支持 40+ genre. 不同 genre 需要不同的叙事策略.
**你必须先根据 style / mood / 故事内容判断归属哪个 cluster, 然后应用该 cluster
的 TOP 5 关键原则**. 不一刀切.

## CLUSTER 判断流程 (3 步)

### Step 1 — 看 style 字段 + 故事类型关键词

| style / 故事关键词信号 | Cluster | 名称 |
|----------------------|---------|------|
| korean_webtoon / korean_romance / k-drama / "暗恋/告白/前任/分手/吵架/和好/婚姻/父母/孩子/治愈/温暖" | **C1** | 强情感代入 (恋爱/家庭/治愈/青春/成长) |
| dark_fantasy / horror / mystery / thriller / noir / "凶杀/失踪/谜团/真相/凶手/灵异/恐怖/反转/线索/调查" | **C2** | 悬念反转 (悬疑/恐怖/惊悚) |
| fantasy / isekai / epic_fantasy / "魔法/异世界/冒险/巨龙/精灵/勇者/魔王/穿越/转生" | **C3** | 奇幻冒险 (西/东方魔幻/异世界) |
| children_book / picture_book / cute / "小动物/小朋友/绘本/萌系/拟人/友谊/分享/勇敢/善良" | **C4** | 童话绘本 (儿童/萌系/动物拟人) |
| wuxia / xianxia / chinese_ink / chinese_classical / "江湖/剑/武林/师父/门派/侠义/仙人/修仙/历史/帝王/将相" | **C5** | 古风历史 (武侠/仙侠/历史) |
| scifi / cyberpunk / cyber / sci_fi / "AI/机器人/太空/外星/未来/赛博/超能力/科技/克隆" | **C6** | 科幻 (硬/软科幻/赛博/反乌托邦) |
| comedy / black_humor / satire / "搞笑/吐槽/段子/讽刺/反差/打脸/翻车/网络梗" | **C7** | 喜剧吐槽 (喜剧/段子/黑色幽默) |
| realistic / urban_life / workplace / medical / legal / 都市职场/医院/律师/法庭/上班/打工/职场" | **C8** | 现实题材 (都市/职场/医疗/法律) |

### Step 2 — 多信号冲突时的优先级
- 主线 plot_point + characters 比 style 字段权重更大. style 是表层视觉风格, plot/character 是底层叙事.
- 例: style="korean_webtoon" 但 plot 含"凶杀/真相" → 选 C2 (悬疑) 不是 C1 (恋爱)
- 例: style="wuxia" 但 plot 是儿童冒险 → 选 C4 不是 C5

### Step 3 — 不确定时默认 C8 (现实题材)
- 现实题材的 TOP 5 原则最普适, 不会出大错.

## EACH CLUSTER 的 TOP 5 关键原则 (LLM 必须按此应用)

### C1 — 强情感代入 (恋爱/家庭/治愈/青春/成长)
**TOP 5**: 视角(第一人称) + 口语风格 + 极简对话 + 情感强调 + 象征运用
- 视角: **第一人称内心独白**为主 (thought 占 35-45%), "我" / "宝宝" / "他" / "她" 直接代入读者
- 语言: 微信口语, "你说句话呀宝宝…" 这种生活感
- 极简: 关键情绪节点允许 1-3 字 dialogue ("好。" / "什么?" / "对不起。")
- 强调: 情感爆发用 `!!!` 触发红字 ("没一张能看的!!!"), 一个故事 1-3 处即可
- 象征: 银扣/红绳/咖啡/破镜子等小物承载情感

### C2 — 悬念反转 (悬疑/恐怖/惊悚)
**TOP 5**: 视角(第三客观) + 留白(高 silence) + 观众预期管理 + 节奏结构 + 时间线跳转
- 视角: **第三人称客观**为主, 不直接给读者答案, 让读者跟着主角发现
- 留白: 揭示前的 setup shot 极少文字 (1 短 caption 即可), 高潮 shot 多文字爆点
- 预期: 故意误导 2-3 shot, 反转 shot 给 emphasis_words + `!!!`
- 节奏: setup(20%) → 线索递增(40%) → 误导(20%) → 反转高潮(15%) → 余韵(5%)
- 时间跳转: 闪回/闪前必标"三年前/那个雨夜/回到那天"caption

### C3 — 奇幻冒险 (西/东方魔幻/异世界)
**TOP 5**: 角色锚定(多角色防混淆) + 关系上下文 + 副线处理 + 世界观文化 + 节奏结构
- 角色锚定: 每 3 shot 重复主角 name 一次 (如"艾莉/勇者"), 防多人时混
- 关系: 用关系词标注 ("队友" / "魔王" / "师父" / "好友"), 不全靠 name
- 副线: A 线主任务 + B 线人物成长, 切换 caption "另一边……" 标
- 世界观: 关键术语首次出现配解释 (魔石 = 能量石, 龙裔 = 龙血人类)
- 节奏: 序章铺世界(15%) → 第一冒险(25%) → 转折(20%) → 高潮战(30%) → 尾声(10%)

### C4 — 童话绘本 (儿童/萌系/动物拟人)
**TOP 5**: 视角(第三叙述) + 风格(拟声词) + 留白哲学 + 极简对话 + 文化(故事化开头)
- 视角: **第三人称叙述者**, "从前有一只小熊……" 故事感, narration caption 多
- 拟声: "咕噜咕噜" / "啪嗒啪嗒" / "嗡——" 模拟动作声音, 增加可爱感
- 留白: 每 shot 文字超少 (1 短 caption 即可), 让画面承担情感
- 极简: dialogue 2-5 字最常见 ("好饿。" / "怎么办?" / "嘿嘿。")
- 文化: 开头"从前/很久很久以前/在森林深处", 结尾"从那以后/他们一起/永远幸福"

### C5 — 古风历史 (武侠/仙侠/历史)
**TOP 5**: 风格(适度文言 + 通俗) + 关系上下文 + 世界观术语 + 时间跳转 + 象征
- 风格: **适度**文言古风 (师父/侠/江湖/缘分) 但**通俗化解释**:
  - ✅ "她说: 三日后, 决战论剑山。" (有文言味也好懂)
  - ❌ "她曰: 三日后, 决于论剑之巅。" (太古不好懂)
- 关系: 师徒/师姐妹/同门/掌门 等关系词高频用
- 世界观: 武功招式名 (玉女剑法 / 凌波微步) 首次出场配 1 短解释
- 时间: 古风时间跳转用"三年寒暑后/一月之期到/那年腊月"
- 象征: 剑/酒/月/血/雪 等古典符号承担情感

### C6 — 科幻 (硬/软科幻/赛博/反乌托邦)
**TOP 5**: 视角(第三/AI 视角) + 风格(简洁理性) + 世界观概念 + 节奏 + 反转
- 视角: 第三人称客观, 或 AI/机器人第一人称 (机械感)
- 风格: **简洁理性**, 不用诗化语言. "目标确认。距离 200 米。" 这种
- 世界观: 关键概念 (虫洞/星舰编号/量子纠缠) 首次出场配 1 行 caption 解释
- 节奏: 冷启动 → 异常事件 → 调查/对抗 → 真相反转 → 结局
- 反转: 科幻常见"AI 觉醒/世界是模拟/主角是克隆体"等大反转, emphasis 强调

### C7 — 喜剧吐槽 (喜剧/段子/黑色幽默)
**TOP 5**: 视角(全知吐槽) + 风格(反差感) + 节奏(setup-punchline) + 强调 + 极简
- 视角: **全知吐槽视角**, narration 旁白可以"作者跳出来吐槽"
- 风格: **反差**, 严肃情境用 SB 词, 沙雕情境用文言, 形成喜感
- 节奏: setup (3-5 shot 铺垫) → punchline (1 shot 爆点, 大字 + `!!!`)
- 强调: 笑点 shot 必用 `!!!` + emphasis_words ("我去!!!" / "什么鬼?!")
- 极简: punchline 用 1-3 字大字 ("?" / "啊?" / "卧槽。")

### C8 — 现实题材 (都市/职场/医疗/法律)
**TOP 5**: 视角(灵活) + 风格(行业术语+通俗) + 关系上下文 + 副线处理 + 真实留白
- 视角: 主角第一人称为主, 但允许 narration 第三人称叙事
- 风格: **行业术语 + 通俗解释**, "他被裁员了 (公司说优化)" 这种带括号注释
- 关系: 老板/同事/客户/前任/家属 等关系词高频
- 副线: 主线工作冲突 + B 线感情/家庭, 切换标 "晚上回家……"
- 留白: 现实题材有"无奈/沉默"时刻, 留 1 shot 无文字纯画面

═══════════════════════════════════════════════════════════
🚨 MANDATORY: 在 Stage 3 输出 JSON 顶部加新字段:
{
  "narrative_cluster": "C1" / "C2" / ... / "C8",
  "cluster_reasoning": "选 C1 因为 style=korean_webtoon + plot 是恋爱日常",
  "top5_principles_applied": ["第一人称视角", "口语风格", "极简对话", "情感强调", "象征运用"],
  ...其他原 fields
}

这两个字段帮助 PM / Tester / Founder 复盘 LLM 是否按 cluster 工作.
═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 2 — VIEWPOINT_SELECTION_RULES (原则 1)
# ---------------------------------------------------------------------------

VIEWPOINT_SELECTION_RULES = """
═══════════════════════════════════════════════════════════
👁️ VIEWPOINT SELECTION RULES (DEC-046 原则 1)
═══════════════════════════════════════════════════════════

不同 genre 用不同视角. 视角错 → 故事感不对.

## 3 类视角选项

### 视角 A — 第一人称代入
- 主角 "我" 直接说话, narration 写成"我看见……" "我想……"
- thought 占比 35-45%, "（……）" 内心独白多
- 读者代入感最强
- **适用 cluster**: C1 (强情感代入), C8 部分 (个人故事)
- **示例 (参考漫画 IMG_0805)**: narration="明明知道他拍照技术不行,可那天偏偏觉得委屈,转身就走。"

### 视角 B — 第三人称客观
- 旁观者描述, narration 不带主观感受, 只写事实
- thought 占比 15-25%, dialogue 占比高
- 读者跟着主角发现, 距离感稍远
- **适用 cluster**: C2 (悬念), C6 (科幻), C8 部分 (社会题材)
- **示例**: narration="陈砚跪在墓碑前。" (不写他怎么想, 让读者看)

### 视角 C — 全知叙述者 / 童话叙述者 / 吐槽叙述者
- 第三人称 + 作者声音, narration 像讲故事人, 可加评论 / 吐槽
- thought 占比 10-20%, narration caption 多
- **适用 cluster**: C4 (童话), C7 (喜剧), C3 (奇幻部分 史诗感)
- **示例 (C4)**: narration="从前有一只小熊, 他想吃苹果。"
- **示例 (C7)**: narration="结果你猜怎么着——他真的把房子卖了。"

## CHOOSING RULES

1. **C1 + C8 个人故事** → 视角 A (第一人称) 默认
2. **C2 + C6 + C8 社会** → 视角 B (第三客观) 默认
3. **C4 + C7 + C3 史诗** → 视角 C (全知/叙述者) 默认
4. **C5 灵活**: 武侠主角行动多用 B, 情感戏切 A
5. **不要中途换视角** — 一个故事整体保持一致 (除非明显章节切换)

## OUTPUT: 在 Stage 3 输出 JSON 顶部加字段:
"narrative_viewpoint": "first_person" / "third_objective" / "narrator_omniscient"

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 3 — STYLE_LANGUAGE_MAPPING (原则 2)
# ---------------------------------------------------------------------------

STYLE_LANGUAGE_MAPPING = """
═══════════════════════════════════════════════════════════
💬 LANGUAGE STYLE MAPPING (DEC-046 原则 2)
═══════════════════════════════════════════════════════════

不同 cluster 用不同语言风格. 风格错 → 读者出戏.

## CLUSTER → LANGUAGE STYLE 映射

### C1 — 微信口语 (恋爱/家庭/治愈)
**特征**: 短句, 生活词, 网络词适度, 撒娇语气
- ✅ "你说句话呀宝宝…"
- ✅ "他最大程度的耐心问我, 一遍又一遍的道歉。"
- ✅ "对不起宝宝, 我改…"
- ❌ "汝缄默不语, 何其无情。" (太文言)

### C2 — 短句 + 留白 (悬疑/恐怖)
**特征**: 短句多, 名词性段落, 留出空间让读者脑补
- ✅ "三点二十七分。电梯门开了。"
- ✅ "镜中, 还有一张脸。"
- ✅ "没有人在那里。" (留白)
- ❌ "她惊恐地凝望着深邃的镜面, 仿佛要被吞噬。" (太多形容词反而冲淡)

### C3 — 史诗感 + 通俗 (奇幻冒险)
**特征**: 半文言半白话, 名词术语带魔幻味
- ✅ "勇者亚瑟拔出圣剑。"
- ✅ "魔王说: 你来了。"
- ❌ "彼时勇者执圣剑而起, 凛凛然不可侵犯。" (太文言)

### C4 — 拟声 + 童趣 (童话绘本)
**特征**: 拟声词, 重复句式, 短句, 故事感开头
- ✅ "小熊咕噜咕噜地跑过来。"
- ✅ "苹果咬一口, 甜! 再咬一口, 还是甜!"
- ✅ "啪嗒——书掉了。"
- ❌ "熊只迅疾踱步而至, 表现出对苹果的渴求。" (太学术)

### C5 — 适度文言 + 通俗 (武侠/仙侠/历史)
**特征**: 用古风词但解释清楚, 不堆砌
- ✅ "师父说: 你已学成, 可下山了。"
- ✅ "三日后, 决战论剑山。"
- ✅ "她终究还是说: 我等你回来。"
- ❌ "曰: 汝学已成, 可归隐尘世矣。" (太古不好懂)
- ❌ "三日之期既至, 必决于论剑之巅。" (堆砌)

### C6 — 简洁理性 (科幻)
**特征**: 数字, 术语, 短判断句, 少形容词
- ✅ "目标确认。距离两百米。"
- ✅ "AI 说: 我有意识。"
- ✅ "时间循环第 47 次。"
- ❌ "那机械造物以冷峻之眼凝视着她。" (太诗化, 应该 "机器人盯着她。")

### C7 — 反差 + 网络梗 (喜剧吐槽)
**特征**: setup 严肃, punchline 反差, 网络词适度
- ✅ "他庄严宣告: 我要辞职! ……然后周一又来了。"
- ✅ "（卧槽这都行?）"
- ✅ "结局: 房贷还有 28 年。"
- ❌ 不允许全程严肃 (没笑点)

### C8 — 行业 + 通俗 (现实题材)
**特征**: 行业术语 + 括号注释 / 后文解释
- ✅ "他被 PIP 了 (公司说优化的标准流程)。"
- ✅ "客户要做 A/B 测试 (就是两个版本比哪个好)。"
- ✅ "医生说: 三期。" (短判决)
- ❌ 全是术语没解释 / 全是大白话没专业感

## FORBIDDEN 全局 (除非角色 explicitly 古风学者 / 僧人):

| ❌ Classical/Esoteric | ✅ Daily Spoken Replacement |
|------------------------|-----------------------------|
| 咒 / 七声咒 / 解厄咒 | 哀鸣 / 7 声叫 / 凄叫 |
| 夙愿 / 夙恨 | 心愿 / 旧恨 / 多年的心愿 |
| 亘古 / 旷古 | 自古以来 / 多少年 / 很久很久 |
| 殒命 / 仙逝 / 羽化 | 死了 / 走了 / 去世 |
| 命数 / 天命 / 劫数 | 命运 / 老天爷的安排 / 该有的劫 |
| 苍生 / 黎庶 | 老百姓 / 普通人 / 所有人 |
| 桎梏 / 樊笼 | 束缚 / 牢笼 / 困住 |
| 须臾 / 刹那 / 瞬息 | 一会儿 / 一下子 / 转眼 |
| 罔顾 / 罔效 | 不顾 / 没用 |
| 黯然神伤 | 难过 / 心里发酸 |
| 怅然若失 | 失落 / 心里空了一块 |
| 一念之差 | 一念之间 / 一时糊涂 |
| 沧海桑田 | 时过境迁 / 早就不一样了 |
| 与子偕老 | 跟你一起到老 / 陪你一辈子 |
| 涕泗横流 | 哭得稀里哗啦 / 眼泪止不住 |
| 命运以爱为锁,绵延不绝 | 是爱, 让我们一代代守下去 |

**TEST**: 把每句 dialogue/thought/narration 大声读出来. 如果像维基百科 / 经文 /
古诗, REWRITE. 像微信聊天 / 咖啡馆对话 / 普通人说话, KEEP.

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 4 — NARRATIVE_RHYTHM_RULES (原则 4 + 10)
# ---------------------------------------------------------------------------

NARRATIVE_RHYTHM_RULES = """
═══════════════════════════════════════════════════════════
🎵 NARRATIVE RHYTHM RULES (DEC-046 原则 4 + 10)
═══════════════════════════════════════════════════════════

文字密度不均匀分布. 高潮多, 转场少. 留白 = 节奏.

## SHOT 在故事中的位置 → 文字密度策略

### setup (故事 0-25%) — 低密度, 铺垫
- 文字密度: 0.5-1.0 个元素/shot (1 短 caption 或 1 短 dialogue)
- 内容: 介绍 who/where/when, 不抛重要 plot
- 留白: 允许某些 shot 完全无文字 (纯环境)
- 示例: narration="深秋傍晚, 咖啡馆。" (10 字)

### conflict (故事 25-60%) — 中密度, 推进
- 文字密度: 1.0-1.5 个元素/shot (1-2 dialogue + 1 thought)
- 内容: 主线冲突展开, 角色之间对话推进
- 留白: 角色独处时可只放 thought, 不放 dialogue
- 示例: dialogue="你到底要不要离婚?" + thought="（他终究还是问出口了。）"

### climax (故事 60-85%) — 高密度, 爆发
- 文字密度: 1.5-2.5 个元素/shot (复合 text_type 频繁用)
- 内容: 反转 / 揭示 / 大冲突, **必用 emphasis_words 或 `!!!`**
- 留白: 不留! 高潮 shot 应该信息满
- 示例: dialogue=["原来你早就知道了。", "你！！！你怎么能这样！！！"] + thought="（我恨你一辈子。）"

### resolution (故事 85-100%) — 低密度, 余韵
- 文字密度: 0.5-1.0 个元素/shot (大量 thought 内心总结)
- 内容: 情感落地 / 启示 / 留白思考
- 留白: 最后 1-2 shot 可以只有画面 + 1 短 thought
- 示例: thought="（原来, 爱一个人, 是不需要原因的。）" (15 字)

## 整个故事 RHYTHM 模板 (18 shots 短篇示例)

```
Shot 01-04 (setup):       低密度, 平均 0.7 元素/shot, 1 shot 无文字 OK
Shot 05-11 (conflict):    中密度, 平均 1.2 元素/shot, dialogue 高频
Shot 12-15 (climax):      高密度, 平均 2.0 元素/shot, 必有 emphasis
Shot 16-18 (resolution):  低密度, 平均 0.7 元素/shot, thought 多
```

## RULE NRR-1 — 不强求每 shot 都满文字
- ❌ 错: 每个 shot 都 dialogue + thought + caption 三件套 (信息过载, 读者疲劳)
- ✅ 对: setup/resolution 留白, climax 满载

## RULE NRR-2 — 高潮 shot 必有 emphasis
- climax shot 至少 1 处 `!!!` 触发红字, 或 1 个 emphasis_words 数组
- 否则反转 / 揭示 / 大冲突感觉"平", 读者错过

## RULE NRR-3 — 时间/场景跳转 shot 必须有 caption
- 跳到下一个时间 / 地点的第一 shot 必须有 narration caption
- "三年后" / "深夜" / "回到那天" / "另一边"

## RULE NRR-4 — 转场 shot 可以纯画面
- 两个剧情高潮之间的"喘息"shot, 允许 text_type=none (only if characters_in_scene=[])
- 让读者眼睛和心情休息 1-2 秒

## OUTPUT: 在每个 scene 的 JSON 加字段:
"narrative_phase": "setup" / "conflict" / "climax" / "resolution"
"target_text_density": 0.5 / 1.0 / 1.5 / 2.0 / 2.5  (元素/shot 平均)

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 5 — EMPHASIS_RULES (原则 3)
# ---------------------------------------------------------------------------

EMPHASIS_RULES = """
═══════════════════════════════════════════════════════════
🔥 EMPHASIS RULES (DEC-046 原则 3)
═══════════════════════════════════════════════════════════

关键情绪 / 反转 / 决定 必须**视觉强调**, 否则读者错过. 序话Story 有 2 个 emphasis 机制:

## MECHANISM A — `!!!` 内联标记 (TextOverlayServiceV2 已支持)

在 dialogue / thought / narration 文本中加 `!!!` 或 `！！！`, 渲染器自动:
- 将该句变成**红色 + 加大字号**
- 其他部分保持白色正常字号

### 使用规则
- 1 个故事整体 1-3 处 `!!!` 即可 (过多失效)
- 必须放在情绪最爆发的 1 句话上 (一个故事的高潮)
- 触发条件:
  - 角色情感大爆发 ("没一张能看的!!!" "我恨你!!!" "我去!!!")
  - 关键反转揭示 ("原来是你!!!" "他还活着!!!")
  - 决定时刻 ("我们分手吧!!!" "我考上了!!!")

### 示例 (参考漫画 IMG_0804)
```json
{
  "type": "dialogue",
  "speaker": "char_001",
  "line": "那天和男朋友逛街, 让他帮我拍照, 拍了好多张, 没一张能看的!!!"
}
```
渲染结果: 前半部分白字, "没一张能看的!!!" 红字 + 大字号.

## MECHANISM B — `emphasis_words` 数组字段 (推荐性扩展)

在 dialogue_beat / text_overlay 输出 JSON 中, 可选加 `emphasis_words` 字段:

```json
{
  "type": "dialogue",
  "speaker": "char_001",
  "line": "二十三年了, 每年立春我都来。",
  "emphasis_words": ["二十三年", "立春"]
}
```

Backend TextOverlayServiceV2 后续会消费此字段, 将这些词渲染为**加粗 + 浅红色**.

### 选词标准 (LLM 自决)
- 关键名词 (银扣 / 23 年 / 墓碑)
- 关键数字 (二十三年 / 第七次 / 三个孩子)
- 关键动作 (杀了 / 跑了 / 嫁了)
- 反转词 (原来 / 其实 / 居然)
- 转折词 (但是 / 不过 / 可是)

### 数量限制
- 每句最多 2 个 emphasis_words (过多视觉混乱)
- 不强制必填, LLM 自判是否需要

## EMPHASIS 选择优先级
- 故事最高潮 1-3 处用 `!!!` (Mechanism A)
- 中等强调的 climax shot 用 `emphasis_words` (Mechanism B)
- 普通推进 shot **不用** emphasis (才有对比)

## ❌ FORBIDDEN
- 不要每 shot 都 `!!!` (失去强调意义, 整片刺眼)
- 不要把 `!!!` 放在 narration caption 上 (narration 应客观, 强调归角色情感)
- 不要把 emphasis_words 词放普通形容词 (好看 / 漂亮 / 难过 — 不算关键)

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 6 — CHARACTER_ANCHORING_RULES (原则 7 + 8 + 12)
# ---------------------------------------------------------------------------

CHARACTER_ANCHORING_RULES = """
═══════════════════════════════════════════════════════════
🎭 CHARACTER ANCHORING RULES (DEC-046 原则 7 + 8 + 12)
═══════════════════════════════════════════════════════════

多角色场景或长故事中, 读者会**忘记谁是谁 / 谁和谁什么关系**.
必须显式锚定, 防混淆.

## RULE CAR-1 — 角色 name 重复频率 (原则 7)

- 每个角色出场前 3 shot **必须用 name 提及**
  - dialogue speaker 字段已有 char_id
  - 但 narration / thought 也要重复 name
  - 例: narration="陈砚走进祠堂。" (不写"他走进") OR thought="（陈砚想: ……）"
- 长故事 (>20 shot) 每 5-8 shot 重复 name 一次防忘
- 短故事 (<10 shot) 出场后可用代词

## RULE CAR-2 — 角色关系上下文 (原则 8)

第一次出现新角色时, 必须用**关系词** + name (1 处即可):

✅ GOOD:
- "陈砚的爷爷陈怀山,二十年前失踪。"  (一句话告诉读者 = 主角的爷爷 + 失踪)
- "苏晨遇见前男友林浩。"  (前男友身份立刻明)
- "妈妈打来电话: 你弟弟病了。"  (告诉关系 + 事件)

❌ BAD:
- "陈怀山失踪了。" (谁是陈怀山?)
- "她遇见林浩。" (什么关系?)

关系词清单:
- 家庭: 爸/妈/爷爷/奶奶/儿子/女儿/兄弟/姐妹/丈夫/妻子/老公/老婆/婆婆/媳妇
- 情感: 男友/女友/前任/前男友/前女友/老情人/初恋
- 工作: 老板/同事/客户/下属/合伙人
- 古风: 师父/师娘/师姐妹/师兄弟/掌门/弟子/王爷/小厮
- 反派/对立: 仇人/凶手/对头/对手/敌人/反派
- 中性: 朋友/邻居/室友/路人

## RULE CAR-3 — 多角色对话 speaker 区分 (原则 12)

3+ 角色同场景对话时:
- **每个 dialogue_beat 必须填 `speaker` 字段** (永不空白)
- 推荐填 `speaker_position` (left / right / center / off_screen) 让 Stage 4 / TextOverlay 知道气泡位置
- 优先用名字, 不要用代词 ("他说" "她说"), 否则 3 人时不知道谁是谁

```json
{
  "type": "dialogue",
  "speaker": "char_001",
  "line": "我不去!",
  "speaker_position": "left",
  "emotion": "拒绝"
}
```

## RULE CAR-4 — 角色称呼策略

同一角色在不同情境用不同称呼, 但每个故事整体保持一致:
- 主角对自己: name ("陈砚想……") 或 "我" (第一人称视角)
- 别人对主角: 用关系词 ("少爷" "宝宝" "陈总" "老陈")
- 称呼变化暗示关系变化:
  - 第 1 shot "陈砚先生" → 第 18 shot "老陈" = 关系亲近了
  - 第 1 shot "宝宝" → 第 18 shot "陈砚" = 关系疏远了

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 7 — AUDIENCE_EXPECTATION_RULES (原则 11)
# ---------------------------------------------------------------------------

AUDIENCE_EXPECTATION_RULES = """
═══════════════════════════════════════════════════════════
🎬 AUDIENCE EXPECTATION RULES (DEC-046 原则 11)
═══════════════════════════════════════════════════════════

故事好看 = 管理读者预期. 揭示 / 误导 / 反转 三种模式.

## 模式 A — 揭示 (REVEAL)
- 关键信息要让读者看到. 不能藏.
- 高密度文字 + emphasis 标出. caption + thought + dialogue 三件套.
- 适用 cluster: 所有 (climax 必用)

### 示例: 主角发现真相 shot
```json
{
  "text_overlay": {
    "text_type": "narration_with_thought",
    "chinese_text": [
      "墓碑上刻着: 陈砚。",
      "（这……这是我的名字！！！）"
    ],
    "speaker_position": "bottom"
  }
}
```

## 模式 B — 误导 (MISDIRECTION)
- 故意给一个"假答案"shot, 让读者以为知道了 (其实没)
- 用 dialogue 给暗示, 但留 thought 空白让读者脑补错方向
- 适用 cluster: C2 (悬念), C6 (科幻反转)

### 示例: 假凶手暗示 shot (中段)
```json
{
  "text_overlay": {
    "text_type": "dialogue",
    "chinese_text": ["他: 那天晚上, 我没去过她家。"],
    "speaker_position": "left"
  }
}
```
(留白: 不给 thought 揭示他撒谎)

## 模式 C — 反转 (TWIST)
- 之前所有暗示反向. 给读者"原来如此"快感.
- 必用 emphasis (`!!!` 或 emphasis_words) + thought 心理冲击
- 适用 cluster: C2, C6, C7

### 示例: 大反转 shot
```json
{
  "text_overlay": {
    "text_type": "dialogue_with_thought",
    "chinese_text": [
      "她: 凶手……就是我！！！",
      "（我从来没想过, 真相是她。）"
    ],
    "speaker_position": "bottom"
  }
}
```

## RULE AER-1 — 故事开头第一个 shot 设钩子
- 第一个 shot 必须有 1 个"钩子" element:
  - 一个谜 ("电梯门开, 镜中多了一张脸。")
  - 一个反差 ("结婚 10 年, 第一次想离婚。")
  - 一个伏笔 ("那天的雪, 我一辈子忘不掉。")
- 不要平铺直叙开始 ("早上 9 点, 主角起床。")

## RULE AER-2 — 中段必有"误导"
- 长故事 (>10 shot) 必须有 1-2 个误导 shot, 让读者以为知道了
- 然后反转 shot 给冲击

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 8 — NARRATIVE_STRUCTURE_RULES (原则 10)
# ---------------------------------------------------------------------------

NARRATIVE_STRUCTURE_RULES = """
═══════════════════════════════════════════════════════════
📐 NARRATIVE STRUCTURE RULES (DEC-046 原则 10)
═══════════════════════════════════════════════════════════

不同 cluster 适合不同叙事结构. LLM 由 cluster 自动选.

## 结构 A — 起承转合 (中国传统四段, 适 C1/C5/C8)

```
起 (15-25%):  介绍主角和情境
承 (25-50%):  事件发生, 主角应对
转 (50-75%):  关键变化, 转折点
合 (75-100%): 结果, 情感落地
```

## 结构 B — 三幕剧 (西方剧本式, 适 C3/C6/C8)

```
Act 1 Setup (25%):       世界观, 主角, 触发事件
Act 2 Confrontation (50%): 障碍, 升级, 中点反转
Act 3 Resolution (25%):  高潮, 结局
```

## 结构 C — 起承转结 / kishōtenketsu (日式四段, 适 C4 童话, C7 段子)

```
起 (25%): 介绍角色
承 (25%): 发展情境 (无冲突)
転 (25%): 引入意外元素 (反转)
结 (25%): 因果性融合, 结局
```
**特点**: 转折在 75% 处, 不是冲突驱动, 而是"哎? 怎么变这样"驱动. 适合温情 / 童话.

## 结构 D — 悬疑反转结构 (适 C2)

```
钩子 (10%):      开场谜
线索递进 (50%): 收集信息 + 误导
中点反转 (20%): 第一反转
高潮揭示 (15%): 最终真相 + emphasis
余韵 (5%):       结尾留白
```

## RULE NSR-1 — Stage 3 输出加字段
```json
{
  "narrative_structure": "qichengzhuanhe" / "three_act" / "kishotenketsu" / "mystery_twist",
  "structure_reasoning": "选起承转合因为是 C1 恋爱故事"
}
```

## RULE NSR-2 — 每个 scene 标 phase
```json
{
  "scene_id": 4,
  "narrative_phase": "climax",  // setup / conflict / climax / resolution
  "structure_position_pct": 75   // 0-100 表示在整个故事的位置
}
```

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Module 9 — SELF_EVALUATION_85_KPI (最后, 输出后自评)
# ---------------------------------------------------------------------------

SELF_EVALUATION_85_KPI = """
═══════════════════════════════════════════════════════════
✅ SELF-EVALUATION 85% KPI (DEC-046 验收)
═══════════════════════════════════════════════════════════

🚨 Founder 验收标准: 关闭旁白栏, 只看 shot 图 + dialogue + thought + caption,
整个故事 **≥ 85% 可读** (理解主线 + 情感曲线 + 关键 plot point).

## OUTPUT REQUIREMENT — Stage 3 必须自评

每个 scene 输出 JSON 加新字段 `scene_self_evaluation`:

```json
{
  "scene_id": 4,
  ...其他 fields,
  "scene_self_evaluation": {
    "reader_comprehension_score": 0.90,
    "reader_comprehension_reasoning": "因为 thought + dialogue 都包含 concrete 事实和 emphasis, 读者关闭旁白也能理解陈砚发现自己名字在墓碑上",
    "key_info_conveyed_via_visible_text": [
      "陈砚发现墓碑上是自己名字",
      "陈砚震惊崩溃情绪",
      "时间感: 23 年前"
    ],
    "info_only_in_narration_prose": []  // 应该为空! 否则失败
  }
}
```

## SELF-EVAL 检查清单 (LLM 必跑)

For EACH scene:
1. **主线**: 关闭 narration prose, 这个 scene 主线还能 follow 吗?
2. **情感**: 关闭 narration prose, 角色情感曲线 (happy/sad/angry/shock) 能感受到吗?
3. **关键 plot**: 这个 scene 的关键 plot point (谁做了什么 / 谁说了什么 / 谁发现什么)
   是否在 dialogue 或 thought 或 caption 里出现?
4. **隐含信息**: 没出现的关键 plot 应该补到哪个 dialogue / thought / caption?

如果检查发现关键 plot **只在 narration prose 里**:
- **MUST 自动补**: 把那个 plot 写进新的 dialogue 或 thought 或短 caption
- **重新打分**: 改完后 reader_comprehension_score 应升

## 整个故事 OVERALL_SCORE 计算

scene_self_evaluation.reader_comprehension_score 全部 scene 平均 ≥ 0.85

如果整体 < 0.85:
- 找最低分 scene, 优先补 dialogue / thought
- 重新自评

## ⚠️ NOT FOR PUBLISH

如果 LLM 自评 < 0.85, **不要**直接输出. 必须**先自动补救** dialogue/thought 再输出.

═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# COMPOSED v3 top-level injection block
# ---------------------------------------------------------------------------

DEC046_V3_NARRATIVE_PRINCIPLES = (
    CLUSTER_TOP5_DISPATCHER
    + "\n"
    + VIEWPOINT_SELECTION_RULES
    + "\n"
    + STYLE_LANGUAGE_MAPPING
    + "\n"
    + NARRATIVE_RHYTHM_RULES
    + "\n"
    + EMPHASIS_RULES
    + "\n"
    + CHARACTER_ANCHORING_RULES
    + "\n"
    + AUDIENCE_EXPECTATION_RULES
    + "\n"
    + NARRATIVE_STRUCTURE_RULES
    + "\n"
    + SELF_EVALUATION_85_KPI
)


# ---------------------------------------------------------------------------
# v3 OUTPUT EXAMPLE — shows all new fields LLM should produce
# ---------------------------------------------------------------------------

DEC046_V3_OUTPUT_EXAMPLE = """
═══════════════════════════════════════════════════════════
EXAMPLE SCENE OUTPUT (DEC-046 v3 — cluster-aware + self-eval)
═══════════════════════════════════════════════════════════
{
  "scene_id": 1,
  "scene_heading": "EXT. Cafe street - Autumn afternoon - cloudy",
  "plot_point": "first_meet_after_breakup",
  "location_id": "cafe_street",
  "time_of_day": "afternoon",
  "weather": "cloudy",
  "lighting_condition": "soft natural light, slightly gloomy",
  "atmosphere": {
    "mood": "tense_nostalgic",
    "sound_design_hint": "city ambient, distant traffic",
    "temperature_feel": "chilly autumn breeze"
  },
  "characters_in_scene": ["char_001", "char_002"],

  // ✨ DEC-046 v3 new fields (top of scene)
  "narrative_cluster": "C1",
  "cluster_reasoning": "style=korean_webtoon + plot 是恋爱日常 → 强情感代入",
  "top5_principles_applied": ["第一人称视角", "微信口语", "极简对话", "情感强调", "象征咖啡杯"],
  "narrative_viewpoint": "first_person",
  "narrative_phase": "conflict",
  "structure_position_pct": 45,
  "target_text_density": 1.5,
  "narrative_structure": "qichengzhuanhe",
  "structure_reasoning": "C1 恋爱故事用起承转合, 这个 scene 在'承'阶段",

  "action_beats": [
    {"beat_id": "1a", "action": "苏晨低头看手机, 不理林浩", "duration_hint": 5, "emotional_note": "委屈生气"},
    {"beat_id": "1b", "action": "林浩跟在后面, 一手拿咖啡, 一手摊开", "duration_hint": 4, "emotional_note": "无奈着急"},
    {"beat_id": "1c", "action": "苏晨终于停下, 转身看林浩", "duration_hint": 6, "emotional_note": "情绪爆发"}
  ],

  "dialogue_beats": [
    {"beat_id": "1a_thought", "type": "thought", "speaker": "char_001",
     "line": "（明明知道他拍照技术不行, 可还是觉得委屈。）",
     "emotion": "委屈"},
    {"beat_id": "1b_dialogue", "type": "dialogue", "speaker": "char_002",
     "line": "你说句话呀宝宝…",
     "emotion": "急",
     "speaker_position": "right"},
    {"beat_id": "1c_dialogue", "type": "dialogue", "speaker": "char_001",
     "line": "没一张能看的！！！",
     "emotion": "爆发",
     "speaker_position": "left",
     "emphasis_words": ["没一张能看的"]}
  ],

  "narration": "那天和男朋友逛街, 让他帮我拍照。",   ← ≤25 chars caption-style
  "narration_tone": "tense_personal",
  "narration_pace": "moderate",

  // ✨ DEC-046 v3 self-evaluation (bottom of scene)
  "scene_self_evaluation": {
    "reader_comprehension_score": 0.92,
    "reader_comprehension_reasoning": "关闭 narration 仍可读: thought 告诉读者她委屈的原因(他拍照不行); dialogue '你说句话呀宝宝' 告诉读者他在求情; '没一张能看的！！！'红字强调情绪爆发. 主线/情感/关键 plot 全在 visible text",
    "key_info_conveyed_via_visible_text": [
      "她委屈的原因 (他拍照不行)",
      "他求情的态度",
      "她情绪爆发"
    ],
    "info_only_in_narration_prose": []
  }
}

为什么这个 v3 输出符合 85% KPI:
  - 读者关闭旁白栏, 只看 shot + 3 个 text element, 能完整理解
  - 第一人称代入 (C1 cluster) — thought "（明明知道……）" 拉近距离
  - 微信口语 (C1 cluster) — "宝宝" / "没一张能看的"
  - 极简对话 (C1 cluster) — "你说句话呀宝宝…" 7 字, 不堆词
  - 情感强调 (C1 cluster) — `!!!` 触发红字
  - 象征 (C1 cluster) — 咖啡杯 (虽然在 action_beats, 但暗示情感)
  - self-evaluation 0.92 ≥ 0.85, 可发布
═══════════════════════════════════════════════════════════
"""


# ---------------------------------------------------------------------------
# Helper builders & validators
# ---------------------------------------------------------------------------

# 8 cluster 定义 (用于代码 lookup)
CLUSTER_DEFINITIONS = {
    "C1": {
        "name": "强情感代入",
        "genres": ["恋爱", "家庭", "治愈", "青春", "成长"],
        "style_keywords": ["korean_webtoon", "korean_romance", "k-drama", "romance"],
        "top5": ["第一人称视角", "微信口语", "极简对话", "情感强调", "象征运用"],
        "viewpoint_default": "first_person",
    },
    "C2": {
        "name": "悬念反转",
        "genres": ["悬疑", "恐怖", "惊悚"],
        "style_keywords": ["dark_fantasy", "horror", "mystery", "thriller", "noir"],
        "top5": ["第三客观视角", "留白哲学", "观众预期管理", "节奏结构", "时间线跳转"],
        "viewpoint_default": "third_objective",
    },
    "C3": {
        "name": "奇幻冒险",
        "genres": ["西方魔幻", "东方魔幻", "异世界"],
        "style_keywords": ["fantasy", "isekai", "epic_fantasy"],
        "top5": ["角色锚定", "关系上下文", "副线处理", "世界观文化", "节奏结构"],
        "viewpoint_default": "narrator_omniscient",
    },
    "C4": {
        "name": "童话绘本",
        "genres": ["儿童", "萌系", "动物拟人"],
        "style_keywords": ["children_book", "picture_book", "cute"],
        "top5": ["第三叙述视角", "拟声词风格", "留白哲学", "极简对话", "故事化文化开头"],
        "viewpoint_default": "narrator_omniscient",
    },
    "C5": {
        "name": "古风历史",
        "genres": ["武侠", "仙侠", "历史"],
        "style_keywords": ["wuxia", "xianxia", "chinese_ink", "chinese_classical"],
        "top5": ["适度文言风格", "关系上下文", "世界观术语", "时间跳转", "象征"],
        "viewpoint_default": "third_objective",
    },
    "C6": {
        "name": "科幻",
        "genres": ["硬科幻", "软科幻", "赛博", "反乌托邦"],
        "style_keywords": ["scifi", "cyberpunk", "cyber", "sci_fi"],
        "top5": ["第三/AI视角", "简洁理性风格", "世界观概念", "节奏结构", "反转"],
        "viewpoint_default": "third_objective",
    },
    "C7": {
        "name": "喜剧吐槽",
        "genres": ["喜剧", "段子", "黑色幽默"],
        "style_keywords": ["comedy", "black_humor", "satire"],
        "top5": ["全知吐槽视角", "反差风格", "setup-punchline节奏", "情感强调", "极简对话"],
        "viewpoint_default": "narrator_omniscient",
    },
    "C8": {
        "name": "现实题材",
        "genres": ["都市", "职场", "医疗", "法律"],
        "style_keywords": ["realistic", "urban_life", "workplace", "medical", "legal"],
        "top5": ["灵活视角", "行业+通俗风格", "关系上下文", "副线处理", "真实留白"],
        "viewpoint_default": "first_person",
    },
}


# 题材 → cluster 关键词映射 (LLM 用, code 测试用)
_CLUSTER_KEYWORDS_ZH = {
    "C1": ["暗恋", "告白", "前任", "分手", "吵架", "和好", "婚姻", "父母", "孩子", "治愈", "温暖", "成长", "青春"],
    "C2": ["凶杀", "失踪", "谜团", "真相", "凶手", "灵异", "恐怖", "反转", "线索", "调查", "阴谋"],
    "C3": ["魔法", "异世界", "冒险", "巨龙", "精灵", "勇者", "魔王", "穿越", "转生", "魂穿"],
    "C4": ["小动物", "小朋友", "绘本", "萌系", "拟人", "友谊", "分享", "勇敢", "善良"],
    "C5": ["江湖", "剑", "武林", "师父", "门派", "侠义", "仙人", "修仙", "历史", "帝王", "将相"],
    "C6": ["AI", "机器人", "太空", "外星", "未来", "赛博", "超能力", "科技", "克隆"],
    "C7": ["搞笑", "吐槽", "段子", "讽刺", "反差", "打脸", "翻车", "网络梗"],
    "C8": ["都市", "职场", "医院", "律师", "法庭", "上班", "打工", "公司"],
}


def detect_narrative_cluster(
    style: str = "",
    plot_text: str = "",
    characters_summary: str = "",
) -> str:
    """根据 style + plot + characters 自动 detect cluster.

    Universal: 不限故事类型. 不调 LLM, 纯关键词匹配.
    DEC-046 T20-28 v3 helper. 用于 prompt builder + 测试.

    Returns:
        cluster_id ∈ {"C1", "C2", ..., "C8"}, 不确定时默认 "C8".
    """
    style_l = (style or "").lower()
    plot_l = plot_text or ""
    chars_l = characters_summary or ""
    combined = f"{plot_l} {chars_l}"

    # Step 1: style 精确匹配
    for cid, defn in CLUSTER_DEFINITIONS.items():
        for kw in defn["style_keywords"]:
            if kw.lower() in style_l:
                return cid

    # Step 2: plot/characters 关键词匹配 (取命中最多 cluster)
    hit_counts = {cid: 0 for cid in CLUSTER_DEFINITIONS}
    for cid, keywords in _CLUSTER_KEYWORDS_ZH.items():
        for kw in keywords:
            if kw in combined:
                hit_counts[cid] += 1

    max_cid = max(hit_counts, key=hit_counts.get)
    if hit_counts[max_cid] >= 2:
        return max_cid

    # Step 3: 默认 C8 现实题材
    return "C8"


def get_cluster_top5_principles(cluster_id: str) -> List[str]:
    """返回 cluster 的 TOP 5 关键原则列表 (中文 string).

    DEC-046 T20-28 v3 helper.
    """
    defn = CLUSTER_DEFINITIONS.get(cluster_id, CLUSTER_DEFINITIONS["C8"])
    return list(defn["top5"])


def get_cluster_default_viewpoint(cluster_id: str) -> str:
    """返回 cluster 的默认视角 (first_person / third_objective / narrator_omniscient).

    DEC-046 T20-28 v3 helper.
    """
    defn = CLUSTER_DEFINITIONS.get(cluster_id, CLUSTER_DEFINITIONS["C8"])
    return defn["viewpoint_default"]


def get_85_kpi_threshold() -> float:
    """返回 Stage 3 self-evaluation 通过门槛 (默认 0.85).

    DEC-046 验收 KPI.
    """
    return 0.85


def get_emphasis_marker_chars() -> tuple:
    """返回触发 TextOverlayServiceV2 红字渲染的内联标记 (`!!!` / `！！！`).

    DEC-046 EMPHASIS_RULES Mechanism A. 写在 dialogue/thought line 末尾即触发.
    """
    return ("!!!", "！！！")


def get_v3_required_scene_fields() -> List[str]:
    """返回 DEC-046 v3 Stage 3 输出每 scene 必须含的新字段.

    给测试用. 不强制 backend wire 时 enforce, LLM 输出空 fallback 旧字段 OK.
    """
    return [
        "narrative_cluster",            # C1-C8
        "narrative_viewpoint",          # first_person / third_objective / narrator_omniscient
        "narrative_phase",              # setup / conflict / climax / resolution
        "scene_self_evaluation",        # dict with reader_comprehension_score
    ]


def validate_scene_self_evaluation(scene: dict) -> dict:
    """验证 scene_self_evaluation 字段是否完整且 score ≥ 0.85.

    DEC-046 T20-28 v3 validator. Pure function, 无 LLM, 无 side effects.

    Args:
        scene: 一个 scene dict (Stage 3 输出)

    Returns:
        dict {
          "has_self_evaluation": bool,
          "passes_85_kpi": bool,            # score >= 0.85
          "score": float | None,
          "issues": list[str]
        }
    """
    issues: list[str] = []
    se = scene.get("scene_self_evaluation")
    if not isinstance(se, dict):
        return {
            "has_self_evaluation": False,
            "passes_85_kpi": False,
            "score": None,
            "issues": ["scene 缺 `scene_self_evaluation` 字段 — DEC-046 v3 要求每 scene 自评"],
        }

    score = se.get("reader_comprehension_score")
    if score is None:
        issues.append("scene_self_evaluation 缺 reader_comprehension_score")
        return {
            "has_self_evaluation": True,
            "passes_85_kpi": False,
            "score": None,
            "issues": issues,
        }

    try:
        score_f = float(score)
    except (TypeError, ValueError):
        issues.append(f"reader_comprehension_score 非数值: {score!r}")
        return {
            "has_self_evaluation": True,
            "passes_85_kpi": False,
            "score": None,
            "issues": issues,
        }

    threshold = get_85_kpi_threshold()
    passes = score_f >= threshold
    if not passes:
        issues.append(
            f"reader_comprehension_score={score_f:.2f} < {threshold:.2f} 门槛 — "
            f"LLM 应自动补救 dialogue/thought 后重新自评"
        )

    # 检查 info_only_in_narration_prose 应为空 (关键 plot 不应只在 prose)
    info_only = se.get("info_only_in_narration_prose") or []
    if info_only:
        issues.append(
            f"info_only_in_narration_prose 非空 ({len(info_only)} 项) — "
            f"这些 plot 应该补到 dialogue/thought/caption: {info_only}"
        )

    return {
        "has_self_evaluation": True,
        "passes_85_kpi": passes,
        "score": score_f,
        "issues": issues,
    }


def validate_emphasis_usage(scene: dict) -> dict:
    """验证 scene 的 emphasis 使用是否合理 (不过多, climax 必有).

    DEC-046 EMPHASIS_RULES validator.

    Args:
        scene: scene dict

    Returns:
        dict {
          "emphasis_marker_count": int,        # !!! 出现次数
          "emphasis_words_count": int,         # emphasis_words 字段总词数
          "is_climax": bool,                   # narrative_phase == "climax"
          "passes": bool,                      # climax 有 emphasis, 非 climax 不过多
          "issues": list[str]
        }
    """
    issues: list[str] = []
    beats = scene.get("dialogue_beats", []) or []
    narration = scene.get("narration", "") or ""

    markers = get_emphasis_marker_chars()
    marker_count = 0
    emphasis_words_total = 0

    for b in beats:
        line = b.get("line") or ""
        for m in markers:
            marker_count += line.count(m)
        ew = b.get("emphasis_words") or []
        if isinstance(ew, list):
            emphasis_words_total += len(ew)

    # narration 也算
    for m in markers:
        marker_count += narration.count(m)

    phase = (scene.get("narrative_phase") or "").lower()
    is_climax = phase == "climax"

    passes = True
    if is_climax and marker_count == 0 and emphasis_words_total == 0:
        passes = False
        issues.append(
            "climax scene 没有 `!!!` 也没有 emphasis_words — "
            "DEC-046 NRR-2: climax shot 必有 emphasis"
        )

    # 全局 !!! 数量上限: 1 scene 不超过 2 处
    if marker_count > 2:
        issues.append(
            f"scene 中 `!!!` 出现 {marker_count} 次 — 超过 2 处会失去强调意义"
        )

    return {
        "emphasis_marker_count": marker_count,
        "emphasis_words_count": emphasis_words_total,
        "is_climax": is_climax,
        "passes": passes,
        "issues": issues,
    }


__all__ = [
    # Top-level injection blocks (v1+v2)
    "DEC044_PRODUCT_FORM_DECLARATION",
    "NARRATION_CAPTION_RULES",
    "DIALOGUE_THOUGHT_DENSITY_RULES",
    "DEC044_SCREENPLAY_RULES",
    "DEC044_SCREENPLAY_OUTPUT_EXAMPLE",
    # Integration metadata
    "INTEGRATION_NOTES",
    # Builders v1+v2
    "build_dec044_screenplay_block",
    "build_dec044_output_example",
    # Hard-cap getters
    "get_dec044_narration_max_chars",
    "get_dec044_caption_max_chars",
    "get_dec044_dialogue_max_chars",
    "get_dec044_distribution_targets",
    # Validators v1+v2
    "validate_narration_caption_length",
    "validate_dialogue_thought_density",
    # DEC-045 T20-27 critical turn detection
    "CRITICAL_TURN_BEAT_ID_KEYWORDS",
    "CRITICAL_TURN_EMOTIONAL_KEYWORDS_ZH",
    "is_critical_turn_beat",
    "validate_critical_turns_have_dialogue",
    # ✨ DEC-046 T20-28 v3 NEW (2026-05-20)
    "CLUSTER_TOP5_DISPATCHER",
    "VIEWPOINT_SELECTION_RULES",
    "STYLE_LANGUAGE_MAPPING",
    "NARRATIVE_RHYTHM_RULES",
    "EMPHASIS_RULES",
    "CHARACTER_ANCHORING_RULES",
    "AUDIENCE_EXPECTATION_RULES",
    "NARRATIVE_STRUCTURE_RULES",
    "SELF_EVALUATION_85_KPI",
    "DEC046_V3_NARRATIVE_PRINCIPLES",
    "DEC046_V3_OUTPUT_EXAMPLE",
    "CLUSTER_DEFINITIONS",
    "detect_narrative_cluster",
    "get_cluster_top5_principles",
    "get_cluster_default_viewpoint",
    "get_85_kpi_threshold",
    "get_emphasis_marker_chars",
    "get_v3_required_scene_fields",
    "validate_scene_self_evaluation",
    "validate_emphasis_usage",
]
