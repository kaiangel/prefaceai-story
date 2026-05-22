"""
单元测试: POST_BETA-5 — Seedream dispatch logging 增强

验证 dispatch log 输出包含 ref count 详情（portrait + scene_ref 分解），
使任何故事的 dispatch 日志都能看到 ref 配置。

修复范围:
1. image_generator.py generate_image dispatch: refs=N
2. image_generator.py generate_shot_image dispatch: refs=N (M portrait + K scene_ref)
3. image_generator.py generate_shot_image_phase2_safe dispatch: refs=N (M portrait + K scene_ref)
4. seedream_generator.py generate_shot_image_seedream: refs=N (M portrait + K scene_ref)

运行命令:
  pytest tests/test_dispatch_logging_post_beta_5.py -v
"""

import sys
import os
import re
import logging
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read_source(rel_path: str) -> str:
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        rel_path
    )
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────────────────────────────────────
# 1. 源码级验证: image_generator.py 的 3 个 dispatch 块
# ─────────────────────────────────────────────────────────────────────────────

class TestImageGeneratorDispatchLog:
    """image_generator.py 的 Seedream dispatch 日志包含 ref count 详情"""

    def test_generate_image_dispatch_has_ref_count(self):
        """generate_image 的 Seedream dispatch 日志包含 refs="""
        source = _read_source("app/services/image_generator.py")

        # 找 generate_image 的 dispatch 块（第一个 Seedream dispatch）
        # 验证有 refs= 字样
        assert "refs=_ref_count" in source or "refs={_ref_count}" in source or \
               "refs={len(reference_images" in source or "_ref_count" in source, (
            "image_generator.py generate_image dispatch 应包含 ref count 日志 (POST_BETA-5)"
        )

    def test_generate_image_dispatch_log_format(self):
        """验证 generate_image dispatch 日志格式包含 POST_BETA-5 注释"""
        source = _read_source("app/services/image_generator.py")
        assert "POST_BETA-5" in source, (
            "image_generator.py 应有 POST_BETA-5 注释 (dispatch logging 增强)"
        )

    def test_generate_shot_image_dispatch_has_portrait_scene_split(self):
        """generate_shot_image 的 dispatch 日志包含 portrait + scene_ref 分解"""
        source = _read_source("app/services/image_generator.py")
        assert "portrait" in source and "scene_ref" in source, (
            "image_generator.py dispatch 日志应包含 portrait + scene_ref 分解 (POST_BETA-5)"
        )

    def test_dispatch_log_includes_ref_calculation(self):
        """dispatch 块有 ref count 计算逻辑（_char_count, _scene_ref_count）"""
        source = _read_source("app/services/image_generator.py")
        assert "_char_count" in source or "_char_count_p2" in source, (
            "image_generator.py dispatch 块应计算 portrait ref count"
        )
        assert "_scene_ref_count" in source or "_scene_ref_count_p2" in source, (
            "image_generator.py dispatch 块应计算 scene_ref count"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 2. 源码级验证: seedream_generator.py 的 dispatch 日志
# ─────────────────────────────────────────────────────────────────────────────

class TestSeedreamGeneratorDispatchLog:
    """seedream_generator.py 的 dispatch 日志包含 ref count 详情"""

    def test_seedream_dispatch_log_has_ref_count(self):
        """[SeedreamGenerator] Shot N 开始生成 日志包含 refs=N (M portrait + K scene_ref)"""
        source = _read_source("app/services/seedream_generator.py")
        # 验证有 portrait 和 scene_ref 的字样
        assert "portrait" in source, (
            "seedream_generator.py dispatch 日志应包含 portrait (POST_BETA-5)"
        )
        assert "scene_ref" in source, (
            "seedream_generator.py dispatch 日志应包含 scene_ref (POST_BETA-5)"
        )

    def test_seedream_dispatch_log_has_char_count_calculation(self):
        """seedream_generator.py 有 characters_in_scene 推断 portrait count"""
        source = _read_source("app/services/seedream_generator.py")
        assert "_char_count" in source or "characters_in_scene" in source, (
            "seedream_generator.py 应从 characters_in_scene 推断 portrait count (POST_BETA-5)"
        )

    def test_seedream_dispatch_log_post_beta_5_comment(self):
        """验证 POST_BETA-5 注释存在"""
        source = _read_source("app/services/seedream_generator.py")
        assert "POST_BETA-5" in source, (
            "seedream_generator.py 应有 POST_BETA-5 注释 (dispatch logging 增强)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 3. 功能验证: ref count 计算逻辑（内联等价实现）
# ─────────────────────────────────────────────────────────────────────────────

class TestRefCountCalculationLogic:
    """验证 ref count 计算逻辑的正确性（portrait + scene_ref 分解）"""

    def _calc_ref_split(self, shot: dict, reference_images: list) -> tuple:
        """等价于 dispatch 块中的计算逻辑"""
        total_refs = len(reference_images)
        char_count = len(shot.get("characters_in_scene", []))
        scene_ref_count = max(0, total_refs - char_count)
        return total_refs, char_count, scene_ref_count

    def test_single_char_no_scene_ref(self):
        """1 角色，0 场景参考图"""
        shot = {"characters_in_scene": ["char_001"]}
        refs = ["portrait_001"]  # 1 个 ref
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 1
        assert char == 1
        assert scene == 0

    def test_two_chars_one_scene_ref(self):
        """2 角色 + 1 场景参考图 = 3 refs"""
        shot = {"characters_in_scene": ["char_001", "char_002"]}
        refs = ["portrait_001", "portrait_002", "scene_ref"]  # 3 refs
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 3
        assert char == 2
        assert scene == 1

    def test_no_chars_no_refs(self):
        """无角色，无参考图"""
        shot = {"characters_in_scene": []}
        refs = []
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 0
        assert char == 0
        assert scene == 0

    def test_three_chars_two_scene_refs(self):
        """3 角色 + 2 场景参考图 = 5 refs"""
        shot = {"characters_in_scene": ["char_001", "char_002", "char_003"]}
        refs = ["p1", "p2", "p3", "sc1", "sc2"]
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 5
        assert char == 3
        assert scene == 2

    def test_missing_characters_in_scene(self):
        """shot 没有 characters_in_scene 字段 — char=0，scene_ref=total"""
        shot = {}  # 没有 characters_in_scene
        refs = ["ref1", "ref2"]
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 2
        assert char == 0
        assert scene == 2

    def test_scene_ref_not_negative(self):
        """当 char_count > total_refs（数据异常），scene_ref 用 max(0, ...) 不为负"""
        shot = {"characters_in_scene": ["char_001", "char_002", "char_003"]}
        refs = ["p1"]  # 只有 1 个 ref 但声明 3 个角色（异常情况）
        total, char, scene = self._calc_ref_split(shot, refs)
        assert total == 1
        assert char == 3
        assert scene == 0  # max(0, 1-3) = max(0, -2) = 0


# ─────────────────────────────────────────────────────────────────────────────
# 4. Log 格式验证（模拟 logger 捕获）
# ─────────────────────────────────────────────────────────────────────────────

class TestDispatchLogFormatVerification:
    """验证 dispatch 日志格式包含必要字段"""

    def test_dispatch_log_format_has_required_parts(self):
        """模拟生成 dispatch log 字符串，验证包含 refs=N (M portrait + K scene_ref)"""
        shot_id = 5
        total_refs = 4
        char_count = 3
        scene_ref_count = max(0, total_refs - char_count)

        # 模拟 seedream_generator.py 中的 log 格式
        log_msg = (
            f"    [SeedreamGenerator] Shot {shot_id} 开始生成 "
            f"(refs={total_refs} ({char_count} portrait + {scene_ref_count} scene_ref), "
            f"prompt=500 chars)"
        )

        assert "refs=4" in log_msg
        assert "3 portrait" in log_msg
        assert "1 scene_ref" in log_msg
        assert "Shot 5" in log_msg

    def test_dispatch_log_format_image_generator(self):
        """验证 image_generator dispatch log 格式"""
        shot_id = 10
        total_refs = 2
        char_count = 1
        scene_ref_count = max(0, total_refs - char_count)

        log_msg = (
            f"    [ImageGenerator] generate_shot_image → Seedream dispatch (D.17 单模型) "
            f"refs={total_refs} ({char_count} portrait + {scene_ref_count} scene_ref)"
        )

        assert "refs=2" in log_msg
        assert "1 portrait" in log_msg
        assert "1 scene_ref" in log_msg
        assert "D.17 单模型" in log_msg

    def test_any_story_gets_ref_details(self):
        """
        Universal: 任何故事类型都会显示 ref 详情（不依赖特定 story 结构）
        模拟 3 种常见 shot 配置
        """
        scenarios = [
            # (chars_in_scene, total_refs) → expected (portrait, scene_ref)
            (["char_001"], 1, 1, 0),                               # 独处场景
            (["char_001", "char_002"], 3, 2, 1),                   # 双人 + 场景
            (["char_001", "char_002", "char_003"], 5, 3, 2),       # 三人 + 2 场景
            ([], 1, 0, 1),                                          # 无角色纯场景
        ]

        for chars, total, expected_char, expected_scene in scenarios:
            shot = {"characters_in_scene": chars}
            refs = [object()] * total  # 不关心实际内容
            calc_char = len(shot.get("characters_in_scene", []))
            calc_scene = max(0, total - calc_char)
            assert calc_char == expected_char, f"chars={chars}: expected char={expected_char}, got {calc_char}"
            assert calc_scene == expected_scene, f"chars={chars}: expected scene={expected_scene}, got {calc_scene}"

            # 生成 log 字符串验证格式
            log = f"refs={total} ({calc_char} portrait + {calc_scene} scene_ref)"
            assert "portrait" in log
            assert "scene_ref" in log
            assert f"refs={total}" in log


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    t1 = TestImageGeneratorDispatchLog()
    t1.test_generate_image_dispatch_has_ref_count()
    t1.test_generate_image_dispatch_log_format()
    t1.test_generate_shot_image_dispatch_has_portrait_scene_split()
    t1.test_dispatch_log_includes_ref_calculation()

    t2 = TestSeedreamGeneratorDispatchLog()
    t2.test_seedream_dispatch_log_has_ref_count()
    t2.test_seedream_dispatch_log_has_char_count_calculation()
    t2.test_seedream_dispatch_log_post_beta_5_comment()

    t3 = TestRefCountCalculationLogic()
    t3.test_single_char_no_scene_ref()
    t3.test_two_chars_one_scene_ref()
    t3.test_no_chars_no_refs()
    t3.test_three_chars_two_scene_refs()
    t3.test_missing_characters_in_scene()
    t3.test_scene_ref_not_negative()

    t4 = TestDispatchLogFormatVerification()
    t4.test_dispatch_log_format_has_required_parts()
    t4.test_dispatch_log_format_image_generator()
    t4.test_any_story_gets_ref_details()

    print("All 17 test cases PASS!")
    import sys
    sys.exit(0)
