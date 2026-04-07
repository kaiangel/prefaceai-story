#!/usr/bin/env python3
"""
TASK-CONFIRM-OUTLINE-TEST + PLOTPOINT-REORDER-FIX + OUTLINE-MERGE-FIX

零 LLM 成本：纯本地 Python，不启动服务器，不调 API。
直接构造 mock 数据，复现 projects.py confirm_outline 合并逻辑，断言结果。

PLOTPOINT-REORDER-FIX: 情节拖拽时 mood/setting/characters_involved 跟随移动。
OUTLINE-MERGE-FIX: summary 同时写入 summary+logline; selected_ending 替换 plot_points[-1]。

测试脚本: tests/test_confirm_outline_wire.py
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

# ============================================================
# Mock 数据：LLM 原始大纲（"逆行的时光"）
# ============================================================

RAW_OUTLINE = {
    "title": "逆行的时光",
    "title_en": "Reverse Time",
    "summary": "年迈的钟表匠贺守时偶然发现百年老钟内藏信，三代人的秘密逐渐浮出水面，最终在钟声中释然。故事以温情治愈为主线，探讨遗憾与释怀的主题。",
    "logline": "年迈的钟表匠贺守时在修复一座百年老钟时，意外发现钟内藏有一封旧信，牵出三代人的秘密与遗憾",
    "characters_overview": [
        {
            "name_suggestion": "贺守时",
            "name_en": "He Shoushi",
            "description": "七十余岁的钟表匠，手艺精湛但性格孤僻",
            "personality": "沉默寡言，对钟表有近乎偏执的热爱",
            "role": "protagonist",
            "age_range": "elderly",
        },
        {
            "name_suggestion": "贺安",
            "name_en": "He An",
            "description": "约十岁的小男孩，贺守时的孙子",
            "personality": "好奇心旺盛，活泼开朗",
            "role": "supporting",
            "age_range": "child",
        },
        {
            "name_suggestion": "宋念慈",
            "name_en": "Song Nianci",
            "description": "六十余岁的邻居老妇，与贺守时是旧相识",
            "personality": "温柔健谈，心思细腻",
            "role": "supporting",
            "age_range": "elderly",
        },
    ],
    "plot_points": [
        {"description": "贺守时在阁楼发现一座锈迹斑斑的百年老钟", "characters_involved": ["贺守时"], "setting": "阁楼", "mood": "神秘"},
        {"description": "修钟过程中发现暗格里藏着一封泛黄的信", "characters_involved": ["贺守时"], "setting": "钟表店", "mood": "惊奇"},
        {"description": "贺安偷看爷爷的信，被信中的故事吸引", "characters_involved": ["贺安", "贺守时"], "setting": "钟表店", "mood": "好奇"},
        {"description": "宋念慈看到信后神情大变，透露信与自己母亲有关", "characters_involved": ["宋念慈", "贺守时"], "setting": "院子", "mood": "震惊"},
        {"description": "三人一起追溯信中的线索，发现三代人纠缠的秘密", "characters_involved": ["贺守时", "贺安", "宋念慈"], "setting": "老街", "mood": "感慨"},
        {"description": "老钟修复完毕，钟声响起的那一刻，三代人的遗憾得以释然", "characters_involved": ["贺守时", "贺安", "宋念慈"], "setting": "钟表店", "mood": "释然"},
    ],
    "ending_options": [
        {"description": "贺守时将修好的钟送给宋念慈，两人相视一笑，往事释怀"},
        {"description": "贺安将信的内容写成作文，在学校朗读，全班感动落泪"},
        {"description": "圆窗后的秘密揭示时光从未真正倒流，但爱跨越了时间"},
    ],
    "visual_tone": {
        "overall_mood": "治愈",
        "color_palette": ["warm amber", "aged sepia", "soft gold"],
        "lighting_style": "warm afternoon light with dust particles",
    },
    "emotional_arc": {
        "opening": "平静中带着孤独感",
        "midpoint": "好奇与紧张交织",
        "climax": "震惊与感慨",
        "resolution": "释然与温暖",
    },
    "unique_locations": [
        {"name": "贺守时的钟表店", "type": "interior"},
        {"name": "老街", "type": "exterior"},
        {"name": "阁楼", "type": "interior"},
    ],
    "narrative_pace": "缓慢推进，层层揭秘",
}

# ============================================================
# Mock 数据：用户在 StageB 的编辑
# ============================================================

USER_EDITS = {
    "title": "逆行的时光_TEST",
    "title_en": "Reverse Time_TEST",
    "summary": "年迈的钟表匠贺守时在修复一座百年老钟时，意外发现钟内藏有一封旧信_PM测试",
    "characters": [
        {
            "name": "贺老师",
            "name_en": "He Laoshi",
            "description": "七十余岁老人（测试）",
            "personality": "沉默寡言_测试标记",
        },
        {
            "name": "贺安",
            "name_en": "He An",
            "description": "约十岁小男孩",
            "personality": "好奇心旺盛",
        },
        {
            "name": "宋念慈",
            "name_en": "Song Nianci",
            "description": "六十余岁邻居老妇",
            "personality": "温柔健谈",
        },
    ],
    # T4: 情节重排序 — 第 3 个(index=2)挪到第 1 位
    # PLOTPOINT-REORDER-FIX: 前端发送 {description, original_index} 对象数组
    "plot_points": [
        {"description": "贺安偷看爷爷的信，被信中的故事吸引", "original_index": 2},           # 原第 3 (0-based: 2)
        {"description": "贺守时在阁楼发现一座锈迹斑斑的百年老钟", "original_index": 0},      # 原第 1 (0-based: 0)
        {"description": "修钟过程中发现暗格里藏着一封泛黄的信", "original_index": 1},         # 原第 2 (0-based: 1)
        {"description": "宋念慈看到信后神情大变，透露信与自己母亲有关", "original_index": 3},  # 原第 4 (0-based: 3)
        {"description": "三人一起追溯信中的线索，发现三代人纠缠的秘密", "original_index": 4},  # 原第 5 (0-based: 4)
        {"description": "老钟修复完毕，钟声响起的那一刻，三代人的遗憾得以释然", "original_index": 5},  # 原第 6 (0-based: 5)
    ],
    "selected_ending": "圆窗后的秘密揭示时光从未真正倒流，但爱跨越了时间",
    "mood": "紧张",
}


# ============================================================
# 合并逻辑复现（projects.py L296-336 的精确副本）
# ============================================================

def merge_outline(raw_outline_json: str, user_edits: dict) -> dict:
    """
    精确复现 projects.py confirm_outline 端点的合并逻辑。
    输入: raw_outline_json (JSON 字符串) + user_edits (dict)
    输出: 合并后的 dict（即将写入 confirmed_outline_json 的内容）
    """
    raw = json.loads(raw_outline_json) if raw_outline_json else {}
    user = user_edits

    # 用户编辑覆盖
    if user.get("title"):
        raw["title"] = user["title"]
    if user.get("title_en"):
        raw["title_en"] = user["title_en"]
    if user.get("summary"):
        raw["summary"] = user["summary"]
        raw["logline"] = user["summary"]   # 同步更新 logline（Stage 2 CharacterDesigner 读这个）

    # 角色: 按索引匹配，更新名字/描述/性格
    if user.get("characters"):
        for i, uc in enumerate(user["characters"]):
            if i < len(raw.get("characters_overview", [])):
                raw["characters_overview"][i]["name_suggestion"] = uc.get("name", "")
                raw["characters_overview"][i]["name_en"] = uc.get("name_en", "")
                raw["characters_overview"][i]["description"] = uc.get("description", "")
                raw["characters_overview"][i]["personality"] = uc.get("personality", "")

    # 情节: PLOTPOINT-REORDER-FIX — 按 original_index 整体移动 dict
    if user.get("plot_points"):
        original = raw.get("plot_points", [])
        reordered = []
        for item in user["plot_points"]:
            if isinstance(item, dict):
                idx = item.get("original_index", 0)
                desc = item.get("description", "")
                if idx < len(original):
                    entry = original[idx].copy() if isinstance(original[idx], dict) else {"description": original[idx]}
                    entry["description"] = desc
                    reordered.append(entry)
            else:
                # 向后兼容: 如果收到纯字符串（旧前端），走原逻辑
                reordered.append({"description": item})
        if reordered:
            raw["plot_points"] = reordered

    # 结局选择
    if user.get("selected_ending"):
        raw["selected_ending"] = user["selected_ending"]
        # MERGE-FIX Bug 2: 用用户选的结局替换 plot_points 最后一条的 description
        if raw.get("plot_points"):
            last = raw["plot_points"][-1]
            if isinstance(last, dict):
                last["description"] = user["selected_ending"]
                last["user_selected_ending"] = True   # 标记，方便后续追溯

    # 情绪
    if user.get("mood"):
        if "visual_tone" not in raw:
            raw["visual_tone"] = {}
        raw["visual_tone"]["overall_mood"] = user["mood"]

    return raw


# ============================================================
# 测试 1: 合并逻辑 8 断言
# ============================================================

def test_merge_logic():
    """验证 confirm_outline 合并逻辑的 8 个断言 + 2 个 LLM 字段保留。"""
    print("\n" + "=" * 60)
    print("测试 1: confirm_outline 合并逻辑 (8 断言)")
    print("=" * 60)

    raw_json = json.dumps(RAW_OUTLINE, ensure_ascii=False)
    result = merge_outline(raw_json, USER_EDITS)

    checks = {}

    # T1: 标题覆盖
    checks["T1: 标题覆盖"] = result["title"] == "逆行的时光_TEST"

    # T2: 简介→logline+summary 映射 (MERGE-FIX Bug 1)
    checks["T2a: summary→logline"] = result["logline"].endswith("_PM测试")
    checks["T2b: summary→summary"] = result["summary"].endswith("_PM测试")

    # T3a: 角色名覆盖 (name_suggestion)
    checks["T3a: 角色名覆盖"] = result["characters_overview"][0]["name_suggestion"] == "贺老师"

    # T3b: 角色描述覆盖
    checks["T3b: 角色描述覆盖"] = "（测试）" in result["characters_overview"][0]["description"]

    # T3c: 角色性格覆盖
    checks["T3c: 角色性格覆盖"] = "测试标记" in result["characters_overview"][0]["personality"]

    # T4: 情节重排序 — 第 1 个位置现在是原来第 3 个情节的内容
    checks["T4: 情节重排序"] = result["plot_points"][0]["description"] == "贺安偷看爷爷的信，被信中的故事吸引"

    # T4b: PLOTPOINT-REORDER-FIX — 元数据跟随移动
    # 原 plot_points[2] 的 mood 是 "好奇"，重排后应跟随到 plot_points[0]
    checks["T4b: mood 跟随重排"] = result["plot_points"][0].get("mood") == "好奇"

    # T5: 结局选择
    checks["T5: 结局选择"] = "圆窗" in result.get("selected_ending", "")

    # T6: 情绪覆盖
    checks["T6: mood→visual_tone"] = result["visual_tone"]["overall_mood"] == "紧张"

    # T7: LLM 字段保留 — emotional_arc
    checks["T7: emotional_arc 保留"] = bool(result.get("emotional_arc")) and len(result["emotional_arc"]) > 0

    # T8: LLM 字段保留 — unique_locations
    checks["T8: unique_locations 保留"] = bool(result.get("unique_locations")) and len(result["unique_locations"]) > 0

    # 打印结果
    all_pass = True
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} — {name}")
        if not passed:
            all_pass = False

    return all_pass, checks


# ============================================================
# 测试 2: 合并后 JSON 完整性
# ============================================================

def test_merge_json_integrity():
    """验证合并后的 JSON 可以正常序列化/反序列化，字段结构完整。"""
    print("\n" + "=" * 60)
    print("测试 2: 合并后 JSON 完整性")
    print("=" * 60)

    raw_json = json.dumps(RAW_OUTLINE, ensure_ascii=False)
    result = merge_outline(raw_json, USER_EDITS)

    checks = {}

    # 可以序列化为 JSON
    try:
        confirmed_json = json.dumps(result, ensure_ascii=False)
        reparsed = json.loads(confirmed_json)
        checks["JSON 序列化/反序列化"] = True
    except (json.JSONDecodeError, TypeError) as e:
        checks["JSON 序列化/反序列化"] = False
        print(f"    ❌ 错误: {e}")

    # 角色数量不变
    checks["角色数量不变 (3)"] = len(result["characters_overview"]) == 3

    # 情节数量不变
    checks["情节数量不变 (6)"] = len(result["plot_points"]) == 6

    # 未编辑的角色字段保留 (第 2 个角色的 role 字段)
    checks["未编辑角色字段保留 (role)"] = result["characters_overview"][1].get("role") == "supporting"

    # 情节元数据跟随重排 (PLOTPOINT-REORDER-FIX)
    # plot_points[0] 现在是原 index=2 的整体 dict，mood 应为 "好奇"
    checks["情节 mood 跟随重排"] = result["plot_points"][0].get("mood") == "好奇"

    # 第 2 个位置是原 index=0，mood 应为 "神秘"
    checks["情节 setting 跟随重排"] = result["plot_points"][0].get("setting") == "钟表店"

    # visual_tone 其他字段保留
    checks["color_palette 保留"] = len(result["visual_tone"].get("color_palette", [])) == 3

    # narrative_pace 保留
    checks["narrative_pace 保留"] = result.get("narrative_pace") == "缓慢推进，层层揭秘"

    # title_en 更新
    checks["title_en 更新"] = result["title_en"] == "Reverse Time_TEST"

    all_pass = True
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} — {name}")
        if not passed:
            all_pass = False

    return all_pass, checks


# ============================================================
# 测试 3: Pipeline Stage 1 跳过逻辑
# ============================================================

def test_pipeline_skip_stage1():
    """验证 Phase2PipelineOrchestrator 在有 confirmed_outline 时跳过 Stage 1。"""
    print("\n" + "=" * 60)
    print("测试 3: Pipeline Stage 1 跳过逻辑")
    print("=" * 60)

    checks = {}

    # 读取 pipeline_orchestrator.py 源码验证 confirmed_outline 分支存在
    pipeline_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "services", "pipeline_orchestrator.py"
    )
    pipeline_path = os.path.normpath(pipeline_path)

    if not os.path.exists(pipeline_path):
        print(f"  ⚠️ 文件不存在: {pipeline_path}")
        checks["pipeline_orchestrator.py 存在"] = False
        return False, checks

    with open(pipeline_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 检查 1: run() 方法签名包含 confirmed_outline 参数
    checks["run() 含 confirmed_outline 参数"] = "confirmed_outline: dict = None" in code

    # 检查 2: 有 "if confirmed_outline:" 分支
    checks["有 if confirmed_outline 分支"] = "if confirmed_outline:" in code

    # 检查 3: 跳过时打印日志 "跳过 LLM 生成"
    checks["跳过日志存在"] = "跳过 LLM 生成" in code

    # 检查 4: else 分支调用 outline_generator.generate
    checks["else 分支调 generate()"] = "outline_generator.generate(" in code

    # 检查 5: confirmed_outline 赋值给 outline
    checks["confirmed → outline 赋值"] = "outline = confirmed_outline" in code

    # 读取 job_manager.py 验证链路透传
    job_mgr_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "services", "job_manager.py"
    )
    job_mgr_path = os.path.normpath(job_mgr_path)

    if os.path.exists(job_mgr_path):
        with open(job_mgr_path, "r", encoding="utf-8") as f:
            jm_code = f.read()

        # 检查 6: job_manager 有 confirmed_outline 参数
        checks["job_manager 含 confirmed_outline"] = "confirmed_outline" in jm_code

        # 检查 7: 有 confirmed_outline 时走 PipelineOrchestrator
        checks["confirmed → PipelineOrchestrator"] = "Phase2PipelineOrchestrator" in jm_code

        # 检查 8: 传入 confirmed_outline 给 pipeline.run
        checks["pipeline.run(confirmed_outline=...)"] = "confirmed_outline=confirmed_outline" in jm_code
    else:
        print(f"  ⚠️ 文件不存在: {job_mgr_path}")
        checks["job_manager.py 存在"] = False

    all_pass = True
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} — {name}")
        if not passed:
            all_pass = False

    return all_pass, checks


# ============================================================
# 测试 4: 代码一致性验证（合并逻辑与 projects.py 源码对照）
# ============================================================

def test_code_consistency():
    """验证 projects.py confirm_outline 端点的合并逻辑关键行存在。"""
    print("\n" + "=" * 60)
    print("测试 4: projects.py 合并逻辑代码验证")
    print("=" * 60)

    projects_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "api", "projects.py"
    )
    projects_path = os.path.normpath(projects_path)

    if not os.path.exists(projects_path):
        print(f"  ⚠️ 文件不存在: {projects_path}")
        return False, {"projects.py 存在": False}

    with open(projects_path, "r", encoding="utf-8") as f:
        code = f.read()

    checks = {}

    # confirm-outline 端点存在
    checks["confirm-outline 端点"] = 'confirm-outline' in code

    # start-generation 端点存在
    checks["start-generation 端点"] = 'start-generation' in code

    # raw_outline_json 读取
    checks["读取 raw_outline_json"] = "raw_outline_json" in code

    # MERGE-FIX Bug 1: summary 同时写入两个字段
    checks['summary 双写 (Bug1)'] = 'raw["summary"] = user["summary"]' in code and 'raw["logline"] = user["summary"]' in code

    # name_suggestion 覆盖
    checks["name_suggestion 覆盖"] = 'name_suggestion' in code

    # plot_points reorder 逻辑（PLOTPOINT-REORDER-FIX）
    checks["plot_points original_index 逻辑"] = 'original_index' in code

    # MERGE-FIX Bug 2: selected_ending 替换 plot_points[-1] + 标记
    checks['selected_ending 写入'] = 'raw["selected_ending"]' in code
    checks['plot_points[-1] 替换 (Bug2)'] = 'last["description"] = user["selected_ending"]' in code
    checks['user_selected_ending 标记'] = 'user_selected_ending' in code

    # visual_tone.overall_mood 写入
    checks["mood→visual_tone 写入"] = 'raw["visual_tone"]["overall_mood"]' in code

    # confirmed_outline_json 写回
    checks["写回 confirmed_outline_json"] = "confirmed_outline_json" in code

    # start-generation 优先读 confirmed
    checks["start-gen 优先 confirmed"] = "confirmed_outline_json or project.raw_outline_json" in code

    # POST /projects/ 不再启动 pipeline（不应有 asyncio.create_task 在 create_project 函数内）
    # 找到 create_project 函数体，检查不含 create_task
    create_fn_start = code.find("async def create_project(")
    if create_fn_start >= 0:
        # 找下一个 async def 作为函数边界
        next_fn = code.find("\nasync def ", create_fn_start + 1)
        # 也检查 @router 作为边界
        next_router = code.find("\n@router", create_fn_start + 1)
        if next_fn < 0:
            next_fn = len(code)
        if next_router >= 0 and next_router < next_fn:
            next_fn = next_router
        create_fn_body = code[create_fn_start:next_fn]
        checks["create_project 无 pipeline"] = "create_task" not in create_fn_body
    else:
        checks["create_project 函数存在"] = False

    all_pass = True
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} — {name}")
        if not passed:
            all_pass = False

    return all_pass, checks


# ============================================================
# 测试 5: OUTLINE-MERGE-FIX — 2 个 Bug 修复验证 (4 场景)
# ============================================================

def test_merge_fix():
    """验证 TASK-OUTLINE-MERGE-FIX 的 2 个 bug 修复。"""
    print("\n" + "=" * 60)
    print("测试 5: OUTLINE-MERGE-FIX (4 场景)")
    print("=" * 60)

    checks = {}

    # ---- T1: summary 正确写入两个字段 ----
    raw_t1 = {
        "logline": "原始一句话",
        "summary": "原始简介100字，描述了一个关于时光的故事",
        "plot_points": [{"description": "开头", "beat": "inciting_incident"}],
    }
    result_t1 = merge_outline(json.dumps(raw_t1, ensure_ascii=False), {"summary": "用户修改后的简介"})
    checks["T1a: summary 被更新"] = result_t1["summary"] == "用户修改后的简介"
    checks["T1b: logline 同步"] = result_t1["logline"] == "用户修改后的简介"

    # ---- T2: summary 未编辑时保持原始值 ----
    raw_t2 = {
        "logline": "原始一句话",
        "summary": "原始简介100字",
        "plot_points": [{"description": "开头"}],
    }
    result_t2 = merge_outline(json.dumps(raw_t2, ensure_ascii=False), {})
    checks["T2a: summary 不覆盖"] = result_t2["summary"] == "原始简介100字"
    checks["T2b: logline 不覆盖"] = result_t2["logline"] == "原始一句话"

    # ---- T3: selected_ending 替换 plot_points 最后一条 ----
    raw_t3 = {
        "plot_points": [
            {"beat": "inciting_incident", "description": "开头", "estimated_duration_seconds": 30},
            {"beat": "resolution", "description": "LLM原始结局", "estimated_duration_seconds": 30},
        ],
        "ending_options": [
            {"id": "ending_1", "description": "LLM原始结局"},
            {"id": "ending_2", "description": "用户选的结局B"},
        ],
    }
    result_t3 = merge_outline(json.dumps(raw_t3, ensure_ascii=False), {"selected_ending": "用户选的结局B"})
    checks["T3a: plot_points[-1] 替换"] = result_t3["plot_points"][-1]["description"] == "用户选的结局B"
    checks["T3b: beat 保留"] = result_t3["plot_points"][-1]["beat"] == "resolution"
    checks["T3c: duration 保留"] = result_t3["plot_points"][-1]["estimated_duration_seconds"] == 30
    checks["T3d: 标记存在"] = result_t3["plot_points"][-1].get("user_selected_ending") == True
    checks["T3e: 其他 plot_point 不变"] = result_t3["plot_points"][0]["description"] == "开头"
    checks["T3f: selected_ending 字段"] = result_t3["selected_ending"] == "用户选的结局B"

    # ---- T4: 重排 + 选结局同时操作 ----
    raw_t4 = {
        "plot_points": [
            {"beat": "inciting_incident", "description": "原始第1", "mood": "紧张"},
            {"beat": "midpoint", "description": "原始第2", "mood": "平静"},
            {"beat": "resolution", "description": "LLM原始结局", "mood": "感人"},
        ],
    }
    user_t4 = {
        "plot_points": [
            {"description": "原始第3", "original_index": 2},  # 原第3拖到第1
            {"description": "原始第1", "original_index": 0},
            {"description": "原始第2", "original_index": 1},
        ],
        "selected_ending": "用户选的结局B",
    }
    result_t4 = merge_outline(json.dumps(raw_t4, ensure_ascii=False), user_t4)
    checks["T4a: 重排 mood 跟随"] = result_t4["plot_points"][0]["mood"] == "感人"
    checks["T4b: 结局替换最后一条"] = result_t4["plot_points"][-1]["description"] == "用户选的结局B"
    checks["T4c: 总数不变"] = len(result_t4["plot_points"]) == 3

    # 打印结果
    all_pass = True
    for name, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} — {name}")
        if not passed:
            all_pass = False

    return all_pass, checks


# ============================================================
# 主入口
# ============================================================

def main():
    print("=" * 60)
    print("TASK-CONFIRM-OUTLINE-TEST — confirm-outline 全链路验证")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"方法: 纯本地 Python，零 LLM / API 成本")
    print("=" * 60)

    results = []
    total_checks = 0
    total_pass = 0

    # 测试 1: 合并逻辑 8+2 断言
    passed, checks = test_merge_logic()
    results.append(("合并逻辑 (8+2 断言)", passed, checks))
    total_checks += len(checks)
    total_pass += sum(1 for v in checks.values() if v)

    # 测试 2: JSON 完整性
    passed, checks = test_merge_json_integrity()
    results.append(("JSON 完整性", passed, checks))
    total_checks += len(checks)
    total_pass += sum(1 for v in checks.values() if v)

    # 测试 3: Pipeline 跳过逻辑
    passed, checks = test_pipeline_skip_stage1()
    results.append(("Pipeline Stage 1 跳过", passed, checks))
    total_checks += len(checks)
    total_pass += sum(1 for v in checks.values() if v)

    # 测试 4: 代码一致性
    passed, checks = test_code_consistency()
    results.append(("代码一致性验证", passed, checks))
    total_checks += len(checks)
    total_pass += sum(1 for v in checks.values() if v)

    # 测试 5: MERGE-FIX 4 场景
    passed, checks = test_merge_fix()
    results.append(("MERGE-FIX (4 场景)", passed, checks))
    total_checks += len(checks)
    total_pass += sum(1 for v in checks.values() if v)

    # 汇总
    print("\n" + "=" * 60)
    print("汇总")
    print("=" * 60)

    all_pass = True
    for name, passed, checks in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        count = sum(1 for v in checks.values() if v)
        print(f"  {status} — {name} ({count}/{len(checks)})")
        if not passed:
            all_pass = False

    print(f"\n  总计: {total_pass}/{total_checks} {'✅ ALL PASS' if all_pass else '❌ HAS FAILURES'}")
    print("=" * 60)

    # 生成报告
    report_dir = os.path.join(
        os.path.dirname(__file__), "..", "test_output", "manualtest",
        f"confirm_outline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "wire_test_report.md")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# TASK-CONFIRM-OUTLINE-TEST 报告\n\n")
        f.write(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**结果**: {total_pass}/{total_checks} {'ALL PASS' if all_pass else 'HAS FAILURES'}\n\n")

        for name, passed, checks in results:
            f.write(f"## {name}\n\n")
            f.write(f"| # | 验证项 | 结果 |\n")
            f.write(f"|---|--------|------|\n")
            for i, (cname, cpassed) in enumerate(checks.items(), 1):
                f.write(f"| {i} | {cname} | {'✅ PASS' if cpassed else '❌ FAIL'} |\n")
            f.write(f"\n")

    print(f"\n  报告: {report_path}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
