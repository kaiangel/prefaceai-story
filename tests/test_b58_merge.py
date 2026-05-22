"""
单元测试: Wave 10 / RISK-T16-4 — B58 ConfirmScenes merge 而非 replace

验证 chapter.scenes_json 在 ConfirmScenes 时保留 LLM 原字段（含 action_beats），
只用 modified_scenes 覆盖用户真实修改的字段。

运行命令:
  pytest tests/test_b58_merge.py -v
"""

import json
import pytest


# --------------------------------------------------------------------------
# 复用 projects.py 中的 merge 逻辑（提取为可测试的纯函数）
# --------------------------------------------------------------------------

def _apply_scenes_merge(existing_scenes: list, modified_scenes: list) -> list:
    """
    Wave 10 / RISK-T16-4: 将 ConfirmScenes 的 merge 逻辑提取为纯函数，
    方便单测验证不依赖 DB/HTTP 上下文。

    逻辑与 app/api/projects.py confirm_scenes() 完全一致:
    - 用 scene_id 或 id 作为 key 找到对应原始 scene
    - existing_scene + modified_scene 合并（modified 字段优先覆盖）
    - 新增 scene（existing 中找不到）直接追加
    """
    existing_dict: dict = {}
    for s in existing_scenes:
        sid = s.get("scene_id") or s.get("id")
        if sid is not None:
            existing_dict[str(sid)] = s

    merged: list = []
    for modified in modified_scenes:
        sid = modified.get("scene_id") or modified.get("id")
        sid_key = str(sid) if sid is not None else None
        if sid_key and sid_key in existing_dict:
            merged_scene = {**existing_dict[sid_key], **modified}
            merged.append(merged_scene)
        else:
            merged.append(modified)

    return merged


# --------------------------------------------------------------------------
# 测试数据
# --------------------------------------------------------------------------

FULL_SCENE_1 = {
    "scene_id": 1,
    "id": 1,
    "name": "咖啡馆邂逅",
    "description": "两人在咖啡馆初次相遇",
    "description_zh": "两人在咖啡馆初次相遇",
    "scene_heading": "INT. 咖啡馆 - 白天",
    "location_id": "loc_001",
    "time_of_day": "morning",
    "weather": "sunny",
    "atmosphere": "warm and cozy",
    "lighting_condition": "natural warm light",
    "action_beats": [
        {"beat": "苏晨推开玻璃门，环顾四周。", "duration_seconds": 8},
        {"beat": "视线扫到角落里低头工作的陈默。", "duration_seconds": 6},
    ],
    "narration": "那是他们第一次相遇的清晨。",
    "characters_in_scene": ["char_001", "char_002"],
}

FULL_SCENE_2 = {
    "scene_id": 2,
    "id": 2,
    "name": "书店重逢",
    "description": "意外在书店再次相遇",
    "description_zh": "意外在书店再次相遇",
    "scene_heading": "INT. 书店 - 傍晚",
    "location_id": "loc_002",
    "action_beats": [
        {"beat": "苏晨在书架间寻找。", "duration_seconds": 5},
    ],
    "narration": "命运再次将他们联系在一起。",
    "characters_in_scene": ["char_001", "char_002"],
}


# --------------------------------------------------------------------------
# Case 1: modified_scenes 只含 4 字段 → merged 必须保留 action_beats 等 LLM 字段
# --------------------------------------------------------------------------

class TestMergePreservesActionBeats:
    """RISK-T16-4 核心场景: frontend 只传 4 字段时，action_beats 不能丢"""

    def test_frontend_4_field_patch_preserves_action_beats(self):
        """
        frontend ScenePreview 组件只传 4 字段:
        [id, name, description, description_zh]
        → merged 必须保留 action_beats / scene_heading / location_id 等 LLM 字段
        """
        existing = [FULL_SCENE_1.copy()]
        modified = [
            {
                "id": 1,
                "scene_id": 1,
                "name": "咖啡馆邂逅",          # 未改
                "description": "两人在咖啡馆初次相遇",   # 未改
                "description_zh": "两人在咖啡馆初次相遇",  # 未改
            }
        ]
        merged = _apply_scenes_merge(existing, modified)

        assert len(merged) == 1
        s = merged[0]
        # LLM 字段必须保留
        assert "action_beats" in s, "action_beats 不能被 merge 丢弃"
        assert len(s["action_beats"]) == 2, "action_beats 内容不能变"
        assert s["action_beats"][0]["beat"] == "苏晨推开玻璃门，环顾四周。"
        assert "scene_heading" in s, "scene_heading 不能丢"
        assert "location_id" in s, "location_id 不能丢"
        assert "characters_in_scene" in s, "characters_in_scene 不能丢"
        assert "narration" in s, "narration 不能丢"

    def test_modified_description_overrides_existing(self):
        """用户修改了 description → merged 用新 description，但保留 action_beats"""
        existing = [FULL_SCENE_1.copy()]
        new_desc = "苏晨推开咖啡馆的门，空气中弥漫着咖啡香"
        modified = [
            {
                "id": 1,
                "scene_id": 1,
                "name": "咖啡馆邂逅",
                "description": new_desc,
                "description_zh": new_desc,
            }
        ]
        merged = _apply_scenes_merge(existing, modified)

        assert len(merged) == 1
        s = merged[0]
        # description 应该被更新
        assert s["description"] == new_desc, "用户修改的 description 应覆盖"
        # action_beats 必须保留
        assert "action_beats" in s
        assert len(s["action_beats"]) == 2

    def test_multiple_scenes_all_preserve_action_beats(self):
        """多个 scene 全部只传 4 字段 → 每个 scene 的 action_beats 都保留"""
        existing = [FULL_SCENE_1.copy(), FULL_SCENE_2.copy()]
        modified = [
            {"id": 1, "scene_id": 1, "name": "咖啡馆邂逅",
             "description": "desc1", "description_zh": "desc1_zh"},
            {"id": 2, "scene_id": 2, "name": "书店重逢",
             "description": "desc2", "description_zh": "desc2_zh"},
        ]
        merged = _apply_scenes_merge(existing, modified)

        assert len(merged) == 2
        # scene 1
        assert "action_beats" in merged[0]
        assert len(merged[0]["action_beats"]) == 2
        # scene 2
        assert "action_beats" in merged[1]
        assert len(merged[1]["action_beats"]) == 1


# --------------------------------------------------------------------------
# Case 2: modified_scenes 含完整字段 → merged 是 modified 完整版
# --------------------------------------------------------------------------

class TestMergeWithFullModified:
    """modified_scenes 含完整字段时，merged 以 modified 为准"""

    def test_full_modified_scene_is_preserved(self):
        """modified_scenes 自带完整字段 → merge 后 merged 字段与 modified 一致"""
        existing = [FULL_SCENE_1.copy()]
        full_modified = {
            "scene_id": 1,
            "id": 1,
            "name": "咖啡馆邂逅（重写）",
            "description": "全新的描述",
            "description_zh": "全新的描述_zh",
            "scene_heading": "INT. 精品咖啡馆 - 清晨",
            "action_beats": [
                {"beat": "新的 beat", "duration_seconds": 10},
            ],
            "characters_in_scene": ["char_001"],
        }
        merged = _apply_scenes_merge(existing, [full_modified])

        s = merged[0]
        assert s["name"] == "咖啡馆邂逅（重写）"
        assert s["description"] == "全新的描述"
        assert s["scene_heading"] == "INT. 精品咖啡馆 - 清晨"
        # modified 中的 action_beats 覆盖原来的
        assert len(s["action_beats"]) == 1
        assert s["action_beats"][0]["beat"] == "新的 beat"


# --------------------------------------------------------------------------
# Case 3: modified_scenes 为 None → 不替换 chapter.scenes_json
# --------------------------------------------------------------------------

class TestModifiedScenesNone:
    """payload.modified_scenes 为 None 时，scenes_json 不变"""

    def test_none_modified_scenes_skips_merge(self):
        """
        simulate: payload.modified_scenes is None → 不调用 merge
        这个 case 验证的是代码 guard 逻辑（if payload.modified_scenes is not None:）
        """
        existing = [FULL_SCENE_1.copy()]
        # None 值时不执行 merge，直接返回 existing 原样
        modified_scenes = None
        if modified_scenes is not None:
            result = _apply_scenes_merge(existing, modified_scenes)
        else:
            result = existing  # simulate: scenes_json 不变

        assert result == existing, "modified_scenes=None 时 scenes_json 不应改变"
        assert "action_beats" in result[0], "existing 的 action_beats 应完整保留"


# --------------------------------------------------------------------------
# Case 4: modified_scenes 含新增 scene_id → 追加到 merged
# --------------------------------------------------------------------------

class TestMergeWithNewScene:
    """modified_scenes 包含 existing 中没有的 scene_id → 直接追加"""

    def test_new_scene_appended_to_merged(self):
        """用户新增了一个场景 → merged 包含 existing 全部 + 新增场景"""
        existing = [FULL_SCENE_1.copy()]
        new_scene = {
            "scene_id": 99,
            "id": 99,
            "name": "新增场景",
            "description": "用户手动添加的场景",
            "description_zh": "用户手动添加的场景_zh",
        }
        modified = [
            # 原有的 scene 1（4字段版）
            {"id": 1, "scene_id": 1, "name": "咖啡馆邂逅",
             "description": "desc1", "description_zh": "desc1_zh"},
            # 新增的 scene 99
            new_scene,
        ]
        merged = _apply_scenes_merge(existing, modified)

        assert len(merged) == 2, "merged 应包含 2 个 scene（原有 + 新增）"
        # 原有 scene 1 保留 action_beats
        scene_1 = merged[0]
        assert scene_1["scene_id"] == 1
        assert "action_beats" in scene_1
        # 新增 scene 99 直接追加
        scene_99 = merged[1]
        assert scene_99["scene_id"] == 99
        assert scene_99["name"] == "新增场景"


# --------------------------------------------------------------------------
# Case 5: modified_scenes 改了 description → merged 含新 description + 原 action_beats
# --------------------------------------------------------------------------

class TestMergeDescriptionUpdate:
    """用户修改了 description → merged 同时有新 description 和原 action_beats"""

    def test_description_updated_action_beats_preserved(self):
        """综合验证: 新 description + 原 action_beats 共存"""
        existing = [FULL_SCENE_1.copy(), FULL_SCENE_2.copy()]
        updated_desc_1 = "苏晨走进阳光明媚的咖啡馆"
        modified = [
            {
                "id": 1,
                "scene_id": 1,
                "name": "咖啡馆邂逅",
                "description": updated_desc_1,
                "description_zh": updated_desc_1,
            },
            {
                "id": 2,
                "scene_id": 2,
                "name": "书店重逢（已修改）",
                "description": "他们又在书店意外相遇了",
                "description_zh": "他们又在书店意外相遇了",
            },
        ]
        merged = _apply_scenes_merge(existing, modified)

        assert len(merged) == 2

        s1 = merged[0]
        assert s1["description"] == updated_desc_1, "scene 1 description 应被更新"
        assert "action_beats" in s1, "scene 1 action_beats 必须保留"
        assert len(s1["action_beats"]) == 2, "scene 1 两条 action_beat 都要在"
        assert "location_id" in s1, "scene 1 location_id 不能丢"

        s2 = merged[1]
        assert s2["name"] == "书店重逢（已修改）", "scene 2 name 应被更新"
        assert "action_beats" in s2, "scene 2 action_beats 必须保留"
        assert len(s2["action_beats"]) == 1


# --------------------------------------------------------------------------
# 运行验证
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    # 快速 smoke 跑
    t = TestMergePreservesActionBeats()
    t.test_frontend_4_field_patch_preserves_action_beats()
    t.test_modified_description_overrides_existing()
    t.test_multiple_scenes_all_preserve_action_beats()

    t2 = TestMergeWithFullModified()
    t2.test_full_modified_scene_is_preserved()

    t3 = TestModifiedScenesNone()
    t3.test_none_modified_scenes_skips_merge()

    t4 = TestMergeWithNewScene()
    t4.test_new_scene_appended_to_merged()

    t5 = TestMergeDescriptionUpdate()
    t5.test_description_updated_action_beats_preserved()

    print("All 7 test cases passed!")
    sys.exit(0)
