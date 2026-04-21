"""
story_music_extractor.py — Pipeline 生产版故事数据提取服务（Wave 1 Step 1）

从 Pipeline 生成的故事 JSON 数据中提取 music prompt 生成所需的 14 字段
+ full_narration + visual_style_hint，返回一个 dict 供下游
music_generation_service.py 使用。

⚠️  PARITY RISK 说明（见 TASK-MUREKA-PIPELINE-INTEGRATION.md 章节 4）：
  - 风险点 1 (narration_quotes 动态化): 不硬编码金句，使用 full_narration
    让 Haiku 在调用时自挑，每个用户故事都不同
  - 风险点 2 (per-scene 数组上限): 限制 max_scenes=6；超出时取 outline 中
    plot_points 关键节点对应的 scene（按 scene.plot_point 字段匹配）
  - 风险点 3 (风格差异): 接收 visual_style_hint 参数，原样传递给下游
  - 风险点 4 (confirmed_outline_json): 传入的 outline 参数必须是 Stage B
    用户 confirmed 后的版本（字段通常叫 confirmed_outline_json），不是原始
    raw_outline_json；raw_outline_json 未经用户确认，mood/plot_points 可能
    和最终故事不符
  - 风险点 5 (prompt cache 质量保证): 所有字段放入 user prompt（每次变化），
    不影响 system prompt cache；输出为扁平 dict，对 Haiku fill_placeholders
    友好

设计约束：
  - 纯数据处理，不调用任何 API
  - 无 DB 交互
  - 所有字段缺失时用空字符串，不抛出 KeyError
  - max_scenes 超限时优先取关键 plot_points 对应的 scene
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("xuhua")

# 关键情节节点的优先级顺序（和 outline 生成时的 beat 命名一致）
# 超出 max_scenes 时按此顺序取关键 scene
_KEY_PLOT_BEATS: list[str] = [
    "inciting_incident",
    "first_turn",
    "midpoint",
    "crisis",
    "climax",
    "resolution",
]


def extract_story_for_music(
    outline: dict,
    screenplay: dict,
    visual_style_hint: str = "",
    max_scenes: int = 6,
) -> dict:
    """
    从 Pipeline JSON 提取 music prompt 生成所需的所有字段。

    ⚠️  outline 参数说明（风险点 4）：
        传入的 outline 应该是 Stage B 用户 confirmed 后的版本。
        在 Pipeline DB 中对应 chapters.confirmed_outline_json 解析结果，
        不要传 raw_outline_json（原始自动生成，未经用户确认）。
        如果用户没有在 Stage B 做任何修改，两者相同，传哪个都可以；
        但如果用户修改了 mood / plot_points / ending，必须传 confirmed 版本。

    Args:
        outline:            Stage 1 输出的故事大纲 dict，或 confirmed_outline_json
                            解析结果。必须包含 title / emotional_arc / narrative_pace
                            / visual_tone / plot_points 等字段。
        screenplay:         Stage 3 输出的分场剧本 dict。包含 scenes 列表，
                            每个 scene 含 atmosphere / narration_tone /
                            narration_pace / narration 等字段。
        visual_style_hint:  从用户选的 style_preset 读取的 music_hint 字段
                            （@ai-ml Step B 产出）。原样传递给下游，不做转换。
        max_scenes:         per-scene 数组字段（sound_design_hints / narration_tones
                            / narration_paces / scene_moods / temperature_feels /
                            full_narration）的 scene 上限。默认 6。
                            超出时取 outline.plot_points 中关键节点对应的 scene
                            （按 scene.plot_point 字段匹配），保证中篇 10+ scenes
                            也能正确截断而不丢失关键戏剧节点。

    Returns:
        dict，包含以下键（字段顺序固定，和 story_input_format.md 一致）：
        {
            "story_title": str,              # outline.title
            "narrative_pace": str,           # outline.narrative_pace
            "overall_mood": str,             # outline.visual_tone.overall_mood
            "emotional_arc_opening": str,    # outline.emotional_arc.opening
            "emotional_arc_midpoint": str,   # outline.emotional_arc.midpoint
            "emotional_arc_climax": str,     # outline.emotional_arc.climax
            "emotional_arc_resolution": str, # outline.emotional_arc.resolution
            "color_palette": str,            # outline.visual_tone.color_palette 拼接
            "sound_design_hints": str,       # per-scene 拼接，限 max_scenes
            "narration_tones": str,          # per-scene 拼接，限 max_scenes
            "narration_paces": str,          # per-scene 拼接，限 max_scenes
            "scene_moods": str,              # per-scene 拼接，限 max_scenes
            "temperature_feels": str,        # per-scene 拼接，限 max_scenes
            "full_narration": str,           # 所有选定 scene 的 narration 拼接
            "visual_style_hint": str,        # 传入的 visual_style_hint 原样返回
        }
    """
    # ── 来自 outline ──────────────────────────────────────────────────────────
    story_title: str = outline.get("title", "")
    narrative_pace: str = outline.get("narrative_pace", "")

    visual_tone: dict = outline.get("visual_tone", {})
    overall_mood: str = visual_tone.get("overall_mood", "")

    arc: dict = outline.get("emotional_arc", {})
    emotional_arc_opening: str = arc.get("opening", "")
    emotional_arc_midpoint: str = arc.get("midpoint", "")
    emotional_arc_climax: str = arc.get("climax", "")
    emotional_arc_resolution: str = arc.get("resolution", "")

    color_palette_raw = visual_tone.get("color_palette", [])
    if isinstance(color_palette_raw, list):
        color_palette: str = ", ".join(str(c) for c in color_palette_raw)
    else:
        # 兼容已经是字符串的情况（防御性处理）
        color_palette = str(color_palette_raw)

    # ── 提取 outline.plot_points 关键节点的 beat → 用于超限场景选择 ──────────
    # plot_points 是 list[dict]，每条有 "beat" 字段（如 "inciting_incident"）
    plot_points: list[dict] = outline.get("plot_points", [])
    key_beats_in_outline: list[str] = [
        pp.get("beat", "") for pp in plot_points if pp.get("beat", "")
    ]

    # ── 来自 screenplay（按 scene_id 顺序排列所有 scenes）───────────────────
    scenes_raw: list[dict] = screenplay.get("scenes", [])
    scenes_sorted: list[dict] = sorted(
        scenes_raw, key=lambda s: int(s.get("scene_id", 0))
    )

    # ── 超限场景选择（风险点 2）───────────────────────────────────────────────
    # 如果 scenes 总数 <= max_scenes，直接全取
    # 如果超出，优先取和 _KEY_PLOT_BEATS 对应的 scene（按优先级顺序，最多取 max_scenes 个）
    selected_scenes: list[dict] = _select_key_scenes(
        scenes_sorted, key_beats_in_outline, max_scenes
    )

    # ── 遍历选定 scenes 提取 per-scene 字段 ─────────────────────────────────
    sound_design_hints_parts: list[str] = []
    narration_tones_parts: list[str] = []
    narration_paces_parts: list[str] = []
    scene_moods_parts: list[str] = []
    temperature_feels_parts: list[str] = []
    narration_parts: list[str] = []

    for scene in selected_scenes:
        scene_id = scene.get("scene_id", "?")
        atm: dict = scene.get("atmosphere", {})

        hint: str = atm.get("sound_design_hint", "").strip()
        if hint:
            sound_design_hints_parts.append(f"Scene {scene_id}: {hint}")

        tone: str = scene.get("narration_tone", "").strip()
        if tone:
            narration_tones_parts.append(f"Scene {scene_id}: {tone}")

        pace: str = scene.get("narration_pace", "").strip()
        if pace:
            narration_paces_parts.append(f"Scene {scene_id}: {pace}")

        mood: str = atm.get("mood", "").strip()
        if mood:
            scene_moods_parts.append(f"Scene {scene_id}: {mood}")

        temp: str = atm.get("temperature_feel", "").strip()
        if temp:
            temperature_feels_parts.append(f"Scene {scene_id}: {temp}")

        narration: str = scene.get("narration", "").strip()
        if narration:
            narration_parts.append(f"[Scene {scene_id}] {narration}")

    sound_design_hints: str = "\n".join(sound_design_hints_parts)
    narration_tones: str = "\n".join(narration_tones_parts)
    narration_paces: str = "\n".join(narration_paces_parts)
    scene_moods: str = "\n".join(scene_moods_parts)
    temperature_feels: str = "\n".join(temperature_feels_parts)
    full_narration: str = "\n\n".join(narration_parts)

    # ── 组装返回 dict（字段顺序固定，和 story_input_format.md 一致）──────────
    return {
        "story_title": story_title,
        "narrative_pace": narrative_pace,
        "overall_mood": overall_mood,
        "emotional_arc_opening": emotional_arc_opening,
        "emotional_arc_midpoint": emotional_arc_midpoint,
        "emotional_arc_climax": emotional_arc_climax,
        "emotional_arc_resolution": emotional_arc_resolution,
        "color_palette": color_palette,
        "sound_design_hints": sound_design_hints,
        "narration_tones": narration_tones,
        "narration_paces": narration_paces,
        "scene_moods": scene_moods,
        "temperature_feels": temperature_feels,
        "full_narration": full_narration,
        "visual_style_hint": visual_style_hint,
    }


# ── 内部辅助函数 ────────────────────────────────────────────────────────────

def _select_key_scenes(
    scenes_sorted: list[dict],
    key_beats_in_outline: list[str],
    max_scenes: int,
) -> list[dict]:
    """
    当 scenes 数量超过 max_scenes 时，从关键 plot_points 节点中选取代表性场景。

    选取策略（按优先级）：
    1. 遍历 _KEY_PLOT_BEATS 优先级顺序（inciting_incident → first_turn →
       midpoint → crisis → climax → resolution）
    2. 在 scenes_sorted 中找 scene.plot_point 匹配的 scene
    3. 如果某个 beat 在 outline 的 plot_points 中存在但 screenplay 里没有对应
       的 scene.plot_point，则跳过
    4. 选够 max_scenes 个后截止，不足 max_scenes 时补充排在最前面的未选 scene

    场景不超出 max_scenes 时直接返回全部 scenes_sorted。

    Args:
        scenes_sorted:          已按 scene_id 排序的 scenes 列表
        key_beats_in_outline:   outline.plot_points 中出现的 beat 名称列表
        max_scenes:             最大场景数上限

    Returns:
        不超过 max_scenes 个 scene 的列表，保持 scene_id 顺序
    """
    if len(scenes_sorted) <= max_scenes:
        return scenes_sorted

    logger.info(
        f"[StoryMusicExtractor] scenes 数量 {len(scenes_sorted)} 超出 "
        f"max_scenes={max_scenes}，启动关键节点选取策略"
    )

    # 建立 plot_point → scene 的映射（每个 beat 只取第一个匹配的 scene）
    beat_to_scene: dict[str, dict] = {}
    for scene in scenes_sorted:
        pp: str = scene.get("plot_point", "").strip()
        if pp and pp not in beat_to_scene:
            beat_to_scene[pp] = scene

    # 按优先级顺序选取
    selected_ids: set[int] = set()
    selected: list[dict] = []

    for beat in _KEY_PLOT_BEATS:
        if len(selected) >= max_scenes:
            break
        if beat in beat_to_scene:
            scene = beat_to_scene[beat]
            sid = int(scene.get("scene_id", -1))
            if sid not in selected_ids:
                selected.append(scene)
                selected_ids.add(sid)

    # 如果关键节点不足 max_scenes，用前面未被选中的 scene 补足
    if len(selected) < max_scenes:
        for scene in scenes_sorted:
            if len(selected) >= max_scenes:
                break
            sid = int(scene.get("scene_id", -1))
            if sid not in selected_ids:
                selected.append(scene)
                selected_ids.add(sid)

    # 按 scene_id 重新排序，保持故事时间顺序
    selected.sort(key=lambda s: int(s.get("scene_id", 0)))

    logger.info(
        f"[StoryMusicExtractor] 选取了 {len(selected)} 个关键 scenes: "
        f"{[s.get('scene_id') for s in selected]}"
    )
    return selected


# ── __main__ 自测块 ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    快速自测：读取年夜饭故事的 outline + screenplay，
    调用 extract_story_for_music()，打印结果。

    运行方式（在项目根目录）：
        python app/services/story_music_extractor.py
    """
    import os

    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.join(_SCRIPT_DIR, "..", "..")

    _STORY_DIR = os.path.join(
        _PROJECT_ROOT,
        "test_output", "manualtest", "sq_upgrade_ab_test", "20260304_113630"
    )

    outline_path = os.path.join(_STORY_DIR, "1_outline.json")
    screenplay_path = os.path.join(_STORY_DIR, "3_screenplay.json")

    print(f"[自测] 读取 outline: {outline_path}")
    print(f"[自测] 读取 screenplay: {screenplay_path}")

    with open(outline_path, encoding="utf-8") as f:
        outline_data = json.load(f)
    with open(screenplay_path, encoding="utf-8") as f:
        screenplay_data = json.load(f)

    total_scenes = len(screenplay_data.get("scenes", []))
    print(f"[自测] screenplay 中共 {total_scenes} 个 scenes")

    # ── 测试 1: 正常调用（年夜饭 5 scenes，未超限）──
    print("\n" + "=" * 60)
    print("[测试 1] 正常调用（max_scenes=6，年夜饭共 5 scenes，不超限）")
    print("=" * 60)

    result = extract_story_for_music(
        outline=outline_data,
        screenplay=screenplay_data,
        visual_style_hint="Korean webtoon style with warm nostalgic palette",
        max_scenes=6,
    )

    for key, value in result.items():
        if key in ("full_narration",):
            # 只打印前 200 字符避免刷屏
            preview = value[:200] + "..." if len(value) > 200 else value
            print(f"  {key}: {repr(preview)}")
        else:
            print(f"  {key}: {repr(value)}")

    # ── 验证返回 dict 包含所有必须字段 ──
    required_keys = [
        "story_title", "narrative_pace", "overall_mood",
        "emotional_arc_opening", "emotional_arc_midpoint",
        "emotional_arc_climax", "emotional_arc_resolution",
        "color_palette", "sound_design_hints", "narration_tones",
        "narration_paces", "scene_moods", "temperature_feels",
        "full_narration", "visual_style_hint",
    ]
    missing = [k for k in required_keys if k not in result]
    if missing:
        print(f"\n[错误] 缺少必须字段: {missing}")
    else:
        print(f"\n[✓] 全部 {len(required_keys)} 个必须字段均存在")

    # ── 测试 2: 超限场景截断（模拟 max_scenes=3 触发关键节点选取）──
    print("\n" + "=" * 60)
    print("[测试 2] max_scenes=3，触发关键节点选取策略")
    print("=" * 60)

    result_limited = extract_story_for_music(
        outline=outline_data,
        screenplay=screenplay_data,
        visual_style_hint="",
        max_scenes=3,
    )

    # 通过计算 "Scene X:" 前缀的行数来验证 scene 数量上限
    sdh_lines = [ln for ln in result_limited["sound_design_hints"].split("\n") if ln.strip()]
    print(f"  sound_design_hints 行数（= 选取的 scenes 数）: {len(sdh_lines)}")
    assert len(sdh_lines) <= 3, f"超限！应 ≤ 3，实际 {len(sdh_lines)}"
    print(f"  [✓] max_scenes=3 上限正确，选取了 {len(sdh_lines)} 个 scenes")
    for line in sdh_lines:
        print(f"    {line[:80]}")

    # ── 测试 3: 空数据容错 ──
    print("\n" + "=" * 60)
    print("[测试 3] 空 outline 和 screenplay 容错")
    print("=" * 60)

    result_empty = extract_story_for_music(
        outline={},
        screenplay={},
        visual_style_hint="",
        max_scenes=6,
    )
    for key, value in result_empty.items():
        print(f"  {key}: {repr(value)}")
    assert all(isinstance(v, str) for v in result_empty.values()), \
        "所有字段应为 str 类型"
    print("[✓] 空数据容错正常，所有字段均为空字符串")

    print("\n[自测完成] extract_story_for_music() 逻辑验证通过")
