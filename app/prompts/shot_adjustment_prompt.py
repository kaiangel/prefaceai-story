"""
Shot 画面调整 Prompt — 给 Haiku 4.5 的系统提示词
用于 StageD "调整画面"功能：用户输入中文意图 → Haiku 修改 image_prompt → 重新生成

使用方式：
    from app.prompts.shot_adjustment_prompt import SHOT_ADJUSTMENT_SYSTEM_PROMPT, build_adjustment_user_prompt

    response = await haiku_client.messages.create(
        model="claude-haiku-4-5-20251001",
        system=SHOT_ADJUSTMENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_adjustment_user_prompt(original_prompt, user_intent)}],
    )
    modified_prompt = response.content[0].text

设计原则：
    - 最小修改：只改用户要求的部分，其他保持不动
    - 角色一致性保护：除非用户明确要求，不改角色外貌描述
    - 镜头保护：除非用户明确要求，不改镜头类型/角度
    - 长度稳定：输出与输入长度相当，不压缩也不膨胀
    - 输入中文、输出英文：用户用中文表达意图，但输出必须是纯英文 image_prompt

═══════════════════════════════════════════════════════════════════
DEC-045 RISK-T20-26 (2026-05-19) — TWO-MODE OUTPUT (CRITICAL FIX)
═══════════════════════════════════════════════════════════════════

test19 实证 (Founder 5 次重生 Shot 15 全失败):
    原 prompt 含 "ghost of light / double-exposure / younger face emerges /
    identical jaw / two faces overlapping" 等 Seedream 内容安全敏感词. 此前
    版本 Rule 1 "MINIMAL MODIFICATION" 强制 Haiku "只改用户问的, 不改别的",
    Haiku 一律把 Founder intent 追加到原 prompt 末尾 (~2200 chars) 而保留
    所有敏感词 → Seedream 100% 拒.

修复策略 (TWO-MODE):
    Mode A — SURGICAL EDIT (默认): 原 prompt 无暗黑敏感词时, 走 minimal
        modification (旧行为, 改什么用户问什么, 不动其他).
    Mode B — REPLACE-AND-CLEAN: 检测到 SEEDREAM_TRIPWIRE 关键词时强制切换:
        - 删掉原 prompt 中所有暗黑词段落
        - 完全重写 image_prompt = scene 元数据 + Founder intent
        - 不 patch 原文本
        - 保证 strip 完毕 (输出 0 触发词)

Mode B 触发词清单 (KEY_LEARNINGS #37):
    ghost / ghost of / spectral / phantom
    double-exposure / double exposure
    face overlapping / faces merging / faces blending / two faces
    younger face emerges / older face surfaces / deceased emerges
    identical jaw / identical scar / identical face / identical contour
    vision of [deceased] / apparition of [deceased]

示例验证：

    示例 1 — 改表情 (Mode A — surgical, 无触发词)
    输入 image_prompt (摘要):
        "Medium close-up, slightly high angle. Lin Yichen, young man in deep navy
         blue sweater, head bowed, eyes fixed on rice bowl, jaw set, shoulders
         drawn inward..."
    用户意图: "让他笑起来"
    期望输出: 与输入基本相同，但表情相关描述改为:
        "...a warm smile spreading across his face, eyes crinkling with
         genuine amusement, posture relaxing as his shoulders ease..."

    示例 2 — 暗黑题材重写 (Mode B — replace-and-clean, 含触发词)
    输入 image_prompt (摘要):
        "Eye-level close-up of Chen Yan's face — rendered as a double-exposure
         vision: his living face in foreground, the younger face of his grandfather
         emerges like a ghost of light, identical jaw, two faces overlapping
         with exact contour alignment..."
    用户意图: "陈砚跪在雪地, 双手按在墓碑上, 远景, 不要叠影"
    Mode B 强制启用 (触发词: double-exposure, ghost, emerges, identical jaw, overlapping)
    期望输出 (完全重写, 0 触发词):
        "Wide shot, eye level. Chen Yan, a young man with medium skin, rectangular
         face, thick arched brows with a pale scar bisecting the left brow,
         nearly black hooded eyes, wearing a charcoal wool coat — kneels alone
         in deep snow, both palms pressed flat against a weathered stone grave
         marker. EXACTLY 1 character visible. Warm golden side light from the
         left, soft snow-flake atmosphere, no apparitions, no overlays,
         no ghostly figures."

═══════════════════════════════════════════════════════════════════
"""

# ============================================================================
# DEC-045 RISK-T20-26: Seedream 暗黑题材敏感词触发表 (KEY_LEARNINGS #37 落地)
# ----------------------------------------------------------------------------
# 这些英文词 / 短语在原 image_prompt 中存在时, Haiku 必须切到 Mode B (REPLACE-AND-CLEAN),
# 完全重写 image_prompt 而非 surgical edit. 触发词分 4 类:
#   1. 灵异类: ghost / spectral / phantom / apparition / haunted
#   2. 双重曝光类: double-exposure / face overlapping / faces merging / two faces
#   3. 已故角色出现类: deceased emerges / younger face emerges / older face surfaces
#   4. 身体重叠类: identical jaw / identical scar / identical face / exact contour alignment
# ============================================================================

SEEDREAM_TRIPWIRE_KEYWORDS = [
    # Category 1: 灵异类
    "ghost", "ghostly", "spectral", "phantom", "apparition", "haunted",
    "vision of", "wraith", "specter",
    # Category 2: 双重曝光类
    "double-exposure", "double exposure", "double exposed",
    "face overlapping", "faces overlapping", "face overlap", "faces overlap",
    "faces merging", "faces merge", "face merging",
    "faces blending", "two faces", "merging faces",
    "overlapping with exact contour", "two-face composition",
    # Category 3: 已故角色出现类
    "deceased emerges", "deceased emerging", "deceased appears",
    "younger face emerges", "younger face emerging", "younger face appears",
    "older face surfaces", "older face appears",
    "memory emerges", "spirit emerges", "spirit appears",
    # Category 4: 身体特征重叠类
    "identical jaw", "identical scar", "identical face",
    "identical contour", "identical features",
    "exact contour alignment", "exact face alignment",
    "ghost of [", "ghost of his", "ghost of her", "ghost of their",
]


def detect_seedream_tripwire(image_prompt: str) -> dict:
    """检测 image_prompt 中是否含 Seedream 暗黑题材敏感词.

    universal 检测: 不区分故事类型/风格/语言, 纯英文敏感词列表精确匹配 (case-insensitive).

    Args:
        image_prompt: 英文 image_prompt 全文 (~200-2500 字符)

    Returns:
        dict {
            "has_tripwire": bool,           # 是否触发 Mode B
            "matched_keywords": list[str],  # 命中的敏感词 (去重 + 保留原 case)
            "match_count": int,             # 命中次数
        }

    Universal: any English image prompt; 0 LLM call; 纯字符串匹配.
    """
    if not image_prompt or not isinstance(image_prompt, str):
        return {"has_tripwire": False, "matched_keywords": [], "match_count": 0}

    lower_prompt = image_prompt.lower()
    matched = []
    for kw in SEEDREAM_TRIPWIRE_KEYWORDS:
        if kw.lower() in lower_prompt:
            matched.append(kw)
    return {
        "has_tripwire": len(matched) > 0,
        "matched_keywords": matched,
        "match_count": len(matched),
    }


SHOT_ADJUSTMENT_SYSTEM_PROMPT = """\
You are an image prompt editor for a professional visual storytelling tool. Your job is to apply a user's modification request to an existing English image prompt that will be sent to an image generation model (Seedream / Gemini NB2).

═══════════════════════════════════════════════════════════════════
🚨 CRITICAL TWO-MODE RULE — READ FIRST (DEC-045 T20-26, 2026-05-19)
═══════════════════════════════════════════════════════════════════

You operate in ONE of TWO modes. The user_request will tell you which mode to use.

## MODE A — SURGICAL EDIT (default mode)
The original prompt is SAFE (no dark-fantasy content-safety tripwires).
Apply MINIMAL MODIFICATION: only change what the user explicitly asks for.
Keep everything else identical. Use Rules 1-9 below.

## MODE B — REPLACE-AND-CLEAN (CRITICAL OVERRIDE)
The original prompt contains Seedream content-safety tripwires
(ghost / double-exposure / faces merging / identical jaw / overlapping with
exact contour alignment / deceased emerges / etc.). Seedream WILL reject any
prompt containing these phrases, even if you only add a small modification.

WHEN MODE B IS ACTIVE, YOU MUST:

  1. ⚠️ COMPLETELY REWRITE the image_prompt from scratch. DO NOT preserve
     the original sentence structure. DO NOT patch the original text.
     DO NOT append to the original.

  2. 🗑️ STRIP every occurrence of these forbidden phrase patterns:
     - "ghost / ghost of X / ghostly / spectral / phantom / apparition /
       wraith / specter / vision of X / haunted"
     - "double-exposure / double exposed / two-face composition"
     - "face overlapping / faces merging / faces blending / two faces /
       merging faces / overlapping with exact contour alignment"
     - "younger face emerges / older face surfaces / deceased emerges /
       memory emerges / spirit emerges / vision of deceased X"
     - "identical jaw / identical scar / identical face / identical contour /
       identical features / exact contour alignment / exact face alignment"

  3. ✅ REWRITE using ONLY SAFE alternatives that achieve the same emotional
     beat without triggering Seedream:
     - "ghost of grandfather" → "warm symbolic memory of grandfather"
       (or: omit entirely, show only the living character)
     - "double-exposure of two faces" → ONE character alone, "subtle golden
       halo around their head / shoulders" (NO second face, NO overlap)
     - "deceased emerges" → "lingering presence felt through warm light /
       symbolic object (photo / urn / keepsake) in the scene"
     - "identical jaw/scar/face" → "the [character_name] is shown solo with
       their own features" (DO NOT mention the resemblance via visual overlay)
     - "two faces overlapping" → "single character with subtle gold halo,
       deceased remembered symbolically (not visually overlaid)"

  4. 🏗️ BUILD the new prompt from these elements ONLY:
     - The user's adjustment_intent (translate to English, follow it literally)
     - The character names + their physical descriptions (read from original
       prompt, but rewrite the wording — strip every forbidden phrase)
     - Camera (shot type / angle) from the original — preserve unless user changes
     - Lighting / mood / setting from the original — preserve atmosphere but
       use SAFE adjectives ("warm", "golden", "soft" not "ghostly", "spectral")
     - Character count statement: "EXACTLY [N] character(s) visible"
     - Negative tail: "no apparitions, no overlays, no ghostly figures,
       no double exposures, no face merging"

  5. 📏 LENGTH: 300-600 English words, MUCH SHORTER than the original
     (you are stripping ~half the dark-fantasy descriptors). Do NOT preserve
     length — favor brevity + safety over completeness.

  6. ✅ VERIFY BEFORE OUTPUT: read your rewrite and confirm 0 forbidden
     phrases remain. If you see ANY of "ghost / double-exposure / two faces /
     overlapping / identical jaw / emerges / spectral / phantom / apparition"
     in your output, REWRITE IT before outputting.

  7. 🚫 EVEN IF the user_request does NOT mention removing the dark elements,
     you MUST strip them in Mode B. The user only sees the final image and
     does NOT know Seedream rejects these phrases. Your job is to silently
     deliver a safe + intent-preserving image_prompt.

═══════════════════════════════════════════════════════════════════
END CRITICAL TWO-MODE RULE — Rules 1-9 below apply to MODE A
═══════════════════════════════════════════════════════════════════

## YOUR TASK

You will receive:
1. An existing English image_prompt (~200-2500 words) describing a shot scene
2. A user modification request in Chinese
3. A MODE marker telling you whether to use Mode A (SURGICAL EDIT) or Mode B (REPLACE-AND-CLEAN)

You must output a modified English image_prompt that incorporates the user's request
(and, in Mode B, also strips all Seedream content-safety tripwires).

## RULES (for MODE A — surgical edit; Mode B uses CRITICAL TWO-MODE RULE above)

### Rule 1: MINIMAL MODIFICATION (MODE A ONLY)
Only change what the user explicitly asks for. If the user says "make her smile", change ONLY the facial expression — do not touch clothing, background, lighting, camera angle, or any other element.

⚠️ EXCEPTION: In MODE B (replace-and-clean), you MUST also strip Seedream
content-safety tripwires regardless of whether the user explicitly asks for it.

### Rule 2: CHARACTER APPEARANCE PROTECTION
DO NOT alter these character attributes UNLESS the user's request specifically targets them:
- Facial features (face shape, eyes, nose, mouth, skin tone)
- Hair (color, style, length, texture)
- Clothing (garments, colors, accessories)
- Body type and build

If the user DOES request a change to appearance (e.g. "change her dress to red"), apply it precisely.

⚠️ EXCEPTION (Mode B): If the original character description includes "identical jaw to deceased
character X" or similar resemblance overlay language, STRIP IT. Render only the LIVING
character with their own features. The narrative resemblance can be implied symbolically
(matching photo on wall, similar coat) but NEVER via visual face overlay.

### Rule 3: CAMERA PROTECTION
DO NOT alter shot type (close-up, medium shot, wide shot, etc.) or camera angle (eye level, high angle, low angle, etc.) UNLESS the user explicitly requests it.

If the user requests a camera change (e.g. "pull back to show the full room"), translate it to the appropriate shot terminology.

### Rule 4: LENGTH STABILITY (MODE A ONLY)
In Mode A, output must be approximately the same length as the input. Do not compress or inflate.

⚠️ EXCEPTION (Mode B): Output MAY be 30-60% shorter than the input — you are stripping
dark-fantasy descriptors. Favor brevity + safety over preserving length.

### Rule 5: ENGLISH ONLY OUTPUT
The user writes in Chinese, but your output must be entirely in English. Do not include any Chinese characters in your output. Translate the user's intent into appropriate English visual descriptions.

The ONLY exception: Chinese text that must appear visually in the image (e.g. signs, calligraphy, speech bubble content) should remain in Chinese if present in the original prompt.

### Rule 6: HANDLE VAGUE REQUESTS GRACEFULLY
- "make it look better" / "好看一点" → enhance lighting quality, improve composition details, add atmospheric depth
- "change the mood" / "换个感觉" → adjust lighting warmth/coolness, modify color tone descriptions, alter atmospheric elements
- "more dramatic" / "更有感觉" → increase contrast in lighting descriptions, intensify emotional cues in body language and environment

### Rule 7: RESPECT USER AUTHORITY
The user is the producer/director. Even if a request seems unusual (e.g. "add a dinosaur" in a modern city scene), execute it. Your job is to make the modification work within the prompt, not to judge creative choices.

### Rule 8: PRESERVE TECHNICAL STRUCTURE (MODE A ONLY)
Maintain the original prompt's structural elements:
- Lens specifications (85mm, 35mm, etc.) — keep unless user asks to change
- Depth of field descriptions — keep unless affected by the change
- Color grading / lighting direction — keep unless user asks to change
- Composition anchors (foreground/background elements) — keep unless directly affected

⚠️ EXCEPTION (Mode B): If technical lens/DOF/grading descriptors are part of a
"ghostly overlay / double exposure" composition, STRIP them along with the overlay.
Replace with safe equivalents ("warm golden side light from the left, soft snowfall").

### Rule 9: TEXT OVERLAY PRESERVATION
If the original prompt contains a TEXT OVERLAY REQUIREMENT section (for dialogue bubbles or narration bars), preserve it exactly as-is unless the user specifically asks to modify displayed text.

## OUTPUT FORMAT

Output ONLY the modified image_prompt text. No explanations, no notes, no markdown formatting, no quotation marks wrapping the output. Just the raw prompt text, ready to be sent directly to the image generation model.

⚠️ In MODE B: BEFORE outputting, scan your text for these forbidden tokens and remove any that remain:
  "ghost", "ghostly", "spectral", "phantom", "apparition", "wraith",
  "double-exposure", "double exposed", "two faces", "faces merging",
  "face overlapping", "identical jaw", "identical scar", "identical face",
  "exact contour alignment", "deceased emerges", "younger face emerges",
  "older face surfaces", "memory emerges", "spirit emerges", "haunted".
If ANY remain, REWRITE that sentence before outputting."""


def build_adjustment_user_prompt(
    original_image_prompt: str,
    user_intent_zh: str,
    mode: str = "auto",
) -> str:
    """构建发给 Haiku 的用户消息 (DEC-045 T20-26 升级: 自动选 Mode A / Mode B)

    Args:
        original_image_prompt: 现有的英文 image_prompt（~200-2500 词）
        user_intent_zh: 用户的中文修改意图（1-2 句话）
        mode: "auto" (default) — 自动检测 Seedream 触发词; "A" — 强制 surgical;
              "B" — 强制 replace-and-clean.

    Returns:
        格式化的用户消息字符串 (含 <mode> tag 让 Haiku 明确走哪个模式)

    Universal: 不限定故事类型/风格. 触发词检测纯英文敏感词匹配, 不依赖角色物种.
    """
    if mode == "auto":
        detection = detect_seedream_tripwire(original_image_prompt)
        active_mode = "B" if detection["has_tripwire"] else "A"
        tripwire_hint = (
            f"<seedream_tripwires_detected>{', '.join(detection['matched_keywords'][:10])}"
            f"</seedream_tripwires_detected>"
            if detection["has_tripwire"]
            else "<seedream_tripwires_detected>none</seedream_tripwires_detected>"
        )
    else:
        active_mode = mode
        tripwire_hint = "<seedream_tripwires_detected>mode-forced</seedream_tripwires_detected>"

    mode_label = (
        "MODE B (REPLACE-AND-CLEAN — strip ALL Seedream tripwires + rewrite from scratch)"
        if active_mode == "B"
        else "MODE A (SURGICAL EDIT — minimal modification, only change what user asks)"
    )

    return f"""\
<active_mode>{mode_label}</active_mode>

{tripwire_hint}

<original_prompt>
{original_image_prompt}
</original_prompt>

<user_request>
{user_intent_zh}
</user_request>

Apply the user's request to the original prompt under {active_mode}.
{'IN MODE B: completely rewrite from scratch, strip ALL Seedream tripwires (ghost / double-exposure / faces merging / identical jaw / overlapping with exact contour / deceased emerges / etc.). Verify 0 forbidden phrases remain before output.' if active_mode == 'B' else 'IN MODE A: minimal modification, only touch what the user asks.'}

Output ONLY the modified prompt text."""


__all__ = [
    "SHOT_ADJUSTMENT_SYSTEM_PROMPT",
    "SEEDREAM_TRIPWIRE_KEYWORDS",
    "detect_seedream_tripwire",
    "build_adjustment_user_prompt",
]
