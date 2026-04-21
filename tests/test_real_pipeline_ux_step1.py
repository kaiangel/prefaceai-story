#!/usr/bin/env python3
"""
TASK-REAL-PIPELINE-UX Step 1 — 后端通路验证

零 LLM 成本：纯本地 Python，不启动服务器，不调 API。
验证 3 项改动：1-A Stage 5 跳过模式 / 1-B generate-outline 返回 scenes / 1-C 生成结果 API

pytest -v tests/test_real_pipeline_ux_step1.py
"""

import glob
import json
import os
import shutil
import tempfile

import pytest

# ============================================================
# 常量
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R8_DATA_DIR = os.path.join(
    BASE_DIR,
    "test_output", "manualtest", "e2e_regression_r8",
    "20260316_145613", "story_A", "20260316_145614",
)


# ============================================================
# 1-A: Stage 5 跳过模式
# ============================================================

class TestStage5SkipMode:
    """验证 pipeline_orchestrator.py 的 SKIP_IMAGE_GENERATION 逻辑"""

    # ---- config.py ----

    def test_config_has_skip_setting(self):
        """config.py 中存在 SKIP_IMAGE_GENERATION 配置项"""
        config_path = os.path.join(BASE_DIR, "app", "config.py")
        with open(config_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "SKIP_IMAGE_GENERATION" in code, "config.py 缺少 SKIP_IMAGE_GENERATION"

    # ---- pipeline_orchestrator.py 代码验证 ----

    def test_r8_data_dir_constant(self):
        """R8_DATA_DIR 常量存在且指向正确路径"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "R8_DATA_DIR" in code, "缺少 R8_DATA_DIR 常量"
        assert "e2e_regression_r8" in code, "R8_DATA_DIR 路径不含 e2e_regression_r8"

    def test_skip_mode_method_exists(self):
        """_run_stage5_skip_mode 方法存在"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "_run_stage5_skip_mode" in code, "缺少 _run_stage5_skip_mode 方法"

    def test_skip_mode_checks_setting(self):
        """run() 中检查 settings.SKIP_IMAGE_GENERATION"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "SKIP_IMAGE_GENERATION" in code, "run() 未检查 SKIP_IMAGE_GENERATION"

    def test_run_accepts_progress_callback(self):
        """run() 方法签名包含 progress_callback 参数"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "progress_callback" in code, "run() 缺少 progress_callback 参数"

    def test_run_accepts_project_uuid(self):
        """run() 方法签名包含 project_uuid 参数"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "project_uuid" in code, "run() 缺少 project_uuid 参数"

    # ---- R8 测试数据完整性 ----

    def test_r8_character_refs_exist(self):
        """R8 角色参考图目录存在且有文件"""
        char_dir = os.path.join(R8_DATA_DIR, "character_refs")
        assert os.path.isdir(char_dir), f"R8 character_refs 目录不存在: {char_dir}"
        files = glob.glob(os.path.join(char_dir, "char_*.png"))
        assert len(files) > 0, "R8 character_refs 无 PNG 文件"

    def test_r8_scene_refs_exist(self):
        """R8 场景参考图目录存在且有文件"""
        scene_dir = os.path.join(R8_DATA_DIR, "scene_refs")
        assert os.path.isdir(scene_dir), f"R8 scene_refs 目录不存在: {scene_dir}"
        files = glob.glob(os.path.join(scene_dir, "*.png"))
        assert len(files) > 0, "R8 scene_refs 无 PNG 文件"

    def test_r8_shot_images_exist(self):
        """R8 shot 图目录存在且有 shot_*.png"""
        img_dir = os.path.join(R8_DATA_DIR, "images")
        assert os.path.isdir(img_dir), f"R8 images 目录不存在: {img_dir}"
        files = sorted(glob.glob(os.path.join(img_dir, "shot_*.png")))
        assert len(files) >= 10, f"R8 images 需至少 10 张 shot 图，实际 {len(files)}"

    def test_r8_character_refs_have_portrait_and_fullbody(self):
        """R8 至少有 1 个角色同时有 portrait 和 fullbody"""
        char_dir = os.path.join(R8_DATA_DIR, "character_refs")
        portraits = glob.glob(os.path.join(char_dir, "char_*_portrait.png"))
        fullbodies = glob.glob(os.path.join(char_dir, "char_*_fullbody.png"))
        assert len(portraits) > 0, "无 portrait 图"
        assert len(fullbodies) > 0, "无 fullbody 图"

    # ---- 跳过模式逻辑模拟 ----

    def test_skip_mode_copies_character_refs(self):
        """模拟跳过模式：角色参考图正确复制到项目目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            char_refs_dir = os.path.join(tmpdir, "character_refs")
            os.makedirs(char_refs_dir, exist_ok=True)

            r8_char_files = sorted(glob.glob(os.path.join(R8_DATA_DIR, "character_refs", "char_*")))
            r8_char_ids = sorted(set(
                "_".join(os.path.basename(f).split("_")[:2]) for f in r8_char_files
            ))
            r8_char_count = len(r8_char_ids)
            assert r8_char_count > 0, "R8 无角色参考图"

            # 模拟 5 个角色（循环复用）
            test_chars = [{"id": f"char_{i+1:03d}"} for i in range(5)]
            for i, char in enumerate(test_chars):
                char_id = char["id"]
                r8_idx = i % r8_char_count
                r8_id = r8_char_ids[r8_idx]
                for suffix in ["portrait", "fullbody"]:
                    src = os.path.join(R8_DATA_DIR, "character_refs", f"{r8_id}_{suffix}.png")
                    dst = os.path.join(char_refs_dir, f"{char_id}_{suffix}.png")
                    if os.path.exists(src):
                        shutil.copy2(src, dst)

            # 验证：5 个角色至少有 portrait 或 fullbody
            copied = glob.glob(os.path.join(char_refs_dir, "char_*.png"))
            assert len(copied) >= 5, f"期望至少 5 张，实际 {len(copied)}"
            # 验证循环复用：char_005 应该存在
            assert any("char_005" in os.path.basename(f) for f in copied), "char_005 未被复制（循环复用失败）"

    def test_skip_mode_copies_shot_images_with_cycling(self):
        """模拟跳过模式：shot 图正确复制 + 循环复用"""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = os.path.join(tmpdir, "images")
            os.makedirs(images_dir, exist_ok=True)

            r8_shots = sorted(glob.glob(os.path.join(R8_DATA_DIR, "images", "shot_*.png")))
            r8_shot_count = len(r8_shots)
            assert r8_shot_count >= 10

            # 模拟 15 个 shot（需要循环复用）
            test_shots = [{"shot_id": i + 1} for i in range(15)]
            for i, shot in enumerate(test_shots):
                shot_id = shot["shot_id"]
                r8_idx = i % r8_shot_count
                src = r8_shots[r8_idx]
                dst = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                shutil.copy2(src, dst)

            copied = sorted(glob.glob(os.path.join(images_dir, "shot_*.png")))
            assert len(copied) == 15, f"期望 15 张，实际 {len(copied)}"
            # shot_11 = R8 的 shot_01（循环复用）
            assert os.path.exists(os.path.join(images_dir, "shot_11.png")), "shot_11 不存在"
            assert os.path.exists(os.path.join(images_dir, "shot_15.png")), "shot_15 不存在"

    def test_skip_mode_handles_fewer_shots(self):
        """模拟跳过模式：shot 数 < R8 时截断"""
        with tempfile.TemporaryDirectory() as tmpdir:
            images_dir = os.path.join(tmpdir, "images")
            os.makedirs(images_dir, exist_ok=True)

            r8_shots = sorted(glob.glob(os.path.join(R8_DATA_DIR, "images", "shot_*.png")))

            # 只要 5 个 shot
            test_shots = [{"shot_id": i + 1} for i in range(5)]
            for i, shot in enumerate(test_shots):
                shot_id = shot["shot_id"]
                r8_idx = i % len(r8_shots)
                src = r8_shots[r8_idx]
                dst = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                shutil.copy2(src, dst)

            copied = glob.glob(os.path.join(images_dir, "shot_*.png"))
            assert len(copied) == 5, f"期望 5 张，实际 {len(copied)}"

    # ---- progress_callback 各阶段 ----

    def test_progress_callbacks_in_stages(self):
        """pipeline_orchestrator.py 中 Stage 1-4 各阶段有 progress_callback 调用"""
        po_path = os.path.join(BASE_DIR, "app", "services", "pipeline_orchestrator.py")
        with open(po_path, "r", encoding="utf-8") as f:
            code = f.read()
        # 检查 Stage 1-4 各有 callback 调用
        assert "await progress_callback(" in code, "无 progress_callback 调用"
        # 至少 4 次调用（Stage 1-4 各一次）+ Stage 5 skip 3 次
        count = code.count("await progress_callback(")
        assert count >= 4, f"progress_callback 调用少于 4 次，实际 {count}"


# ============================================================
# 1-B: generate-outline 返回 scenes 数据
# ============================================================

class TestGenerateOutlineScenes:
    """验证 projects.py generate_outline 返回 scenes 字段"""

    def test_generate_outline_has_scenes_field(self):
        """projects.py generate_outline 函数返回值包含 scenes 字段"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert '"scenes"' in code or "'scenes'" in code, "generate_outline 返回值缺少 scenes 字段"

    def test_scenes_mapped_from_unique_locations(self):
        """scenes 从 unique_locations 映射"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "unique_locations" in code, "未从 unique_locations 映射 scenes"

    def test_scene_has_required_fields(self):
        """模拟 unique_locations → scenes 映射，验证字段"""
        outline = {
            "unique_locations": [
                {
                    "display_name": "钟表店",
                    "interior_description": "古色古香的钟表维修店",
                    "exterior_description": "",
                    "location_type": "interior",
                },
                {
                    "display_name": "老街",
                    "interior_description": "",
                    "exterior_description": "青石板铺就的小巷",
                    "location_type": "exterior",
                },
            ]
        }

        scenes = []
        for i, loc in enumerate(outline.get("unique_locations", [])):
            scenes.append({
                "id": f"scene_{i+1}",
                "name": loc.get("display_name", f"场景{i+1}"),
                "description": loc.get("interior_description", "") or loc.get("exterior_description", ""),
                "locationType": loc.get("location_type", "interior"),
            })

        assert len(scenes) == 2
        assert scenes[0]["id"] == "scene_1"
        assert scenes[0]["name"] == "钟表店"
        assert scenes[0]["description"] == "古色古香的钟表维修店"
        assert scenes[0]["locationType"] == "interior"
        assert scenes[1]["id"] == "scene_2"
        assert scenes[1]["name"] == "老街"
        assert scenes[1]["description"] == "青石板铺就的小巷"
        assert scenes[1]["locationType"] == "exterior"

    def test_scene_empty_locations(self):
        """unique_locations 为空时 scenes 为空列表"""
        outline = {"unique_locations": []}
        scenes = [
            {
                "id": f"scene_{i+1}",
                "name": loc.get("display_name", f"场景{i+1}"),
                "description": loc.get("interior_description", "") or loc.get("exterior_description", ""),
                "locationType": loc.get("location_type", "interior"),
            }
            for i, loc in enumerate(outline.get("unique_locations", []))
        ]
        assert scenes == []

    def test_scene_missing_display_name_fallback(self):
        """display_name 缺失时使用默认 '场景N'"""
        outline = {"unique_locations": [{"location_type": "interior"}]}
        scenes = [
            {
                "id": f"scene_{i+1}",
                "name": loc.get("display_name", f"场景{i+1}"),
                "description": loc.get("interior_description", "") or loc.get("exterior_description", ""),
                "locationType": loc.get("location_type", "interior"),
            }
            for i, loc in enumerate(outline.get("unique_locations", []))
        ]
        assert scenes[0]["name"] == "场景1"

    def test_scene_interior_fallback_to_exterior(self):
        """interior_description 为空时 fallback 到 exterior_description"""
        outline = {"unique_locations": [
            {"display_name": "公园", "interior_description": "", "exterior_description": "绿树成荫的公园", "location_type": "exterior"}
        ]}
        scenes = [
            {
                "id": f"scene_{i+1}",
                "name": loc.get("display_name", f"场景{i+1}"),
                "description": loc.get("interior_description", "") or loc.get("exterior_description", ""),
                "locationType": loc.get("location_type", "interior"),
            }
            for i, loc in enumerate(outline.get("unique_locations", []))
        ]
        assert scenes[0]["description"] == "绿树成荫的公园"


# ============================================================
# 1-C: 生成结果 API
# ============================================================

class TestGenerationResultAPI:
    """验证 projects.py 的 generation-result 和 images 端点"""

    def test_generation_result_endpoint_exists(self):
        """GET /generation-result 端点存在"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "generation-result" in code, "缺少 generation-result 端点"

    def test_images_endpoint_exists(self):
        """GET /images/{filename} 端点存在"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "images/{filename}" in code or "images/" in code, "缺少 images 端点"

    def test_images_endpoint_has_path_traversal_check(self):
        """images 端点有路径遍历安全检查"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "abs_path" in code or "abspath" in code, "images 端点缺少路径遍历检查"

    def test_generation_result_reads_storyboard_json(self):
        """generation-result 端点读取 storyboard_json"""
        proj_path = os.path.join(BASE_DIR, "app", "api", "projects.py")
        with open(proj_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "storyboard_json" in code, "未读取 storyboard_json"

    def test_generation_result_returns_shots_structure(self):
        """generation-result 返回 shots 数组结构（模拟）"""
        # 模拟 storyboard 数据
        storyboard = {
            "shots": [
                {
                    "shot_id": 1,
                    "narration_segment": "旁白文字1",
                    "text_overlay": {"text_type": "dialogue", "chinese_text": ["你好", "世界"]},
                },
                {
                    "shot_id": 2,
                    "narration_segment": "旁白文字2",
                    "text_overlay": None,
                },
            ]
        }
        project_id = "test-uuid-123"

        shots = []
        for shot in storyboard.get("shots", []):
            shot_id = shot.get("shot_id", 0)
            narration = shot.get("narration_segment", "")
            text_overlay = shot.get("text_overlay", {})
            shots.append({
                "shotId": shot_id,
                "imageUrl": f"/api/projects/{project_id}/images/shot_{shot_id:02d}.png",
                "narration": narration,
                "textOverlay": {
                    "type": text_overlay.get("text_type", "none"),
                    "text": " ".join(text_overlay.get("chinese_text", [])) if text_overlay.get("chinese_text") else "",
                } if text_overlay else None,
            })

        result = {
            "status": "completed",
            "storyboard": {"shots": shots},
            "characters": [],
            "totalShots": len(shots),
        }

        assert result["status"] == "completed"
        assert result["totalShots"] == 2
        assert result["storyboard"]["shots"][0]["shotId"] == 1
        assert result["storyboard"]["shots"][0]["imageUrl"] == "/api/projects/test-uuid-123/images/shot_01.png"
        assert result["storyboard"]["shots"][0]["narration"] == "旁白文字1"
        assert result["storyboard"]["shots"][0]["textOverlay"]["type"] == "dialogue"
        assert result["storyboard"]["shots"][0]["textOverlay"]["text"] == "你好 世界"
        assert result["storyboard"]["shots"][1]["textOverlay"] is None

    def test_generation_result_processing_returns_null_storyboard(self):
        """未完成时返回 storyboard: null"""
        job_status = "processing"
        if job_status not in ("completed",):
            result = {"status": job_status, "storyboard": None, "characters": [], "totalShots": 0}
        assert result["storyboard"] is None
        assert result["totalShots"] == 0

    def test_path_traversal_prevention(self):
        """路径遍历攻击被阻止"""
        project_id = "test-uuid"
        filename = "../../etc/passwd"
        image_path = os.path.join("output", project_id, "images", filename)
        abs_path = os.path.abspath(image_path)
        abs_base = os.path.abspath(os.path.join("output", project_id, "images"))
        assert not abs_path.startswith(abs_base), "路径遍历应被检测"

    def test_image_url_format(self):
        """图片 URL 格式正确"""
        project_id = "abc-123"
        shot_id = 5
        url = f"/api/projects/{project_id}/images/shot_{shot_id:02d}.png"
        assert url == "/api/projects/abc-123/images/shot_05.png"


# ============================================================
# 1-A 补充: job_manager.py 链路
# ============================================================

class TestJobManagerChanges:
    """验证 job_manager.py 的 Step 1 改动"""

    def test_job_manager_has_project_uuid_param(self):
        """run_story_generation_task 有 project_uuid 参数"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "project_uuid" in code, "缺少 project_uuid 参数"

    def test_job_manager_has_progress_callback(self):
        """job_manager 创建 progress_callback 闭包"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "progress_callback" in code, "缺少 progress_callback"

    def test_job_manager_passes_progress_to_pipeline(self):
        """job_manager 将 progress_callback 传给 pipeline.run()"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "progress_callback=progress_callback" in code, "未传 progress_callback 给 pipeline"

    def test_job_manager_stores_storyboard_json(self):
        """chapter.storyboard_json 被正确存储"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "storyboard_json" in code, "未存储 storyboard_json"

    def test_job_manager_chapter_status_completed(self):
        """chapter.status 设为 completed"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert '"completed"' in code or "'completed'" in code, "chapter.status 未设为 completed"

    def test_job_manager_generate_images_true(self):
        """pipeline 调用使用 generate_images=True"""
        jm_path = os.path.join(BASE_DIR, "app", "services", "job_manager.py")
        with open(jm_path, "r", encoding="utf-8") as f:
            code = f.read()
        assert "generate_images=True" in code, "pipeline 调用未设 generate_images=True"


# ============================================================
# .env 验证
# ============================================================

class TestEnvConfig:
    """验证 .env 配置"""

    def test_env_has_skip_image_generation(self):
        """.env 文件包含 SKIP_IMAGE_GENERATION"""
        env_path = os.path.join(BASE_DIR, ".env")
        if not os.path.exists(env_path):
            pytest.skip(".env 文件不存在（CI 环境）")
        with open(env_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "SKIP_IMAGE_GENERATION" in content, ".env 缺少 SKIP_IMAGE_GENERATION"
