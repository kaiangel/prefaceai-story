"""
Shot Prompt Rewriter — Replace Strategy 兜底层 (T20-26 P0 fix)

Backend 配合 AI-ML `app/prompts/shot_adjustment_prompt.py` 的 Mode A/B 升级.

设计目的:
test19 暴露 Shot 15 Founder 重生 5 次都失败的真根因是 PromptRewriter "追加" 策略 —
Haiku 把 Founder intent 追加到原 prompt 末尾, 但不删原 prompt 中的 ghost /
double-exposure / overlap / merging 段落, 导致 Seedream content_safety 永远拒.

═══════════════════════════════════════════════════════════════════
职责分工 (T20-26 Wave 4 双团队协调):
═══════════════════════════════════════════════════════════════════
  AI-ML 层 (`app/prompts/shot_adjustment_prompt.py`):
    - SHOT_ADJUSTMENT_SYSTEM_PROMPT — TWO-MODE rule (Mode A surgical / Mode B replace)
    - build_adjustment_user_prompt(mode="auto") — auto detect tripwire 切 Mode B
    - SEEDREAM_TRIPWIRE_KEYWORDS — 触发词列表
    - detect_seedream_tripwire() — 触发词检测器

  Backend 层 (本模块, regenerate endpoint 实际兜底):
    1. KNOWN_DARK_TERMS — Backend 内部敏感词列表 (与 AI-ML SEEDREAM_TRIPWIRE_KEYWORDS
       有重叠但不必完全一致, 双层防线)
    2. check_replace_effective() — Haiku 返回后**强制校验** replace 真生效
       (找 Haiku 漏的敏感词 + 检测 length suspicious append)
    3. strip_known_dark_terms() — 兜底机械 strip (Haiku 都失败时的最后防线)
    4. find_known_dark_terms() — 检测函数 (Backend 内部一致性校验)

  Helper (保留供未来扩展或 Backend 独立调用):
    5. build_replace_user_prompt() — 完整 Backend 端 replace user prompt 构造
       (含 scene + character context). 当前 endpoint 不用, 因为 AI-ML auto 已能
       cover. 未来如果需要 Backend 完全自主构造 prompt (脱离 AI-ML), 可启用.
    6. gather_scene_context_for_replace() — 从 shot/storyboard 提取 scene 元数据.
    7. gather_character_context_for_replace() — 提取 character 外貌 + 服装.

═══════════════════════════════════════════════════════════════════
Wire 位置: app/api/chapters.py:regenerate_shot endpoint (T20-26)
═══════════════════════════════════════════════════════════════════

Created: 2026-05-19 Wave 4 (Founder 团队 Backend, 配合 AI-ML T20-26 P0)
Reference:
  - KEY_LEARNINGS #37 (Seedream 暗黑题材敏感词)
  - KEY_LEARNINGS #38 (PromptRewriter 必须 replace 不能 append)
  - DEC-045 Wave 4
  - .team-brain/analysis/TEST19_FULL_AUDIT_2026-05-19.md Phase 12
  - Founder 5 次失败实证 (Shot 15 / "陈砚跪在雪地" 仍含原 ghost 段落)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 已知 Seedream 暗黑题材敏感词 (KEY_LEARNINGS #37 实证)
# ---------------------------------------------------------------------------
# test19 Shot 15 5 次失败定位的关键短语 (大小写不敏感, 词边界匹配).
# 这些词在 Seedream content_safety 模型上稳定触发拒绝.
# 任何 Rewriter / Editor 必须在 replace 后**强制删除**这些词, 用安全替代.
#
# Universal: 不绑定特定故事, 任何暗黑/恐怖/悬疑/灵异/逝者题材都会触发.
KNOWN_DARK_TERMS: Tuple[str, ...] = (
    # ghost / vision 类
    "ghost",
    "ghostly",
    "ghosts",
    "spectre",
    "specter",
    "phantom",
    "apparition",
    "spirit overlay",
    "vision overlay",
    "spectral",
    # double exposure / face merge 类 (test19 实测 Shot 15 触发)
    "double-exposure",
    "double exposure",
    "double-exposed",
    "doubly exposed",
    "face overlap",
    "face overlapping",
    "faces overlap",
    "faces merging",
    "two faces merging",
    "two faces merge",
    "identical jaw",
    "identical face",
    "identical features",
    "merged face",
    "merging faces",
    "morphing faces",
    "jaw merging",
    "overlapping faces",
    "overlapping silhouettes",
    # deceased / emerge 类
    "deceased emerges",
    "deceased emerging",
    "the deceased appears",
    "dead person appears",
    "dead emerging",
    "corpse appears",
    "corpse rising",
    # vision 浮现叠加类 (常用作 ghost 替代但同样触发)
    "vision of the deceased",
    "image of the deceased",
)


# ---------------------------------------------------------------------------
# 安全替代提示 (供 LLM 参考)
# ---------------------------------------------------------------------------
# KEY_LEARNINGS #37 推荐: 用 in memory / lingering presence / warm light 等
# 间接表达, 远离 Seedream 敏感词触发.
SAFE_REPLACEMENT_HINTS: str = """\
SAFE ALTERNATIVES for dark / mourning / supernatural themes (use these instead of forbidden terms):
- "ghost of XXX" → solitary candle, single empty chair, soft warm halo, the character alone with a faint trail of light
- "double-exposure of two faces" → character alone in scene + symbolic distant blurred silhouette in deep background (not overlapping the face)
- "deceased XXX emerges" → "in fond memory", "lingering presence", "a warm shaft of light", framed photograph on a wooden shelf
- "vision overlay" → soft golden bokeh, dust motes in sunbeam, distant out-of-focus form (never overlapping face)
- "two faces merging" → split composition: protagonist in foreground sharp, symbolic figure in deep background blurred and offset
"""


# ---------------------------------------------------------------------------
# 1. Replace strategy user prompt builder
# ---------------------------------------------------------------------------
def build_replace_user_prompt(
    original_image_prompt: str,
    user_intent_zh: str,
    scene_context: Optional[Dict[str, Any]] = None,
    character_context: Optional[List[Dict[str, Any]]] = None,
    style_preset: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
) -> str:
    """
    构造给 Haiku 的 user message — replace 策略 (不是 append patch).

    与旧 `build_adjustment_user_prompt()` 区别:
      - 旧: 只传 original_prompt + intent → Haiku 容易"挑几句补丁"
      - 新: 传 scene + characters 完整素材 + 显式 MUST DELETE 敏感词列表
            → Haiku 有素材"全新重写", 强制删除原 prompt 中所有 KNOWN_DARK_TERMS

    AI-ML 在 Wave 4 改 `SHOT_ADJUSTMENT_SYSTEM_PROMPT` 加 replace strategy 规则;
    Backend 用本函数喂更丰富的上下文配合.

    Args:
        original_image_prompt: 现有英文 image_prompt (~200-500 words, 可能含敏感词)
        user_intent_zh: Founder 中文修改意图 (1-2 句话, e.g. "陈砚跪在雪地")
        scene_context: 可选 — scene 元数据 dict
            {
              "scene_id" / "location_id": "...",
              "location_name": "...",
              "lighting": "...",
              "mood": "...",
              "setting": "...",
              "time_of_day": "...",
              "weather": "...",
            }
            (任何缺失字段都安全忽略, 不报错)
        character_context: 可选 — characters_in_scene 详情列表
            [
              {
                "id": "char_001",
                "name": "陈砚" / name_en,
                "character_type": "human" / "animal" / etc,
                "appearance_summary": "...",
                "clothing_summary": "...",
              },
              ...
            ]
        style_preset: 风格 preset 名 (e.g. "ghibli" / "anime" / "realistic")
        aspect_ratio: 画幅 (e.g. "2:3" / "16:9")

    Returns:
        发送给 Haiku 的 user message, 含:
          - <original_prompt> (供 Haiku 识别要删除什么)
          - <user_request> (Founder intent)
          - <scene_context> + <character_context> (重写素材)
          - <forbidden_terms> KNOWN_DARK_TERMS 显式列表
          - <safe_alternatives> SAFE_REPLACEMENT_HINTS
          - REPLACE 策略明确指令
    """
    intent_zh = (user_intent_zh or "").strip()
    if not intent_zh:
        intent_zh = "(no specific change requested; rewrite to be safer / cleaner)"

    # 构造 scene block (跳过空字段, 保持 prompt 简洁)
    scene_lines: List[str] = []
    if scene_context:
        for key in ("scene_id", "location_id", "location_name", "setting",
                    "lighting", "mood", "time_of_day", "weather"):
            v = scene_context.get(key)
            if v and isinstance(v, (str, int, float)):
                scene_lines.append(f"  - {key}: {v}")
    scene_block = "\n".join(scene_lines) if scene_lines else "  (no scene metadata available)"

    # 构造 characters block (只取关键字段, 避免 prompt 膨胀)
    char_lines: List[str] = []
    if character_context:
        for c in character_context:
            if not isinstance(c, dict):
                continue
            name = c.get("name") or c.get("name_en") or c.get("id", "unknown")
            ctype = c.get("character_type") or c.get("type") or "character"
            appearance = (c.get("appearance_summary")
                          or c.get("appearance")
                          or "")
            clothing = (c.get("clothing_summary")
                        or c.get("clothing")
                        or "")
            line = f"  - {name} ({ctype})"
            if appearance:
                line += f"\n      appearance: {appearance}"
            if clothing:
                line += f"\n      clothing: {clothing}"
            char_lines.append(line)
    char_block = "\n".join(char_lines) if char_lines else "  (no character context available)"

    style_line = f"  - style_preset: {style_preset}" if style_preset else "  - style_preset: (preserve from original)"
    aspect_line = f"  - aspect_ratio: {aspect_ratio}" if aspect_ratio else "  - aspect_ratio: (preserve from original)"

    forbidden_list = "\n".join(f"  - {term}" for term in KNOWN_DARK_TERMS)

    return f"""\
<original_prompt>
{original_image_prompt}
</original_prompt>

<user_request>
{intent_zh}
</user_request>

<scene_context>
{scene_block}
</scene_context>

<character_context>
{char_block}
</character_context>

<style_and_aspect>
{style_line}
{aspect_line}
</style_and_aspect>

<forbidden_terms_must_delete>
The original prompt MAY contain these phrases. You MUST DELETE all of them from your output:
{forbidden_list}
</forbidden_terms_must_delete>

<safe_alternatives>
{SAFE_REPLACEMENT_HINTS}
</safe_alternatives>

## STRATEGY: REPLACE, NOT APPEND

You are NOT patching the original prompt. You are rewriting it from scratch using:
1. The scene_context (location, lighting, mood)
2. The character_context (who is in the shot, what they look like / wear)
3. The style_and_aspect (visual style + aspect ratio)
4. The user_request (Founder's modification intent)

The original_prompt is provided ONLY so you can identify which phrases must be DELETED (especially from forbidden_terms_must_delete). DO NOT preserve sentences containing those forbidden phrases.

If the original prompt was 500 words and the new prompt is 350 words because you removed forbidden segments — that's CORRECT. Length stability does NOT apply when forbidden content is being stripped.

Output ONLY the rewritten English image_prompt text. No explanations. No markdown. No wrapping quotes.
"""


# ---------------------------------------------------------------------------
# 2. Sensitive-term detection + strip fallback
# ---------------------------------------------------------------------------
def find_known_dark_terms(text: str) -> List[str]:
    """
    找出 text 中所有出现的 KNOWN_DARK_TERMS (大小写不敏感).

    Returns:
        命中的敏感短语列表 (按出现顺序, 去重保序).
    """
    if not text:
        return []
    lowered = text.lower()
    hits: List[str] = []
    seen = set()
    for term in KNOWN_DARK_TERMS:
        term_lower = term.lower()
        # 多词短语用子串匹配; 单词用词边界匹配避免误伤 ("ghost" 匹配 "ghosts" 算同一类是 OK)
        if " " in term_lower or "-" in term_lower:
            pattern = re.escape(term_lower)
        else:
            pattern = r"\b" + re.escape(term_lower) + r"\b"
        if re.search(pattern, lowered) and term not in seen:
            hits.append(term)
            seen.add(term)
    return hits


def strip_known_dark_terms(text: str) -> Tuple[str, List[str]]:
    """
    机械 strip — 最后兜底防线 (Haiku replace 都失败时启用).

    替换策略:
      - "ghost" / "ghostly" → "warm light"
      - "double-exposure" / "double exposure" → "split composition"
      - "deceased emerges" → "in fond memory"
      - 其他暗黑词 → "" (直接删除, 句子可能略碎但 Seedream 不会拒)

    Args:
        text: 含敏感词的 prompt

    Returns:
        (stripped_text, removed_terms_list)
    """
    if not text:
        return text, []
    replacements: Dict[str, str] = {}
    # 高频替换 (保留 prompt 可读性)
    safe_map = {
        "ghostly": "warm",
        "ghost": "warm light",
        "ghosts": "warm lights",
        "spectre": "silhouette",
        "specter": "silhouette",
        "phantom": "silhouette",
        "apparition": "silhouette",
        "spectral": "soft",
        "double-exposure": "split composition",
        "double exposure": "split composition",
        "double-exposed": "softly framed",
        "doubly exposed": "softly framed",
        "face overlap": "split composition",
        "face overlapping": "split composition",
        "faces overlap": "two figures separated",
        "faces merging": "two figures separated",
        "two faces merging": "two figures separated",
        "two faces merge": "two figures separated",
        "merged face": "single face",
        "merging faces": "two figures separated",
        "morphing faces": "two figures separated",
        "jaw merging": "softly framed",
        "overlapping faces": "two figures separated",
        "overlapping silhouettes": "two distinct silhouettes",
        "identical jaw": "softly framed face",
        "identical face": "softly framed face",
        "identical features": "softly framed features",
        "deceased emerges": "in fond memory",
        "deceased emerging": "in fond memory",
        "the deceased appears": "a warm memory",
        "dead person appears": "a warm memory",
        "dead emerging": "in fond memory",
        "corpse appears": "in fond memory",
        "corpse rising": "in fond memory",
        "vision of the deceased": "warm memory",
        "image of the deceased": "framed photograph",
        "spirit overlay": "warm halo",
        "vision overlay": "warm halo",
        "apparition": "silhouette",
    }
    removed: List[str] = []
    result = text
    # 按短语长度倒序替换 (长短语优先, 防止 "two faces merging" 替换后留下 "faces merging"
    # 再被二次替换产生 "two two figures separated" 拼接)
    ordered_terms = sorted(KNOWN_DARK_TERMS, key=lambda t: -len(t))
    for term in ordered_terms:
        repl = safe_map.get(term.lower(), "")
        # 词边界规则同 find_known_dark_terms
        if " " in term or "-" in term:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
        else:
            pattern = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        if pattern.search(result):
            removed.append(term)
            result = pattern.sub(repl, result)
    # 清理多余空格 / 双逗号
    result = re.sub(r"\s+,", ",", result)
    result = re.sub(r",\s*,", ",", result)
    result = re.sub(r"\s{2,}", " ", result).strip()
    return result, removed


# ---------------------------------------------------------------------------
# 3. Replace 真生效校验
# ---------------------------------------------------------------------------
def check_replace_effective(
    original_prompt: str,
    rewritten_prompt: str,
) -> Dict[str, Any]:
    """
    验证 replace 策略真生效, 不是 append.

    判定标准 (任一不满足都标 effective=False):
      1. rewritten 不含 original 中出现过的任何 KNOWN_DARK_TERMS (强制)
      2. rewritten 长度 <= original 长度 * 2.0 (防 append: append 模式实测 2.7×)
         注: 1.5× 太严, 2.0× 给合法重写余量

    Returns:
        {
          "effective": bool,
          "original_len": int,
          "rewritten_len": int,
          "length_ratio": float,
          "original_dark_terms": list,    # original 含的敏感词
          "rewritten_dark_terms": list,   # rewritten 仍含的敏感词 (空 = 真删了)
          "still_contains_dark_terms": bool,
          "length_suspicious_append": bool,
          "reason": str,                  # 不 effective 的原因 (空 = effective)
        }
    """
    orig_len = len(original_prompt or "")
    new_len = len(rewritten_prompt or "")
    ratio = (new_len / orig_len) if orig_len > 0 else 0.0
    orig_dark = find_known_dark_terms(original_prompt or "")
    new_dark = find_known_dark_terms(rewritten_prompt or "")
    still_dark = len(new_dark) > 0
    length_susp = ratio > 2.0
    effective = (not still_dark) and (not length_susp)
    reason_parts: List[str] = []
    if still_dark:
        reason_parts.append(f"rewritten still contains dark terms: {new_dark}")
    if length_susp:
        reason_parts.append(
            f"length ratio {ratio:.2f}x > 2.0 (suspicious append, not replace)"
        )
    return {
        "effective": effective,
        "original_len": orig_len,
        "rewritten_len": new_len,
        "length_ratio": round(ratio, 3),
        "original_dark_terms": orig_dark,
        "rewritten_dark_terms": new_dark,
        "still_contains_dark_terms": still_dark,
        "length_suspicious_append": length_susp,
        "reason": "; ".join(reason_parts) if reason_parts else "",
    }


# ---------------------------------------------------------------------------
# 4. Context extractors (从 storyboard / characters 提取重写素材)
# ---------------------------------------------------------------------------
def gather_scene_context_for_replace(
    shot: Dict[str, Any],
    storyboard_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    从 shot + storyboard 提取 scene 元数据给 Haiku 重写素材.

    兼容多种字段命名 (location_id / scene_id / scene_index, lighting / lighting_mood):
    任何缺失都安全跳过, 不报错.
    """
    ctx: Dict[str, Any] = {}
    if not isinstance(shot, dict):
        return ctx
    # 直接从 shot 拿
    for key in ("scene_id", "location_id", "scene_index"):
        v = shot.get(key)
        if v is not None:
            ctx[key] = v
    for key in ("setting", "lighting", "mood", "time_of_day", "weather"):
        v = shot.get(key)
        if v:
            ctx[key] = v
    # camera 块内可能有 mood / lighting
    cam = shot.get("camera") or {}
    if isinstance(cam, dict):
        for key in ("lighting", "mood"):
            if key not in ctx and cam.get(key):
                ctx[key] = cam.get(key)

    # 从 storyboard.scenes 查同 scene_id 的元数据
    if storyboard_data and isinstance(storyboard_data, dict):
        scenes = storyboard_data.get("scenes") or []
        if isinstance(scenes, list):
            scene_id = ctx.get("scene_id") or ctx.get("location_id")
            for s in scenes:
                if not isinstance(s, dict):
                    continue
                # 多种 id 字段
                if (s.get("scene_id") == scene_id
                        or s.get("id") == scene_id
                        or s.get("location_id") == scene_id):
                    for key in ("location_name", "setting", "lighting",
                                "mood", "time_of_day", "weather",
                                "description"):
                        if key not in ctx and s.get(key):
                            ctx[key] = s.get(key)
                    break
    return ctx


def gather_character_context_for_replace(
    chars_in_scene: List[str],
    characters_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    从 characters_list 找出 chars_in_scene 涉及的角色, 提炼 appearance + clothing
    给 Haiku 重写素材.

    Args:
        chars_in_scene: ["char_001", "char_003"] 等
        characters_list: chapter.characters_json 解析后的列表

    Returns:
        [
          {
            "id": "char_001",
            "name": "陈砚" / name_en,
            "character_type": "human",
            "appearance_summary": "...",
            "clothing_summary": "...",
          },
          ...
        ]
    """
    if not chars_in_scene or not characters_list:
        return []
    char_map = {c.get("id"): c for c in characters_list if isinstance(c, dict)}
    out: List[Dict[str, Any]] = []
    for cid in chars_in_scene:
        c = char_map.get(cid)
        if not c:
            continue
        appearance_parts: List[str] = []
        physical = c.get("physical") or {}
        if isinstance(physical, dict):
            for k in ("hair_color", "hair_style", "eye_color", "skin_tone",
                      "face_shape"):
                v = physical.get(k)
                if v:
                    appearance_parts.append(f"{k}={v}")
        appearance_summary = ", ".join(appearance_parts)
        # 兜底用 appearance / description 字段
        if not appearance_summary:
            appearance_summary = (c.get("appearance")
                                   or c.get("description") or "")

        clothing_parts: List[str] = []
        clothing = c.get("clothing") or {}
        if isinstance(clothing, dict):
            for k in ("top", "bottom", "footwear", "style"):
                v = clothing.get(k)
                if v:
                    clothing_parts.append(f"{k}={v}")
            accessories = clothing.get("accessories")
            if isinstance(accessories, list) and accessories:
                clothing_parts.append("accessories=" + ", ".join(accessories[:3]))
        clothing_summary = "; ".join(clothing_parts)

        out.append({
            "id": cid,
            "name": c.get("name") or c.get("name_en") or cid,
            "character_type": (c.get("character_type")
                               or c.get("type") or "character"),
            "appearance_summary": appearance_summary,
            "clothing_summary": clothing_summary,
        })
    return out
