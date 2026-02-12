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


class Phase2PipelineOrchestrator:
    """
    Phase 2.0 完整生成流程编排器

    使用方法：
    ```python
    orchestrator = Phase2PipelineOrchestrator(output_dir="./output")
    result = await orchestrator.run(
        idea="雨夜公交站，错过末班车的三个人",
        style_preset="realistic",
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

        # 状态跟踪
        self.current_stage = None
        self.stage_results = {}

    async def run(
        self,
        idea: str,
        style_preset: str = "realistic",
        target_duration_minutes: int = 3,
        language: str = "zh-CN",
        character_count: int = 3,
        generate_images: bool = True,
        max_concurrent_images: int = 2,
        shots_limit: int = 0
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

            outline = await self.outline_generator.generate(
                idea=idea,
                style_preset=style_preset,
                target_duration_minutes=target_duration_minutes,
                language=language,
                character_count=character_count
            )

            self.stage_results["outline"] = outline
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

            screenplay = await self.screenplay_writer.write(outline, characters)

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
                style_preset=style_preset
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
                refs_dir = os.path.join(project_dir, "refs")
                os.makedirs(images_dir, exist_ok=True)
                os.makedirs(refs_dir, exist_ok=True)

                # 5a. 生成角色参考图
                print("\n--- 5a. 生成角色参考图 ---")
                ref_manager = ReferenceImageManager()

                # 创建风格配置
                project_style = ProjectStyleConfig(style_preset=style_preset)

                # 为每个角色生成参考图
                char_list = characters.get("characters", [])
                for char in char_list:
                    char_name = char.get("name", char.get("id", "unknown"))
                    print(f"  生成 {char_name} 参考图...", end=" ")
                    try:
                        await ref_manager.generate_character_multi_refs(
                            character=char,
                            project_style=project_style,
                            image_generator=self.image_generator
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

                    try:
                        scene_anchors = await scene_ref_manager.generate_anchor_images(
                            scenes=[],  # Phase 2.0 直接用 unique_locations
                            project_style=project_style,
                            image_generator=self.image_generator,
                            unique_locations=unique_locations,
                            delay=3.0
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

                previous_shot_image = None
                previous_shot = None

                for i, shot in enumerate(shots):
                    shot_id = shot.get("shot_id", i + 1)
                    print(f"\n  生成 Shot {shot_id}/{len(shots)}...")

                    # 获取角色参考图 - 从character_direction.characters_visible读取
                    char_direction = shot.get("character_direction", {})
                    chars_in_scene = char_direction.get("characters_visible", [])
                    char_refs = ref_manager.get_references_for_scene(chars_in_scene)

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

                    # 使用Phase 2.0增强生成
                    result = await self.image_generator.generate_shot_image_phase2(
                        shot=shot,
                        storyboard=storyboard,
                        characters=characters,
                        style_preset=style_preset,
                        reference_images=all_refs,  # 合并后的参考图
                        previous_shot_image=previous_shot_image,
                        previous_shot=previous_shot,
                        screenplay=screenplay,  # 传入screenplay用于获取场景氛围
                        aspect_ratio="16:9"
                    )

                    if result.get("success"):
                        # 保存图像
                        image_path = os.path.join(images_dir, f"shot_{shot_id:02d}.png")
                        result["pil_image"].save(image_path)

                        # 更新前序shot信息（用于下一shot的连续性）
                        previous_shot_image = result["pil_image"]
                        previous_shot = shot  # 传递完整shot数据

                        image_results.append({
                            "shot_id": shot_id,
                            "success": True,
                            "image_path": image_path,
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

            # 检查关键元素
            checks = {
                "镜头信息 (shot/angle)": any(k in prompt.lower() for k in ["shot", "angle"]),
                "光线描述 (light/shadow)": any(k in prompt.lower() for k in ["light", "shadow", "lighting"]),
                "角色外观 (wearing/expression)": any(k in prompt.lower() for k in ["wearing", "expression", "hair"]),
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
    style_preset: str = "realistic",
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
