"""
Phase 2.0 Pipeline Orchestrator

整合5阶段生成流程：
Stage 1: StoryOutlineGenerator - 故事大纲
Stage 2: CharacterDesigner - 角色设计
Stage 3: ScreenplayWriter - 分场剧本
Stage 4: StoryboardDirector - 分镜脚本
Stage 5: ShotImageGenerator - 镜头图像生成

数据流：
idea → outline.json → characters.json → screenplay.json → storyboard.json → images/
"""

import json
import os
import re
import asyncio
from datetime import datetime
from typing import Optional, List
from PIL import Image

from app.services.story_outline_generator import StoryOutlineGenerator
from app.services.character_designer import CharacterDesigner
from app.services.screenplay_writer import ScreenplayWriter
from app.services.storyboard_director import StoryboardDirector
from app.services.image_generator import ImageGenerator
from app.services.reference_image_manager import ReferenceImageManager
from app.services.scene_reference_manager import SceneReferenceManager
from app.models.style_config import ProjectStyleConfig
from app.services.text_overlay_service import TextOverlayService
from app.services.shot_validator import ShotValidator


class Phase2PipelineOrchestrator:
    """
    Phase 2.0 完整生成流程编排器

    使用方法：
    ```python
    orchestrator = Phase2PipelineOrchestrator(output_dir="./output")
    result = await orchestrator.run(
        idea="雨夜公交站，错过末班车的三个人",
        style_preset="anime",
        target_duration_minutes=3
    )
    ```
    """

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir

        # 初始化各阶段服务
        self.outline_generator = StoryOutlineGenerator()
        self.character_designer = CharacterDesigner()
        self.screenplay_writer = ScreenplayWriter()
        self.storyboard_director = StoryboardDirector()
        self.image_generator = ImageGenerator()

        # T9: 文字渲染配置（与 generate_shot_image_phase2() 默认值同步）
        self.use_native_text = True
        # T17: Shot 后置视觉验证
        self.shot_validator = ShotValidator()

        # 状态跟踪
        self.current_stage = None
        self.stage_results = {}

    async def run(
        self,
        idea: str,
        style_preset: str = "anime",
        target_duration_minutes: int = 3,
        language: str = "zh-CN",
        character_count: int = 3,
        generate_images: bool = True,
        max_concurrent_images: int = 2,
        shots_limit: int = 0,
        custom_style_analysis: dict = None,
        character_seeds: dict = None,
        scene_seeds: dict = None,
        confirmed_outline: dict = None,
    ) -> dict:
        """
        运行完整的5阶段生成流程

        Args:
            idea: 用户创意
            style_preset: 视觉风格预设
            target_duration_minutes: 目标时长（分钟）
            language: 语言
            character_count: 角色数量
            generate_images: 是否生成图像（可设为False只生成文本）
            max_concurrent_images: 最大并发图像生成数
            shots_limit: 限制生成的shot数量（0=不限制）

        Returns:
            完整的生成结果
        """
        start_time = datetime.now()
        project_id = start_time.strftime("%Y%m%d_%H%M%S")
        project_dir = os.path.join(self.output_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Phase 2.0 Pipeline 开始")
        print(f"{'='*60}")
        print(f"Project ID: {project_id}")
        print(f"Idea: {idea}")
        print(f"Style: {style_preset}")
        print(f"Target: {target_duration_minutes}分钟")
        print(f"{'='*60}\n")

        try:
            # ============================================================
            # Stage 1: 故事大纲生成
            # ============================================================
            self.current_stage = "Stage 1: StoryOutlineGenerator"
            print(f"\n{'='*40}")
            print(f"Stage 1: 生成故事大纲")
            print(f"{'='*40}")

            if confirmed_outline:
                print(f"  使用用户确认后的大纲（跳过 LLM 生成）")
                outline = confirmed_outline
            else:
                outline = await self.outline_generator.generate(
                    idea=idea,
                    style_preset=style_preset,
                    target_duration_minutes=target_duration_minutes,
                    language=language,
                    character_count=character_count
                )

            self.stage_results["outline"] = outline

            # N13-FIX: 自动补全 spouse_of 对称关系
            family_rels = outline.get("family_relationships", [])
            for rel in list(family_rels):  # 遍历副本，避免修改遍历中的列表
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

            self._save_json(project_dir, "1_outline.json", outline)

            print(f"✅ Stage 1 完成: {outline.get('title', 'N/A')}")

            # ============================================================
            # Stage 2: 角色设计
            # ============================================================
            self.current_stage = "Stage 2: CharacterDesigner"
            print(f"\n{'='*40}")
            print(f"Stage 2: 设计角色")
            print(f"{'='*40}")

            characters = await self.character_designer.design(outline)

            self.stage_results["characters"] = characters
            self._save_json(project_dir, "2_characters.json", characters)

            char_names = [c.get("name", "N/A") for c in characters.get("characters", [])]
            print(f"✅ Stage 2 完成: {', '.join(char_names)}")

            # ============================================================
            # Stage 3: 分场剧本
            # ============================================================
            self.current_stage = "Stage 3: ScreenplayWriter"
            print(f"\n{'='*40}")
            print(f"Stage 3: 编写分场剧本")
            print(f"{'='*40}")

            screenplay = await self.screenplay_writer.write(
                outline, characters,
                family_relationships=outline.get("family_relationships", [])
            )

            self.stage_results["screenplay"] = screenplay
            self._save_json(project_dir, "3_screenplay.json", screenplay)

            scene_count = len(screenplay.get("scenes", []))
            beat_count = screenplay.get("total_action_beats", 0)
            print(f"✅ Stage 3 完成: {scene_count}场戏, {beat_count}个动作节拍")

            # ============================================================
            # Stage 4: 分镜脚本
            # ============================================================
            self.current_stage = "Stage 4: StoryboardDirector"
            print(f"\n{'='*40}")
            print(f"Stage 4: 创建分镜脚本")
            print(f"{'='*40}")

            visual_tone = outline.get("visual_tone", {})
            storyboard = await self.storyboard_director.direct(
                screenplay=screenplay,
                characters=characters,
                visual_tone=visual_tone,
                style_preset=style_preset,
                characters_overview=outline.get("characters_overview", []),
                family_relationships=outline.get("family_relationships", [])
            )

            self.stage_results["storyboard"] = storyboard
            self._save_json(project_dir, "4_storyboard.json", storyboard)

            # 保存prompt质量报告
            self._save_prompt_quality_report(storyboard, project_dir)

            shot_count = len(storyboard.get("shots", []))
            print(f"✅ Stage 4 完成: {shot_count}个镜头")

            # ============================================================
            # Stage 5: 图像生成（可选）
            # ============================================================
            if generate_images:
                self.current_stage = "Stage 5: ShotImageGenerator"
                print(f"\n{'='*40}")
                print(f"Stage 5: 生成镜头图像")
                print(f"{'='*40}")

                images_dir = os.path.join(project_dir, "images")
                os.makedirs(images_dir, exist_ok=True)
                # T22: with_text_dir 仅在 TextOverlay 备用通道时创建
                with_text_dir = None
                if not self.use_native_text:
                    with_text_dir = os.path.join(project_dir, "with_text_images")
                    os.makedirs(with_text_dir, exist_ok=True)

                # TextOverlay 服务初始化
                text_overlay_service = TextOverlayService()

                # 5a. 生成角色参考图
                print("\n--- 5a. 生成角色参考图 ---")
                ref_manager = ReferenceImageManager()

                # 创建风格配置（自定义风格优先）
                project_style = ProjectStyleConfig(style_preset=style_preset)
                if custom_style_analysis:
                    from app.services.style_enforcer import StyleEnforcer
                    custom_enforcement = StyleEnforcer.create_custom_enforcement(custom_style_analysis)
                    project_style.custom_enforcement = custom_enforcement

                # 为每个角色生成参考图
                char_list = characters.get("characters", [])
                for char in char_list:
                    char_id = char.get("id", "unknown")
                    char_name = char.get("name", char_id)
                    seed = (character_seeds or {}).get(char_id)
                    if seed:
                        print(f"  生成 {char_name} 参考图（使用用户 seed 图）...", end=" ")
                    else:
                        print(f"  生成 {char_name} 参考图...", end=" ")
                    try:
                        await ref_manager.generate_character_multi_refs(
                            character=char,
                            project_style=project_style,
                            image_generator=self.image_generator,
                            seed_image=seed,
                        )
                        print("✅")
                    except Exception as e:
                        print(f"❌ {e}")

                print(f"✅ 角色参考图生成完成")

                # 保存角色参考图
                char_refs_dir = os.path.join(project_dir, "character_refs")
                os.makedirs(char_refs_dir, exist_ok=True)
                ref_manager.save_all_references(char_refs_dir)

                # 5a.5. 生成场景参考图
                print("\n--- 5a.5. 生成场景参考图 ---")
                unique_locations = outline.get("unique_locations", [])
                scene_ref_manager = None

                if unique_locations:
                    scene_ref_manager = SceneReferenceManager()
                    print(f"  共 {len(unique_locations)} 个场景位置")

                    # T21: 计算每个 location 的最大角色数量
                    location_char_counts = {}
                    for sc in screenplay.get("scenes", []):
                        loc_ref = sc.get("location_ref", "")
                        chars = sc.get("characters_in_scene", [])
                        if loc_ref and chars:
                            location_char_counts[loc_ref] = max(
                                location_char_counts.get(loc_ref, 0), len(chars)
                            )

                    try:
                        scene_anchors = await scene_ref_manager.generate_anchor_images(
                            scenes=[],  # Phase 2.0 直接用 unique_locations
                            project_style=project_style,
                            image_generator=self.image_generator,
                            unique_locations=unique_locations,
                            delay=3.0,
                            location_character_counts=location_char_counts,  # T21
                            seed_images=scene_seeds,  # 用户上传场景 seed 图
                        )

                        # 保存场景参考图
                        scene_refs_dir = os.path.join(project_dir, "scene_refs")
                        os.makedirs(scene_refs_dir, exist_ok=True)
                        for anchor_key, anchor_data in scene_anchors.items():
                            img = anchor_data.get('image')
                            if img:
                                img.save(os.path.join(scene_refs_dir, f"{anchor_key}.png"))

                        print(f"✅ 场景参考图生成完成: {len(scene_anchors)}张")
                    except Exception as e:
                        print(f"⚠️ 场景参考图生成失败: {e}")
                        scene_ref_manager = None
                else:
                    print("⚠️ 无 unique_locations，跳过场景参考图")

                # 5b. 生成镜头图像
                print("\n--- 5b. 生成镜头图像 ---")
                shots = storyboard.get("shots", [])

                # 应用shots_limit限制
                if shots_limit > 0 and len(shots) > shots_limit:
                    print(f"  ⚠️ 限制生成前 {shots_limit} 个shots（总共 {len(shots)} 个）")
                    shots = shots[:shots_limit]

                image_results = []
                reference_images_log = []  # 记录每个shot的参考图使用情况

                for i, shot in enumerate(shots):
                    shot_id = shot.get("shot_id", i + 1)
                    print(f"\n  生成 Shot {shot_id}/{len(shots)}...")

                    # 获取角色参考图 - SQ-2: 智能选择，每角色1张
                    char_direction = shot.get("character_direction", {})
                    chars_in_scene = char_direction.get("characters_visible", [])
                    shot_type = shot.get("camera", {}).get("shot_size", "medium_shot")
                    char_refs = ref_manager.get_smart_references_for_scene(chars_in_scene, shot_type)

                    # 获取场景参考图 - 从scene_id追溯到location_id
                    scene_refs = []
                    location_id = None
                    if scene_ref_manager:
                        scene_id = shot.get("scene_id")
                        location_id = self._get_location_id_for_scene(
                            scene_id, screenplay, unique_locations
                        )
                        if location_id:
                            scene_refs = scene_ref_manager.get_references_for_location(location_id)

                    # 合并参考图：角色参考图 + 场景参考图
                    all_refs = char_refs + scene_refs

                    # 日志输出
                    ref_info = []
                    if chars_in_scene:
                        ref_info.append(f"角色: {chars_in_scene} ({len(char_refs)}张)")
                    if location_id and scene_refs:
                        ref_info.append(f"场景: {location_id} ({len(scene_refs)}张)")
                    if ref_info:
                        print(f"    {', '.join(ref_info)}")

                    # 记录参考图使用情况
                    reference_images_log.append({
                        "shot_id": shot_id,
                        "characters_in_scene": chars_in_scene,
                        "char_refs_count": len(char_refs),
                        "location_id": location_id,
                        "scene_refs_count": len(scene_refs),
                        "total_refs": len(all_refs)
                    })

                    # T-I: Prompt Pre-Check (v1 log-only, 不阻断不修改 prompt)
                    pre_check_warnings = self._pre_check_prompt(shot, characters)
                    for w in pre_check_warnings:
                        print(f"    [PromptPreCheck] Shot {shot_id}: ⚠️ {w}")

                    # T17: Shot 生成 + Haiku 视觉验证 + Auto-Retry
                    MAX_SHOT_RETRIES = 1  # T-B: 最多 retry 1 次，共 2 次尝试（R7 数据：第 3 次尝试 0% 通过率）
                    best_result = None
                    text_overlay_data = shot.get("text_overlay", {})

                    for attempt in range(MAX_SHOT_RETRIES + 1):
                        if attempt > 0:
                            print(f"    [T17] Retry {attempt}/{MAX_SHOT_RETRIES} Shot {shot_id}...")

                        # 使用Phase 2.0增强生成 (DEC-014: previous_shot removed)
                        # TASK-SAFE-INTEGRATION: 使用 safe 版本（含 PromptRewriter CONTENT_SAFETY 恢复）
                        result = await self.image_generator.generate_shot_image_phase2_safe(
                            shot=shot,
                            storyboard=storyboard,
                            characters=characters,
                            style_preset=style_preset,
                            reference_images=all_refs,
                            screenplay=screenplay,
                            aspect_ratio="2:3",
                            use_native_text=self.use_native_text
                        )

                        if not result.get("success"):
                            best_result = result
                            break  # 生成失败不 retry（API 错误由 image_generator 内部处理）

                        best_result = result

                        # T28: 从 composition 中提取关键道具（Stage 4 输出含 foreground/background）
                        key_props = []
                        composition = shot.get("composition", {})
                        if composition:
                            for field in ["foreground", "background", "key_object"]:
                                val = composition.get(field, "")
                                if val and isinstance(val, str) and len(val) > 2:
                                    key_props.append(val)

                        # T17+T28+T30: Haiku 视觉验证（含道具存在性检测）
                        props_log = f" + {len(key_props)} props" if key_props else ""
                        print(f"    [ShotValidator] Shot {shot_id}: 开始验证 (expect {len(chars_in_scene)} chars{props_log})")
                        validation = await self.shot_validator.validate_shot(
                            pil_image=result["pil_image"],
                            expected_character_count=len(chars_in_scene),
                            text_overlay_data=text_overlay_data,
                            key_props=key_props if key_props else None
                        )
                        print(f"    [ShotValidator] Shot {shot_id}: valid={validation['valid']}, reason={validation['reason']}")

                        if validation["valid"]:
                            if attempt > 0:
                                print(f"    [T17] ✅ Shot {shot_id} retry 后验证通过")
                            break
                        else:
                            print(f"    [T17] ⚠️ Shot {shot_id} 验证失败: {validation['reason']}")
                            if attempt == MAX_SHOT_RETRIES:
                                print(f"    [T17] Shot {shot_id} 已达最大重试次数，使用当前结果")

                    # 处理最终结果
                    result = best_result
                    if result.get("success"):
                        # 保存无文字版图像
                        image_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                        result["pil_image"].save(image_path)

                        # TextOverlay: 生成带文字版本
                        with_text_path = None
                        text_type = text_overlay_data.get("text_type", "none") if text_overlay_data else "none"
                        # T12-UNIFY + T22: use_native_text 时 NB2 已渲染所有文字（DEC-012 架构），
                        # 直接指向 raw image，不复制；仅 use_native_text=False 时走 TextOverlay 备用通道
                        use_native_text = self.use_native_text
                        if text_type != "none":
                            if use_native_text:
                                # T22: NB2 原生渲染，with_text_path 直接指向 raw image（不复制）
                                with_text_path = image_path
                            else:
                                try:
                                    with_text_image = text_overlay_service.process_shot(
                                        result["pil_image"].copy(), text_overlay_data
                                    )
                                    with_text_path = os.path.join(with_text_dir, f"shot_{shot_id:02d}.png")
                                    with_text_image.save(with_text_path)
                                    print(f"    ✅ TextOverlay: {with_text_path}")
                                except Exception as te:
                                    print(f"    ⚠️ TextOverlay失败: {te}")

                        image_results.append({
                            "shot_id": shot_id,
                            "success": True,
                            "image_path": image_path,
                            "with_text_path": with_text_path,
                            "generation_time": result.get("generation_time_seconds", 0)
                        })
                        print(f"    ✅ Shot {shot_id} 保存: {image_path}")
                    else:
                        image_results.append({
                            "shot_id": shot_id,
                            "success": False,
                            "error": result.get("error", "Unknown error")
                        })
                        print(f"    ❌ Shot {shot_id} 失败: {result.get('error')}")

                    # 控制并发（简单串行，可优化为并行）
                    await asyncio.sleep(0.5)

                self.stage_results["images"] = image_results
                self._save_json(project_dir, "5_image_results.json", image_results)

                # 保存参考图使用日志
                self._save_json(project_dir, "reference_images_log.json", reference_images_log)
                print(f"  参考图使用日志已保存: reference_images_log.json")

                success_count = sum(1 for r in image_results if r.get("success"))
                print(f"\n✅ Stage 5 完成: {success_count}/{len(shots)} 图像生成成功")

            # ============================================================
            # 完成
            # ============================================================
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            summary = {
                "project_id": project_id,
                "project_dir": project_dir,
                "idea": idea,
                "style_preset": style_preset,
                "target_duration_minutes": target_duration_minutes,
                "title": outline.get("title", ""),
                "total_characters": len(characters.get("characters", [])),
                "total_scenes": len(screenplay.get("scenes", [])),
                "total_shots": len(storyboard.get("shots", [])),
                "images_generated": generate_images,
                "pipeline_duration_seconds": round(duration, 2),
                "stages_completed": list(self.stage_results.keys()),
                "timestamp": end_time.isoformat()
            }

            self._save_json(project_dir, "summary.json", summary)

            print(f"\n{'='*60}")
            print(f"Phase 2.0 Pipeline 完成!")
            print(f"{'='*60}")
            print(f"项目目录: {project_dir}")
            print(f"总耗时: {duration:.1f}秒")
            print(f"故事标题: {summary['title']}")
            print(f"角色数: {summary['total_characters']}")
            print(f"场景数: {summary['total_scenes']}")
            print(f"镜头数: {summary['total_shots']}")
            print(f"{'='*60}\n")

            return {
                "success": True,
                "summary": summary,
                "stage_results": self.stage_results
            }

        except Exception as e:
            print(f"\n❌ Pipeline 失败于 {self.current_stage}: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "failed_stage": self.current_stage,
                "stage_results": self.stage_results
            }

    def _pre_check_prompt(self, shot: dict, characters: dict) -> list:
        """
        T-I: Prompt Pre-Check — v1 仅日志，不阻断不修改 prompt

        4 个预检维度:
        - P1: characters_visible 数量 vs prompt 中 "EXACTLY N"
        - P2: 画外角色物理接触描述
        - P3: 空间矛盾（v2 预留）
        - P4: dialogue embed + native text 对同一 speaker 重复指令
        """
        warnings = []
        image_prompt = shot.get("image_prompt", "")
        char_direction = shot.get("character_direction", {})
        chars_visible = char_direction.get("characters_visible", [])
        text_overlay = shot.get("text_overlay", {})

        # P1: characters_visible count vs prompt "EXACTLY N"
        match = re.search(r'EXACTLY\s+(\d+)\s+characters?', image_prompt, re.IGNORECASE)
        if match:
            prompt_count = int(match.group(1))
            actual_count = len(chars_visible)
            if prompt_count != actual_count:
                warnings.append(
                    f"P1 — prompt 指定 EXACTLY {prompt_count} 角色，"
                    f"但 characters_visible 有 {actual_count} 人"
                )

        # P2: off-screen physical contact keywords
        prompt_lower = image_prompt.lower()
        offscreen_kws = ["off-screen", "off screen", "outside the frame", "beyond the frame"]
        contact_kws = [
            "grip", "pull", "pulled", "hold", "holding", "held",
            "embrace", "embracing", "grab", "grabbing", "drag", "dragging",
            "tug", "tugging", "clutch", "clutching"
        ]
        has_offscreen = any(kw in prompt_lower for kw in offscreen_kws)
        has_contact = any(kw in prompt_lower for kw in contact_kws)
        if has_offscreen and has_contact:
            warnings.append("P2 — 检测到画外角色物理接触描述（off-screen + 物理接触关键词）")

        # P3: spatial contradiction — reserved for v2

        # P4: off_screen_speaker=True 但 speaker 在 characters_visible 中
        if text_overlay and text_overlay.get("off_screen_speaker"):
            text_type = text_overlay.get("text_type", "")
            chinese_text = text_overlay.get("chinese_text", "")
            if text_type in ("dialogue", "dialogue_with_thought",
                             "dialogue_with_narration", "narration_with_dialogue"):
                # 提取 speaker 名
                speaker_names = set()
                texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]
                for txt in texts:
                    if isinstance(txt, str):
                        m = re.match(r'^([\w\u4e00-\u9fff]+?)(?:内心)?[：:]', txt)
                        if m:
                            speaker_names.add(m.group(1))

                # 构建 name→id 映射
                char_name_to_id = {}
                for c in characters.get("characters", []):
                    cid = c.get("id", "")
                    cname = c.get("name", "")
                    if cid and cname:
                        char_name_to_id[cname] = cid

                for speaker in speaker_names:
                    char_id = char_name_to_id.get(speaker)
                    if not char_id:
                        for name, cid in char_name_to_id.items():
                            if speaker in name or name in speaker:
                                char_id = cid
                                break
                    if char_id and char_id in chars_visible:
                        warnings.append(
                            f"P4 — speaker '{speaker}' 同时出现在 "
                            f"off_screen dialogue 和 characters_visible 中"
                        )

        return warnings

    def _save_json(self, directory: str, filename: str, data: dict) -> str:
        """保存JSON文件"""
        filepath = os.path.join(directory, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath

    def _get_location_id_for_scene(
        self,
        scene_id: int,
        screenplay: dict,
        unique_locations: Optional[List[dict]] = None
    ) -> Optional[str]:
        """
        从scene_id获取对应的location_id

        注意：screenplay中的location_id可能与outline的unique_locations不一致
        此方法会尝试从unique_locations中找到最匹配的location_id

        Args:
            scene_id: 场景ID（对应storyboard中的scene_id）
            screenplay: 分场剧本数据
            unique_locations: outline中的unique_locations列表

        Returns:
            location_id 或 None（如果找不到）
        """
        if not scene_id or not screenplay:
            return None

        # 获取screenplay中该scene的location_id
        screenplay_location_id = None
        for scene in screenplay.get("scenes", []):
            if scene.get("scene_id") == scene_id:
                screenplay_location_id = scene.get("location_id")
                break

        if not screenplay_location_id:
            return None

        # 如果没有unique_locations，直接返回screenplay的location_id
        if not unique_locations:
            return screenplay_location_id

        # 尝试精确匹配
        for loc in unique_locations:
            if loc.get("location_id") == screenplay_location_id:
                return screenplay_location_id

        # 精确匹配失败，使用第一个unique_location作为fallback
        # 这是因为LLM可能生成了不同的location_id
        if unique_locations:
            fallback_id = unique_locations[0].get("location_id")
            print(f"  ⚠️ location_id不匹配: screenplay用'{screenplay_location_id}', fallback到'{fallback_id}'")
            return fallback_id

        return screenplay_location_id

    def _save_prompt_quality_report(self, storyboard: dict, output_dir: str) -> None:
        """保存image_prompt质量报告"""
        report_lines = ["# Image Prompt 质量报告\n\n"]

        total_prompts = 0
        total_chars = 0
        quality_issues = 0

        for shot in storyboard.get("shots", []):
            shot_id = shot.get("shot_id")
            prompt = shot.get("image_prompt", "")
            total_prompts += 1
            total_chars += len(prompt)

            report_lines.append(f"## Shot {shot_id}\n")
            report_lines.append(f"**字符数**: {len(prompt)}\n")
            report_lines.append(f"**Prompt内容**:\n```\n{prompt}\n```\n")

            # T-D: 扩展关键词（复用 storyboard_director.py _check_prompt_quality 的 ~90 关键词列表）
            prompt_lower = prompt.lower()
            checks = {
                "镜头信息 (camera/framing)": any(k in prompt_lower for k in [
                    "shot", "close-up", "closeup", "wide", "medium", "extreme", "full",
                    "establishing", "insert", "cutaway", "pov", "over-the-shoulder",
                    "angle", "high angle", "low angle", "eye level", "dutch", "bird's eye",
                    "overhead", "tilted", "lens", "focus", "depth of field", "bokeh",
                    "35mm", "50mm", "telephoto", "wide-angle",
                    "composition", "framing", "foreground", "background", "midground",
                    "rule of thirds", "centered", "negative space", "symmetry",
                ]),
                "光线描述 (lighting/mood)": any(k in prompt_lower for k in [
                    "light", "lighting", "sunlight", "moonlight", "neon", "streetlight",
                    "ambient", "backlight", "rim light", "fill light", "key light",
                    "shadow", "shadows", "silhouette", "highlight", "contrast",
                    "glow", "reflection", "mood", "moody", "atmosphere", "atmospheric",
                    "dramatic", "cinematic", "ethereal", "dreamy", "gritty", "noir",
                    "warm", "cold", "cool", "golden hour", "blue hour",
                    "foggy", "misty", "hazy", "diffused", "harsh", "soft light",
                ]),
                "角色外观 (appearance/clothing)": any(k in prompt_lower for k in [
                    "expression", "face", "facial", "eyes", "gaze", "look", "stare",
                    "smile", "frown", "tears", "crying", "laughing",
                    "posture", "pose", "stance", "standing", "sitting", "leaning",
                    "gesture", "reaching", "holding", "gripping", "pointing", "walking",
                    "wearing", "dressed", "outfit", "clothes", "clothing",
                    " in a ", " in an ", " in his ", " in her ",
                    "shirt", "pants", "dress", "jacket", "coat", "sweater",
                    "glasses", "watch", "bag", "hat", "scarf", "hair",
                ]),
            }

            report_lines.append("**质量检查**:\n")
            for check_name, passed in checks.items():
                status = "✅" if passed else "❌"
                report_lines.append(f"- {status} {check_name}\n")
                if not passed:
                    quality_issues += 1

            report_lines.append("\n")

        # 添加汇总
        avg_chars = total_chars / total_prompts if total_prompts > 0 else 0
        report_lines.insert(1, f"**汇总**: {total_prompts}个shots, 平均{avg_chars:.0f}字符/prompt, {quality_issues}个质量问题\n\n")

        # 保存报告
        report_path = os.path.join(output_dir, "prompt_quality_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("".join(report_lines))

        # 同时保存到forclaudeweb
        try:
            with open("forclaudeweb/prompt_quality_report.md", "w", encoding="utf-8") as f:
                f.write("".join(report_lines))
        except:
            pass

    def _convert_characters_for_ref_manager(self, characters: dict) -> List[dict]:
        """
        转换角色数据格式，适配ReferenceImageManager

        Phase 2.0 characters 格式 → ReferenceImageManager 格式
        """
        result = []
        for char in characters.get("characters", []):
            # 构建description
            physical = char.get("physical", {})
            clothing = char.get("clothing", {})

            desc_parts = []

            # 基本信息
            gender = char.get("gender", "")
            age = char.get("age_appearance", "adult")
            if gender:
                desc_parts.append(f"{gender}, {age}")

            # 外貌
            if physical:
                hair = f"{physical.get('hair_color', '')} {physical.get('hair_style', '')}".strip()
                if hair:
                    desc_parts.append(f"{hair} hair")

                eye = physical.get('eye_color', '')
                if eye:
                    desc_parts.append(f"{eye} eyes")

                skin = physical.get('skin_tone', '')
                if skin:
                    desc_parts.append(f"{skin} skin")

                face = physical.get('face_shape', '')
                if face:
                    desc_parts.append(f"{face} face")

            # 服装
            if clothing:
                top = clothing.get('top', '')
                if top:
                    desc_parts.append(f"wearing {top}")

                bottom = clothing.get('bottom', '')
                if bottom:
                    desc_parts.append(bottom)

            description = ", ".join(desc_parts) if desc_parts else "character"

            result.append({
                "id": char.get("id", ""),
                "name": char.get("name", ""),
                "name_en": char.get("name_en", ""),
                "description": description,
                "type": char.get("type", "human"),
                "gender": gender,
                "age_appearance": age,
                "physical": physical,
                "clothing": clothing
            })

        return result


# 便捷函数
async def run_phase2_pipeline(
    idea: str,
    style_preset: str = "anime",
    target_duration_minutes: int = 3,
    output_dir: str = "./test_output/manualtest/phase2",
    generate_images: bool = True
) -> dict:
    """
    便捷函数：运行Phase 2.0完整流程

    Args:
        idea: 用户创意
        style_preset: 风格预设
        target_duration_minutes: 目标时长
        output_dir: 输出目录
        generate_images: 是否生成图像

    Returns:
        生成结果
    """
    orchestrator = Phase2PipelineOrchestrator(output_dir=output_dir)
    return await orchestrator.run(
        idea=idea,
        style_preset=style_preset,
        target_duration_minutes=target_duration_minutes,
        generate_images=generate_images
    )
