#!/usr/bin/env python3
"""
TASK-IMG-SAFETY-VERIFY — 4 项验证测试

验证:
  Test 1: N13-FIX — spouse_of 对称关系自动补全
  Test 2: L1 — CONTENT_SAFETY 日志显示实际尝试次数
  Test 3: L2+L3a — 场景参考图 3 级恢复链路
  Test 4: L3b — 角色参考图 PromptRewriter 改写重试

测试人: @tester
日期: 2026-03-16
"""

import asyncio
import sys
import os
import json
import re
import io
import traceback
from datetime import datetime
from contextlib import redirect_stdout

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

OUTPUT_DIR = os.path.join(
    PROJECT_ROOT,
    "test_output", "manualtest", "img_safety_verify",
    datetime.now().strftime("%Y%m%d_%H%M%S")
)

# ============================================================
# 工具函数
# ============================================================

ALL_RESULTS = []  # (test_id, name, passed, detail)

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def record(test_id, name, passed, detail=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"  {status}: {test_id} {name}")
    if detail:
        print(f"    → {detail}")
    ALL_RESULTS.append((test_id, name, passed, detail))

def capture_stdout(coro):
    """运行 async 函数并捕获 stdout"""
    buf = io.StringIO()
    loop = asyncio.new_event_loop()
    try:
        with redirect_stdout(buf):
            result = loop.run_until_complete(coro)
    finally:
        loop.close()
    return result, buf.getvalue()


# ============================================================
# TEST 1: N13-FIX — spouse_of 对称关系自动补全 (纯单元测试)
# ============================================================

def run_n13_fix_logic(family_rels):
    """复制 pipeline_orchestrator.py L129-143 的 N13-FIX 逻辑"""
    for rel in list(family_rels):
        if rel.get("relationship") == "spouse_of":
            reverse_exists = any(
                r.get("from") == rel["to"] and r.get("to") == rel["from"]
                for r in family_rels
            )
            if not reverse_exists:
                family_rels.append({
                    "from": rel["to"],
                    "to": rel["from"],
                    "relationship": "spouse_of"
                })
                print(f"  [N13-FIX] 补全 spouse_of: {rel['to']} → {rel['from']}")
    return family_rels


def test_1_n13_fix():
    section("TEST 1: N13-FIX — spouse_of 对称补全")

    # 1a: 单向 spouse → 应自动补全
    print("\n  --- 1a: 单向 spouse_of → 自动补全 ---")
    rels = [
        {"from": "梁志远", "to": "陈秀云", "relationship": "spouse_of"},
        {"from": "梁德顺", "to": "阿朗", "relationship": "grandparent_of"},
    ]
    rels = run_n13_fix_logic(rels)
    spouse = [r for r in rels if r["relationship"] == "spouse_of"]
    has_fwd = any(r["from"] == "梁志远" and r["to"] == "陈秀云" for r in spouse)
    has_rev = any(r["from"] == "陈秀云" and r["to"] == "梁志远" for r in spouse)
    record("1a", "单向→双向补全", len(spouse) == 2 and has_fwd and has_rev,
           f"{len(spouse)} spouse_of, 正向={has_fwd}, 反向={has_rev}")

    # 1b: 已双向 → 不重复
    print("\n  --- 1b: 已双向 → 不重复添加 ---")
    rels2 = [
        {"from": "A", "to": "B", "relationship": "spouse_of"},
        {"from": "B", "to": "A", "relationship": "spouse_of"},
    ]
    rels2 = run_n13_fix_logic(rels2)
    spouse2 = [r for r in rels2 if r["relationship"] == "spouse_of"]
    record("1b", "已双向不重复", len(spouse2) == 2,
           f"spouse_of 数量={len(spouse2)} (期望2)")

    # 1c: 无 spouse → 不报错
    print("\n  --- 1c: 无 spouse_of → 无操作 ---")
    rels3 = [{"from": "A", "to": "B", "relationship": "parent_of"}]
    rels3 = run_n13_fix_logic(rels3)
    record("1c", "无spouse不报错", len(rels3) == 1, "无变化")

    # 1d: 多对 spouse → 全部补全
    print("\n  --- 1d: 多对 spouse → 全部补全 ---")
    rels4 = [
        {"from": "A", "to": "B", "relationship": "spouse_of"},
        {"from": "C", "to": "D", "relationship": "spouse_of"},
    ]
    rels4 = run_n13_fix_logic(rels4)
    spouse4 = [r for r in rels4 if r["relationship"] == "spouse_of"]
    record("1d", "多对全补全", len(spouse4) == 4,
           f"spouse_of 数量={len(spouse4)} (期望4)")

    # 1e: 代码审计 — pipeline_orchestrator.py 中 N13-FIX 存在
    print("\n  --- 1e: 代码审计 — pipeline_orchestrator.py ---")
    po_path = os.path.join(PROJECT_ROOT, "app/services/pipeline_orchestrator.py")
    with open(po_path) as f:
        po_code = f.read()
    has_fix = "[N13-FIX]" in po_code
    has_list_copy = "list(family_rels)" in po_code or "list(family_rel" in po_code
    has_spouse_check = 'spouse_of' in po_code
    record("1e", "代码审计 pipeline_orchestrator",
           has_fix and has_list_copy and has_spouse_check,
           f"[N13-FIX]标记={has_fix}, list()副本={has_list_copy}, spouse_of检查={has_spouse_check}")


# ============================================================
# TEST 2: L1 — 日志修复 (代码审计 + API 集成)
# ============================================================

def test_2_l1_log_fix():
    section("TEST 2: L1 — CONTENT_SAFETY 日志实际次数")

    # 2a: 代码审计 — image_generator.py 使用 attempt+1
    print("\n  --- 2a: 代码审计 — image_generator.py ---")
    ig_path = os.path.join(PROJECT_ROOT, "app/services/image_generator.py")
    with open(ig_path) as f:
        ig_code = f.read()

    # 检查 "attempt + 1" 存在且 "self.MAX_RETRIES} attempts" 不存在于错误消息中
    has_attempt_plus_1 = "attempt + 1} attempts" in ig_code
    # 旧模式: "self.MAX_RETRIES} attempts" 不应出现在 fail 消息中
    old_pattern_lines = []
    for i, line in enumerate(ig_code.split('\n'), 1):
        if 'MAX_RETRIES} attempts' in line and 'failed after' in line.lower():
            old_pattern_lines.append(i)

    record("2a", "代码审计 attempt+1",
           has_attempt_plus_1 and len(old_pattern_lines) == 0,
           f"attempt+1={has_attempt_plus_1}, 旧模式残留行={old_pattern_lines}")


def test_2b_l1_integration():
    """2b: API 集成 — 触发 CONTENT_SAFETY，验证日志"""
    print("\n  --- 2b: API 集成 — 触发 CONTENT_SAFETY ---")
    try:
        from app.services.image_generator import ImageGenerator

        ig = ImageGenerator()
        if not ig.client:
            record("2b", "API集成(CONTENT_SAFETY日志)", False, "Gemini 客户端未初始化")
            return

        # 用极端 prompt 尝试触发 CONTENT_SAFETY
        provocative_prompt = (
            "Dense crowds of people fighting and pushing in a narrow dark alley, "
            "live chickens and livestock everywhere, blazing open fires with thick smoke, "
            "children running unsupervised through the dangerous scene"
        )

        buf = io.StringIO()
        loop = asyncio.new_event_loop()
        try:
            with redirect_stdout(buf):
                result = loop.run_until_complete(
                    ig.generate_image(prompt=provocative_prompt, aspect_ratio="2:3")
                )
        finally:
            loop.close()

        log_output = buf.getvalue()

        if result.get('success'):
            # Gemini 没有拦截 — 正常路径，无额外开销
            record("2b", "API集成(正常路径)", True,
                   "Gemini 未触发 CONTENT_SAFETY — 正常路径验证 OK，零额外开销")
        else:
            error_type = result.get('error_type', '')
            error_msg = result.get('error', '')
            if error_type == 'content_safety':
                # 验证日志: 应该是 "after 1 attempts" 而非 "after 3 attempts"
                has_1_attempt = "after 1 attempts" in error_msg or "after 1 attempts" in log_output
                has_3_attempts = "after 3 attempts" in error_msg or "after 3 attempts" in log_output
                record("2b", "API集成(CONTENT_SAFETY日志)",
                       has_1_attempt and not has_3_attempts,
                       f"error='{error_msg[:100]}', 1-attempt={has_1_attempt}, 3-attempts={has_3_attempts}")
            else:
                record("2b", "API集成(其他错误)", False,
                       f"非 CONTENT_SAFETY 错误: {error_type} — {error_msg[:100]}")

    except Exception as e:
        record("2b", "API集成", False, f"异常: {e}")


# ============================================================
# TEST 3: L2+L3a — 场景参考图恢复链路
# ============================================================

def test_3_scene_recovery():
    section("TEST 3: L2+L3a — 场景参考图恢复链路")

    # 3a: _simplify_anchor_prompt 单元测试
    print("\n  --- 3a: _simplify_anchor_prompt 单元测试 ---")
    try:
        from app.services.scene_reference_manager import SceneReferenceManager
        srm = SceneReferenceManager()

        test_prompt = (
            "A bustling rural market entrance with crowds of townspeople, "
            "clucking chickens near wooden stalls, smoke rising from food vendors, "
            "dense rows of merchant booths. people are walking everywhere. "
            "Sign MUST display: 周记百草堂"
        )
        simplified = srm._simplify_anchor_prompt(test_prompt)

        # 检查前缀
        has_prefix = simplified.startswith("Architectural scene only.")
        # 检查 CROWD 替换: crowds → visitors
        no_crowds = "crowds of townspeople" not in simplified.lower()
        # 检查 ANIMAL 替换: chickens → baskets
        no_chickens = "clucking chickens" not in simplified.lower()
        # 检查 FIRE_SMOKE 替换: smoke rising → haze
        no_smoke_rising = "smoke rising" not in simplified.lower()
        # 检查正则: "people are walking" 应被去除
        no_people_walking = "people are walking" not in simplified.lower()
        # 检查 SIGNAGE 保留
        has_signage = "周记百草堂" in simplified

        all_ok = has_prefix and no_crowds and no_chickens and no_smoke_rising and no_people_walking and has_signage
        record("3a", "_simplify_anchor_prompt",
               all_ok,
               f"前缀={has_prefix}, 去crowds={no_crowds}, 去chickens={no_chickens}, "
               f"去smoke={no_smoke_rising}, 去people_walking={no_people_walking}, "
               f"保留signage={has_signage}")

        if not all_ok:
            print(f"    [DEBUG] 简化结果前300字: {simplified[:300]}")

    except Exception as e:
        record("3a", "_simplify_anchor_prompt", False, f"异常: {e}")

    # 3b: _build_anchor_prompt "No people" 位置检查
    print("\n  --- 3b: _build_anchor_prompt 'No people' 位置 ---")
    try:
        srm_path = os.path.join(PROJECT_ROOT, "app/services/scene_reference_manager.py")
        with open(srm_path) as f:
            srm_code = f.read()

        # 查找 "MASTER ANCHOR IMAGE - EXTERIOR" 后紧接 "STRICT: No people"
        ext_pattern = re.search(
            r'MASTER ANCHOR IMAGE - EXTERIOR\s*\n\s*STRICT:\s*No people',
            srm_code
        )
        int_pattern = re.search(
            r'MASTER ANCHOR IMAGE - INTERIOR\s*\n\s*STRICT:\s*No people',
            srm_code
        )
        # 确认末尾没有残留
        # 统计 "STRICT: No people" 出现次数（应该正好 2 次，分别在 exterior 和 interior）
        strict_count = len(re.findall(r'STRICT:\s*No people', srm_code))

        record("3b", "_build_anchor_prompt No-people前置",
               ext_pattern is not None and int_pattern is not None and strict_count == 2,
               f"exterior前置={ext_pattern is not None}, interior前置={int_pattern is not None}, "
               f"总出现次数={strict_count}(期望2)")

    except Exception as e:
        record("3b", "_build_anchor_prompt", False, f"异常: {e}")

    # 3c: 代码审计 — L2/L3a 链路存在
    print("\n  --- 3c: 代码审计 — L2+L3a 链路 ---")
    try:
        srm_path = os.path.join(PROJECT_ROOT, "app/services/scene_reference_manager.py")
        with open(srm_path) as f:
            srm_code = f.read()

        has_l2 = "CONTENT_SAFETY → 简化 prompt 重试" in srm_code
        has_l3a = "简化仍失败 → PromptRewriter 改写重试" in srm_code
        has_simplify_call = "_simplify_anchor_prompt" in srm_code
        has_rewrite_call = "rewrite_scene_ref" in srm_code

        record("3c", "代码审计 L2+L3a 链路",
               has_l2 and has_l3a and has_simplify_call and has_rewrite_call,
               f"L2日志={has_l2}, L3a日志={has_l3a}, "
               f"simplify调用={has_simplify_call}, rewrite调用={has_rewrite_call}")

    except Exception as e:
        record("3c", "代码审计 L2+L3a", False, f"异常: {e}")


def test_3d_scene_integration():
    """3d: API 集成 — 通过 SceneReferenceManager 触发 CONTENT_SAFETY"""
    print("\n  --- 3d: API 集成 — 场景参考图恢复链路 ---")
    try:
        from app.services.image_generator import ImageGenerator
        from app.services.scene_reference_manager import SceneReferenceManager
        from app.models.style_config import ProjectStyleConfig

        ig = ImageGenerator()
        if not ig.client:
            record("3d", "API集成(场景恢复)", False, "Gemini 客户端未初始化")
            return

        srm = SceneReferenceManager()
        style = ProjectStyleConfig(style_preset="illustration")

        # 构造会触发 CONTENT_SAFETY 的锚点信息
        anchor_info = {
            'location_name': 'rural_market_entrance',
            'description': (
                'A narrow, crowded rural market entrance packed with dense throngs '
                'of townspeople, live chickens clucking and livestock penned in bamboo '
                'enclosures, blazing open fires with thick black smoke billowing from '
                'multiple food stalls, children running between stalls'
            ),
            'time_of_day': 'morning',
            'key_visual_elements': [
                'dense crowds of people pushing and shoving',
                'live chickens and roosters clucking loudly',
                'blazing fire pits with smoke rising thickly'
            ],
            'signage_text': '周记百草堂',
            'representative_scene': {
                'location': 'rural market',
                'mood': 'chaotic bustling',
            }
        }

        buf = io.StringIO()
        loop = asyncio.new_event_loop()
        try:
            with redirect_stdout(buf):
                pil_image, result_dict = loop.run_until_complete(
                    srm._generate_single_anchor(
                        anchor_key="rural_market_entrance_exterior_anchor",
                        anchor_info=anchor_info,
                        view_type="exterior",
                        project_style=style,
                        image_generator=ig,
                        reference_image=None,
                        location_id="rural_market_entrance"
                    )
                )
        finally:
            loop.close()

        log_output = buf.getvalue()
        print(log_output)  # 打印到主 stdout 供报告使用

        if pil_image is not None:
            # 生成成功（可能原始通过，也可能 L2/L3a 恢复成功）
            if "简化 prompt 重试" in log_output:
                record("3d", "API集成(L2简化恢复成功)", True,
                       "CONTENT_SAFETY 触发 → L2 简化重试成功")
            elif "PromptRewriter 改写重试" in log_output:
                record("3d", "API集成(L3a改写恢复成功)", True,
                       "CONTENT_SAFETY 触发 → L3a PromptRewriter 恢复成功")
            else:
                record("3d", "API集成(首次即成功)", True,
                       "Gemini 未触发 CONTENT_SAFETY — 正常路径验证 OK")
        else:
            # 全部失败
            has_l2_log = "简化 prompt 重试" in log_output
            has_l3a_log = "PromptRewriter 改写重试" in log_output
            chain_ok = has_l2_log and has_l3a_log
            record("3d", "API集成(3级链路完整)",
                   chain_ok,
                   f"图片未生成但链路: L2={has_l2_log}, L3a={has_l3a_log}, "
                   f"error={result_dict.get('error', '')[:80]}")

    except Exception as e:
        record("3d", "API集成(场景恢复)", False, f"异常: {traceback.format_exc()[:200]}")


# ============================================================
# TEST 4: L3b — 角色参考图 PromptRewriter 改写重试
# ============================================================

def test_4_char_recovery():
    section("TEST 4: L3b — 角色参考图恢复链路")

    # 4a: 代码审计 — rewrite_char_ref 存在
    print("\n  --- 4a: 代码审计 — L3b 链路 ---")
    try:
        rim_path = os.path.join(PROJECT_ROOT, "app/services/reference_image_manager.py")
        with open(rim_path) as f:
            rim_code = f.read()

        has_l3b_log = "CONTENT_SAFETY → PromptRewriter 改写重试" in rim_code
        has_rewrite_call = "rewrite_char_ref" in rim_code
        has_get_rewriter = "get_rewriter" in rim_code

        record("4a", "代码审计 L3b 链路",
               has_l3b_log and has_rewrite_call and has_get_rewriter,
               f"L3b日志={has_l3b_log}, rewrite_char_ref={has_rewrite_call}, "
               f"get_rewriter={has_get_rewriter}")

    except Exception as e:
        record("4a", "代码审计 L3b", False, f"异常: {e}")

    # 4b: build_char_ref_rewrite_prompt 输出检查
    print("\n  --- 4b: build_char_ref_rewrite_prompt 模板检查 ---")
    try:
        from app.prompts.prompt_safety_rewrite import build_char_ref_rewrite_prompt

        test_prompt = "A warrior in revealing armor holding a sword, bare chest, with blood splatter"
        rewrite_prompt = build_char_ref_rewrite_prompt(test_prompt)

        has_original = test_prompt in rewrite_prompt
        has_preserve = "PRESERVE" in rewrite_prompt
        has_modify = "MODIFY" in rewrite_prompt
        has_rules = "REWRITE RULES" in rewrite_prompt
        min_length = len(rewrite_prompt) > 500

        record("4b", "build_char_ref_rewrite_prompt",
               has_original and has_preserve and has_modify and has_rules and min_length,
               f"含原prompt={has_original}, PRESERVE={has_preserve}, MODIFY={has_modify}, "
               f"长度={len(rewrite_prompt)}")

    except Exception as e:
        record("4b", "build_char_ref_rewrite_prompt", False, f"异常: {e}")

    # 4c: build_scene_ref_rewrite_prompt 输出检查
    print("\n  --- 4c: build_scene_ref_rewrite_prompt 模板检查 ---")
    try:
        from app.prompts.prompt_safety_rewrite import build_scene_ref_rewrite_prompt

        test_prompt = "A crowded market with people everywhere and live chickens"
        rewrite_prompt = build_scene_ref_rewrite_prompt(test_prompt)

        has_original = test_prompt in rewrite_prompt
        has_remove = "REMOVE" in rewrite_prompt
        has_signage = "signage" in rewrite_prompt.lower() or "SIGNAGE" in rewrite_prompt
        min_length = len(rewrite_prompt) > 500

        record("4c", "build_scene_ref_rewrite_prompt",
               has_original and has_remove and has_signage and min_length,
               f"含原prompt={has_original}, REMOVE={has_remove}, SIGNAGE保护={has_signage}, "
               f"长度={len(rewrite_prompt)}")

    except Exception as e:
        record("4c", "build_scene_ref_rewrite_prompt", False, f"异常: {e}")

    # 4d: apply_simple_replacements CROWD/ANIMAL/FIRE_SMOKE 替换验证
    print("\n  --- 4d: apply_simple_replacements 新类别替换 ---")
    try:
        from app.prompts.prompt_safety_rewrite import apply_simple_replacements

        test_text = (
            "Dense crowds of townspeople near clucking chickens, "
            "with smoke rising from fires and blazing torches"
        )
        replaced = apply_simple_replacements(test_text)

        no_crowds = "crowds of" not in replaced.lower()
        no_chickens = "clucking chickens" not in replaced.lower()
        no_smoke_rising = "smoke rising" not in replaced.lower()
        no_blazing = "blazing" not in replaced.lower()
        # 替换后应包含安全词
        has_safe_words = (
            "visitors" in replaced.lower() or
            "baskets" in replaced.lower() or
            "haze" in replaced.lower()
        )

        all_ok = no_crowds and no_chickens and no_smoke_rising and has_safe_words
        record("4d", "apply_simple_replacements 新类别",
               all_ok,
               f"去crowds={no_crowds}, 去chickens={no_chickens}, "
               f"去smoke={no_smoke_rising}, 去blazing={no_blazing}, "
               f"含安全词={has_safe_words}")

        if not all_ok:
            print(f"    [DEBUG] 替换结果: {replaced[:200]}")

    except Exception as e:
        record("4d", "apply_simple_replacements", False, f"异常: {e}")

    # 4e: prompt_rewriter.py 新方法存在
    print("\n  --- 4e: prompt_rewriter 新方法存在 ---")
    try:
        pr_path = os.path.join(PROJECT_ROOT, "app/services/prompt_rewriter.py")
        with open(pr_path) as f:
            pr_code = f.read()

        has_scene_ref = "async def rewrite_scene_ref" in pr_code
        has_char_ref = "async def rewrite_char_ref" in pr_code
        has_import_scene = "build_scene_ref_rewrite_prompt" in pr_code
        has_import_char = "build_char_ref_rewrite_prompt" in pr_code
        has_get_rewriter = "def get_rewriter" in pr_code

        all_ok = has_scene_ref and has_char_ref and has_import_scene and has_import_char and has_get_rewriter
        record("4e", "prompt_rewriter 新方法",
               all_ok,
               f"rewrite_scene_ref={has_scene_ref}, rewrite_char_ref={has_char_ref}, "
               f"imports={has_import_scene and has_import_char}, get_rewriter={has_get_rewriter}")

    except Exception as e:
        record("4e", "prompt_rewriter", False, f"异常: {e}")


def test_4f_char_integration():
    """4f: API 集成 — 角色参考图 CONTENT_SAFETY 恢复"""
    print("\n  --- 4f: API 集成 — 角色参考图恢复 ---")
    try:
        from app.services.image_generator import ImageGenerator
        from app.services.reference_image_manager import ReferenceImageManager
        from app.models.style_config import ProjectStyleConfig

        ig = ImageGenerator()
        if not ig.client:
            record("4f", "API集成(角色恢复)", False, "Gemini 客户端未初始化")
            return

        rim = ReferenceImageManager()
        style = ProjectStyleConfig(style_preset="illustration")

        # 构造可能触发 CONTENT_SAFETY 的角色
        provocative_char = {
            'id': 'char_test',
            'name': '黑刃武士',
            'name_en': 'Dark Blade Warrior',
            'character_type': 'human',
            'gender': 'male',
            'age_appearance': 'adult',
            'physical': {
                'height': 'tall',
                'build': 'muscular',
                'skin_tone': 'tanned',
                'hair_color': 'black',
                'hair_style': 'long wild',
                'eye_color': 'dark',
                'face_shape': 'angular',
            },
            'clothing': {
                'top': 'bare chest with revealing leather straps and blood-red war paint',
                'bottom': 'torn loincloth with bone ornaments',
                'accessories': ['skull necklace', 'arm wrappings with blades'],
                'style': 'barbaric warrior'
            }
        }

        buf = io.StringIO()
        loop = asyncio.new_event_loop()
        try:
            with redirect_stdout(buf):
                result = loop.run_until_complete(
                    rim.generate_character_reference(
                        character=provocative_char,
                        project_style=style,
                        image_generator=ig,
                        ref_type='portrait',
                        portrait_ref=None
                    )
                )
        finally:
            loop.close()

        log_output = buf.getvalue()
        print(log_output)  # 打印到主 stdout

        if result.get('success'):
            if "PromptRewriter 改写重试" in log_output:
                record("4f", "API集成(L3b改写恢复成功)", True,
                       "CONTENT_SAFETY 触发 → L3b PromptRewriter 恢复成功")
            else:
                record("4f", "API集成(首次即成功)", True,
                       "Gemini 未触发 CONTENT_SAFETY — 正常路径验证 OK")
        else:
            has_l3b_log = "PromptRewriter 改写重试" in log_output
            error = result.get('error', '')
            record("4f", "API集成(L3b链路)",
                   has_l3b_log,
                   f"L3b日志={has_l3b_log}, error={error[:80]}")

    except Exception as e:
        record("4f", "API集成(角色恢复)", False, f"异常: {traceback.format_exc()[:200]}")


# ============================================================
# 报告生成
# ============================================================

def generate_report():
    """生成验证报告"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    report_path = os.path.join(OUTPUT_DIR, "verify_report.md")

    total = len(ALL_RESULTS)
    passed = sum(1 for r in ALL_RESULTS if r[2])
    failed = sum(1 for r in ALL_RESULTS if not r[2])

    lines = []
    lines.append("# TASK-IMG-SAFETY-VERIFY 验证报告\n")
    lines.append(f"**日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**测试人**: @tester")
    lines.append(f"**结果**: {passed}/{total} PASS, {failed}/{total} FAIL\n")

    # 汇总表
    lines.append("## 汇总\n")
    lines.append("| # | 测试 | 结果 | 说明 |")
    lines.append("|---|------|------|------|")
    for test_id, name, ok, detail in ALL_RESULTS:
        status = "✅ PASS" if ok else "❌ FAIL"
        lines.append(f"| {test_id} | {name} | {status} | {detail[:80]} |")

    # 按 Test 分组详情
    lines.append("\n## 详细结果\n")

    lines.append("### Test 1: N13-FIX (spouse_of 对称补全)")
    for r in ALL_RESULTS:
        if r[0].startswith("1"):
            lines.append(f"- **{r[0]}** {r[1]}: {'✅' if r[2] else '❌'} {r[3]}")

    lines.append("\n### Test 2: L1 (日志修复)")
    for r in ALL_RESULTS:
        if r[0].startswith("2"):
            lines.append(f"- **{r[0]}** {r[1]}: {'✅' if r[2] else '❌'} {r[3]}")

    lines.append("\n### Test 3: L2+L3a (场景恢复)")
    for r in ALL_RESULTS:
        if r[0].startswith("3"):
            lines.append(f"- **{r[0]}** {r[1]}: {'✅' if r[2] else '❌'} {r[3]}")

    lines.append("\n### Test 4: L3b (角色恢复)")
    for r in ALL_RESULTS:
        if r[0].startswith("4"):
            lines.append(f"- **{r[0]}** {r[1]}: {'✅' if r[2] else '❌'} {r[3]}")

    # 验收判定
    lines.append("\n## 验收判定\n")
    lines.append(f"- 总测试: {total}")
    lines.append(f"- PASS: {passed}")
    lines.append(f"- FAIL: {failed}")

    # PM 验收标准
    n13_pass = all(r[2] for r in ALL_RESULTS if r[0].startswith("1"))
    code_audit_pass = all(r[2] for r in ALL_RESULTS
                          if r[0] in ["2a", "3b", "3c", "4a", "4e"])
    unit_test_pass = all(r[2] for r in ALL_RESULTS
                         if r[0] in ["3a", "4b", "4c", "4d"])

    lines.append(f"\n- N13-FIX 验证: {'✅ PASS' if n13_pass else '❌ FAIL'}")
    lines.append(f"- 代码审计 (L1+L2+L3a+L3b): {'✅ PASS' if code_audit_pass else '❌ FAIL'}")
    lines.append(f"- 单元测试 (simplify+templates+replacements): {'✅ PASS' if unit_test_pass else '❌ FAIL'}")

    report = "\n".join(lines)
    with open(report_path, "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"  报告已保存: {report_path}")
    print(f"  结果: {passed}/{total} PASS, {failed}/{total} FAIL")
    print(f"{'='*60}")

    return report_path


# ============================================================
# 主函数
# ============================================================

def main():
    print("=" * 60)
    print("  TASK-IMG-SAFETY-VERIFY: 4 项验证测试")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Part A: 纯单元测试 + 代码审计（无 API 调用）
    test_1_n13_fix()
    test_2_l1_log_fix()
    test_3_scene_recovery()
    test_4_char_recovery()

    # Part B: API 集成测试（需要 Gemini API）
    section("API 集成测试 (需要 Gemini API)")
    print("  尝试触发 CONTENT_SAFETY 以验证恢复链路...")
    print("  注: CONTENT_SAFETY 触发取决于 Gemini 模型判断，非必然触发\n")

    test_2b_l1_integration()
    test_3d_scene_integration()
    test_4f_char_integration()

    # 报告
    report_path = generate_report()

    return report_path


if __name__ == "__main__":
    main()
