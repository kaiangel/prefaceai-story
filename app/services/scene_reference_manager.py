"""
场景参考图管理器 (P2.0 精简版)

管理场景/环境的锚点参考图，确保同一场景在不同镜头中的视觉一致性

P2.0核心原则：
- 只为每种场景类型生成1张锚点图（interior + exterior）
- 差异化由 ShotPromptGenerator 在 shots 阶段处理
- 时间/光线差异通过 shot prompt 描述，不需要多张锚点
"""

import asyncio
import re
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

from app.models.style_config import ProjectStyleConfig
from app.services.style_enforcer import StyleEnforcer


def _label_scene_image(image: Image.Image, label: str) -> Image.Image:
    """
    SQ-1: 在场景参考图左上角叠加场景标签（半透明黑底+白字）
    返回标注后的副本，不修改原图
    """
    labeled = image.copy().convert("RGBA")
    overlay = Image.new("RGBA", labeled.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(20, image.width // 20)
    font = None
    for font_path in [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (OSError, IOError):
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    padding = 8

    draw.rectangle(
        [4, 4, text_w + padding * 2 + 4, text_h + padding * 2 + 4],
        fill=(0, 0, 0, 180)
    )
    draw.text((padding + 4, padding + 4), label, fill=(255, 255, 255), font=font)

    labeled = Image.alpha_composite(labeled, overlay)
    return labeled.convert("RGB")


class SceneReferenceManager:
    """
    场景参考图管理器 (P2.0)

    为故事中的场景生成锚点参考图，确保环境一致性
    锚点图只有2张：interior_anchor 和 exterior_anchor
    """

    def __init__(self):
        self.scene_references: Dict[str, Dict[str, Image.Image]] = {}
        self.anchor_descriptions: Dict[str, str] = {}
        self.location_names: Dict[str, str] = {}  # SQ-1: {location_id: location_name}

    # ========== 场景分析方法 ==========

    def extract_unique_locations(self, scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从故事场景中提取独特的场景位置

        Args:
            scenes: 故事场景列表

        Returns:
            独特场景位置列表
        """
        seen_locations = {}
        locations = []

        for scene in scenes:
            location_name = (
                scene.get('location', '') or
                scene.get('setting', '') or
                scene.get('location_name', '')
            )

            if not location_name:
                continue

            location_id = self._normalize_location_id(location_name)

            if location_id not in seen_locations:
                location_info = {
                    'id': location_id,
                    'name': location_name,
                    'description': scene.get('location_description', ''),
                    'type': self._infer_location_type(location_name, scene),
                }
                seen_locations[location_id] = location_info
                locations.append(location_info)

        return locations

    def _normalize_location_id(self, location_name: str) -> str:
        """
        将场景名称标准化为ID，提取核心场所名称

        例如：
        - "24小时便利店，收银台附近" → "convenience_store"
        - "便利店饮料区，咖啡货架前" → "convenience_store"
        - "便利店门口" → "convenience_store"
        - "咖啡厅室内，靠窗位置" → "coffee_shop"
        - "翠竹林深处" → "bamboo_forest"
        """
        name_lower = location_name.lower()

        # 核心场所关键词映射 - 提取主要场景
        location_patterns = [
            # 中文场所
            (r'便利店', 'convenience_store'),
            (r'咖啡厅|咖啡店|咖啡馆', 'coffee_shop'),
            (r'公寓|住宅|卧室|客厅', 'apartment'),
            (r'街道|街边|马路|人行道', 'street'),
            (r'竹林', 'bamboo_forest'),
            (r'客栈', 'inn'),
            (r'山洞|洞穴', 'cave'),
            (r'山巅|山顶|山峰', 'mountain_peak'),
            (r'飞船|宇宙飞船|太空船', 'spaceship'),
            (r'基地|殖民地', 'colony_base'),
            (r'异星|外星|星球', 'alien_planet'),
            (r'办公室|写字楼', 'office'),
            (r'餐厅|饭店', 'restaurant'),
            (r'酒吧|夜店', 'bar'),
            (r'医院|诊所', 'hospital'),
            (r'学校|教室|校园', 'school'),
            (r'公园|花园', 'park'),
            (r'森林|树林', 'forest'),
            (r'海边|海滩|沙滩', 'beach'),
            (r'房间|室内', 'room'),
            # 英文场所
            (r'convenience store', 'convenience_store'),
            (r'coffee shop|cafe|coffee', 'coffee_shop'),
            (r'apartment|home|house', 'apartment'),
            (r'street|road|sidewalk', 'street'),
            (r'bamboo forest', 'bamboo_forest'),
            (r'inn|hotel', 'inn'),
            (r'cave', 'cave'),
            (r'spaceship|spacecraft', 'spaceship'),
            (r'colony|base', 'colony_base'),
            (r'alien|planet', 'alien_planet'),
        ]

        # 按顺序匹配，返回第一个匹配的场所ID
        for pattern, location_id in location_patterns:
            if re.search(pattern, name_lower):
                return location_id

        # 未匹配到已知场所，使用简化的名称
        # 去掉逗号后的修饰语，只保留主要场所
        main_part = re.split(r'[,，、]', location_name)[0].strip()
        normalized = re.sub(r'[^\w\s]', '', main_part.lower())
        normalized = re.sub(r'\s+', '_', normalized.strip())
        return normalized or 'unknown_location'

    def _infer_location_type(self, location_name: str, scene: Dict[str, Any]) -> str:
        """
        推断场景类型

        优先级：明确外景 > 明确内景 > 自然场景(只有exterior) > 默认both
        """
        name_lower = location_name.lower()

        # 明确的外景关键词
        explicit_exterior = ['外观', '门口', '门外', '台阶', '停车场', '街道', '街边',
                            '边缘', '地表', '荒漠',
                            'exterior', 'outside', 'outdoor', 'entrance', 'steps', 'parking']
        for keyword in explicit_exterior:
            if keyword in name_lower:
                return 'exterior'

        # 明确的内景关键词
        explicit_interior = ['店内', '室内', '房间', '柜台', '货架', '咖啡区', '收银台',
                            '大堂', '内部', '舱内', '驾驶舱', '卧室', '客厅',
                            'inside', 'interior', 'room', 'counter', 'aisle', 'checkout',
                            'cabin', 'cockpit', 'chamber', 'hall']
        for keyword in explicit_interior:
            if keyword in name_lower:
                return 'interior'

        # 自然场景 - 只有exterior（户外场景本身就是exterior）
        natural_exterior_only = ['竹林', '树林', '森林', '山顶', '山巅', '山峰', '海边', '沙滩',
                                 '草原', '荒野', '田野', '湖边', '河边',
                                 'forest', 'mountain', 'beach', 'field', 'lake', 'river', 'wilderness']
        for keyword in natural_exterior_only:
            if keyword in name_lower:
                return 'exterior'

        # 封闭场景 - 只有interior（山洞、舱室等）
        enclosed_interior_only = ['山洞', '洞穴', '地下', '隧道', '舱室', '船舱',
                                  'cave', 'tunnel', 'underground', 'cabin']
        for keyword in enclosed_interior_only:
            if keyword in name_lower:
                return 'interior'

        # 模糊关键词 - 生成both（可能有内外景的建筑）
        ambiguous_keywords = ['店', '栈', '酒店', '房', '基地', 'store', 'shop', 'hall', 'office', 'inn', 'hotel', 'base']
        for keyword in ambiguous_keywords:
            if keyword in name_lower:
                return 'both'

        return 'both'

    def _clean_location_name(self, location_name: str) -> str:
        """清洗location名称，移除或翻译中文"""
        translations = {
            '便利店': 'convenience store',
            '收银台': 'checkout counter',
            '咖啡区': 'coffee section',
            '饮料区': 'beverage section',
            '货架': 'shelves',
            '门口': 'entrance',
            '外观': 'exterior',
            '室内': 'interior',
            '店内': 'inside the store',
            '凌晨': 'early morning',
            '深夜': 'late night',
            '荧光灯': 'fluorescent light',
        }

        result = location_name
        for cn, en in translations.items():
            result = result.replace(cn, en)

        # 移除剩余的中文字符
        result = re.sub(r'[\u4e00-\u9fff]+', '', result)
        result = re.sub(r'\s+', ' ', result).strip()
        return result

    def _get_location_negative_prompt(self) -> str:
        """获取场景生成的negative prompt"""
        return "people, humans, characters, animals, text, watermark, logo, signature, blurry, low quality"

    # ========== 引用存取方法 ==========

    def set_reference(self, location_id: str, view_type: str, image: Image.Image):
        """设置场景参考图"""
        if location_id not in self.scene_references:
            self.scene_references[location_id] = {}
        self.scene_references[location_id][view_type] = image

    def get_reference(self, location_id: str, view_type: str) -> Optional[Image.Image]:
        """获取特定视角的场景参考图"""
        if location_id in self.scene_references:
            return self.scene_references[location_id].get(view_type)
        return None

    def get_references_for_location(self, location_id: str) -> List[Image.Image]:
        """获取指定场景的所有参考图（T11: 返回无标签原图，避免 Gemini 复现标签文字）"""
        if location_id not in self.scene_references:
            return []

        refs = []
        for view_type, image in self.scene_references[location_id].items():
            # T11: 移除 _label_scene_image() 调用，直接返回原图
            # 原因: PIL 标签被 Gemini 在生成图中复现（3/20 泄露）
            refs.append(image)
        return refs

    def has_reference(self, location_id: str) -> bool:
        """检查是否存在某场景的参考图"""
        return location_id in self.scene_references and len(self.scene_references[location_id]) > 0

    def clear_references(self):
        """清空所有参考图"""
        self.scene_references.clear()
        self.anchor_descriptions.clear()

    # ========== P2.0 锚点图生成方法 ==========

    async def generate_anchor_images(
        self,
        scenes: List[Dict[str, Any]],
        project_style: ProjectStyleConfig,
        image_generator,
        unique_locations: List[Dict[str, Any]] = None,
        delay: float = 3.0,
        location_character_counts: Dict[str, int] = None,
        seed_images: Dict[str, "Image.Image"] = None,
        aspect_ratio: str = "2:3",
        # T21-NEW-6 (2026-05-21): sub-stage progress callback for frontend stage_message 细化
        # 每个 view (interior/exterior) 完成时回调: (stage, progress_pct, message)
        # 用于 Stage 4.5 scene_image_preparation 细化 "生成场景参考图 (interior 1/4: 客厅)..."
        sub_progress_callback=None,
        sub_progress_stage_name: str = "scene_image_preparation",
        sub_progress_base_pct: int = 60,
        sub_progress_max_pct: int = 63,
    ) -> Dict[str, Dict[str, Any]]:
        """
        P2.0核心方法：为每种场景类型生成锚点图

        🚨 内外景关联优化（2025-12-23）：
        - 同一location先生成内景，再生成外景
        - 生成外景时，把内景作为参考图传入
        - 确保内外景视觉风格一致

        Args:
            scenes: 故事场景列表
            project_style: 项目风格配置
            image_generator: 图片生成器实例
            unique_locations: 结构化场景列表（新格式，可选）
            delay: 请求间隔（秒）

        Returns:
            {
                "location_id_interior_anchor": {"image": Image, "description": str},
                "location_id_exterior_anchor": {"image": Image, "description": str},
                ...
            }
        """
        print("  [SceneRefManager] P2.0锚点图生成模式（内外景关联）")

        # 1. 分析需要哪些锚点（支持新旧格式）
        anchor_needs = self._analyze_anchor_needs(scenes, unique_locations)
        print(f"  需要生成 {len(anchor_needs)} 张锚点图: {list(anchor_needs.keys())}")

        results = {}
        results_lock = asyncio.Lock()  # 保护并行写入 results dict

        # 2. 按location_id分组，确保内景先于外景生成
        location_groups = self._group_anchors_by_location(anchor_needs)

        # RISK-T14-10 (DEC-029): 跨 location 并行生成（Semaphore 3 路并发）
        # 同一 location 内 interior → exterior 仍串行（exterior 依赖 interior 作参考）
        _loc_sem = asyncio.Semaphore(3)

        # T21-NEW-6: 计算所有 view total (interior + exterior 各 1, 不一定全有)
        _total_views = sum(
            (1 if f"{loc_id}_interior_anchor" in anchors else 0) +
            (1 if f"{loc_id}_exterior_anchor" in anchors else 0)
            for loc_id, anchors in location_groups.items()
        )
        _completed_views = [0]  # mutable counter for sub-progress
        _completed_lock = asyncio.Lock()

        async def _emit_sub_progress(view_label: str, location_zh: str):
            """T21-NEW-6: 单 view 完成后回调 sub-stage progress 细化"""
            if sub_progress_callback is None:
                return
            try:
                async with _completed_lock:
                    _completed_views[0] += 1
                    _done = _completed_views[0]
                _pct_range = max(sub_progress_max_pct - sub_progress_base_pct, 1)
                _pct = sub_progress_base_pct + int(_pct_range * _done / max(_total_views, 1))
                _msg = (
                    f"生成场景参考图 ({view_label} {_done}/{_total_views}: {location_zh})..."
                )
                await sub_progress_callback(sub_progress_stage_name, _pct, _msg)
            except Exception as _cb_e:
                print(f"  [SceneRefManager] sub_progress_callback 失败（非阻塞）: {_cb_e}")

        async def _gen_one_location(location_id: str, anchors: dict):
            """单 location 的内外景生成（interior→exterior 串行，保留参考关系）"""
            interior_image = None
            # T21: 获取该场景的角色数量
            loc_num_chars = (location_character_counts or {}).get(location_id)
            # T21-NEW-6: 中文 location 名(优先 display_name, 回退 location_id)
            _loc_zh = location_id
            for _ak, _ai in anchors.items():
                if _ai.get('location_name'):
                    _loc_zh = _ai['location_name']
                    break

            # 3.1 先生成内景（如果有）
            interior_key = f"{location_id}_interior_anchor"
            if interior_key in anchors:
                anchor_info = anchors[interior_key]
                print(f"  生成锚点图: {interior_key}...")

                # seed_image: 用户上传的场景参考图（如有）
                scene_seed = (seed_images or {}).get(location_id)
                async with _loc_sem:
                    interior_image, interior_result = await self._generate_single_anchor(
                        anchor_key=interior_key,
                        anchor_info=anchor_info,
                        view_type='interior',
                        project_style=project_style,
                        image_generator=image_generator,
                        reference_image=scene_seed,  # 用户 seed 图或 None
                        location_id=location_id,  # 传入原始location_id用于存储
                        num_characters=loc_num_chars,  # T21: 角色数量
                        aspect_ratio=aspect_ratio,
                    )
                async with results_lock:
                    results[interior_key] = interior_result
                # T21-NEW-6: 细化 sub-stage progress
                await _emit_sub_progress("interior", _loc_zh)

            # 3.2 再生成外景（如果有），把内景作为参考图
            exterior_key = f"{location_id}_exterior_anchor"
            if exterior_key in anchors:
                anchor_info = anchors[exterior_key]

                if interior_image:
                    print(f"  生成锚点图: {exterior_key}（使用内景作为参考）...")
                else:
                    print(f"  生成锚点图: {exterior_key}...")

                async with _loc_sem:
                    _, exterior_result = await self._generate_single_anchor(
                        anchor_key=exterior_key,
                        anchor_info=anchor_info,
                        view_type='exterior',
                        project_style=project_style,
                        image_generator=image_generator,
                        reference_image=interior_image,  # 关键：内景作为参考
                        location_id=location_id,  # 传入原始location_id用于存储
                        num_characters=loc_num_chars,  # T21: 角色数量
                        aspect_ratio=aspect_ratio,
                    )
                async with results_lock:
                    results[exterior_key] = exterior_result
                # T21-NEW-6: 细化 sub-stage progress
                await _emit_sub_progress("exterior", _loc_zh)

        # 并行执行所有 location（location 内部 interior→exterior 串行保持）
        await asyncio.gather(
            *[_gen_one_location(loc_id, anchors) for loc_id, anchors in location_groups.items()],
            return_exceptions=True,
        )

        return results

    def _group_anchors_by_location(
        self,
        anchor_needs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        按location_id分组锚点需求

        Returns:
            {
                "location_id_1": {
                    "location_id_1_interior_anchor": {...},
                    "location_id_1_exterior_anchor": {...}
                },
                ...
            }
        """
        groups = {}

        for anchor_key, anchor_info in anchor_needs.items():
            location_id = anchor_info.get('location_id', '')
            if not location_id:
                # 从anchor_key中提取location_id
                # 格式: {location_id}_{view_type}_anchor
                parts = anchor_key.rsplit('_', 2)
                if len(parts) >= 3:
                    location_id = parts[0]
                else:
                    location_id = anchor_key

            if location_id not in groups:
                groups[location_id] = {}

            groups[location_id][anchor_key] = anchor_info

        return groups

    async def _generate_single_anchor(
        self,
        anchor_key: str,
        anchor_info: Dict[str, Any],
        view_type: str,
        project_style: ProjectStyleConfig,
        image_generator,
        reference_image: Optional[Image.Image] = None,
        location_id: str = None,
        num_characters: int = None,
        aspect_ratio: str = "2:3",
    ) -> tuple:
        """
        生成单个锚点图

        Args:
            anchor_key: 锚点键名
            anchor_info: 锚点信息
            view_type: "interior" 或 "exterior"
            project_style: 项目风格
            image_generator: 图片生成器
            reference_image: 参考图（外景时传入内景图）
            location_id: 原始location_id（用于scene_references存储）

        Returns:
            (pil_image, result_dict)
        """
        representative_scene = anchor_info.get('representative_scene') or {}

        # 构建锚点图的location信息
        location_info = {
            'id': anchor_key,
            'name': anchor_info.get('location_name', '') or representative_scene.get('location', ''),
            'description': anchor_info.get('description', '') or representative_scene.get('location_description', ''),
            'type': view_type,
            'time_of_day': anchor_info.get('time_of_day', ''),
            'atmosphere': representative_scene.get('mood', ''),
            'lighting': representative_scene.get('scene_style', {}).get('lighting', ''),
            'key_visual_elements': anchor_info.get('key_visual_elements', []),
            'signage_text': anchor_info.get('signage_text', ''),
        }

        # 构建锚点图prompt（外景时添加内景一致性指令）
        prompt = self._build_anchor_prompt(
            location_info,
            view_type,
            project_style,
            has_interior_reference=(reference_image is not None),
            num_characters=num_characters
        )
        negative_prompt = self._get_location_negative_prompt()

        # 准备参考图列表
        reference_images = [reference_image] if reference_image else None

        # 生成图片（使用Flash模型，场景图不需要Pro）
        result = await image_generator.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,  # D.15: 由 pipeline 传入 project.aspect_ratio
            reference_images=reference_images
            # 不传use_pro_model，默认使用Flash
        )

        # L2: CONTENT_SAFETY 简化重试
        if not result.get('success') and result.get('error_type') == 'content_safety':
            print(f"    ⚠️ {anchor_key} CONTENT_SAFETY → 简化 prompt 重试")
            simplified_prompt = self._simplify_anchor_prompt(prompt)
            result = await image_generator.generate_image(
                prompt=simplified_prompt,
                negative_prompt=negative_prompt,
                aspect_ratio=aspect_ratio,
                reference_images=reference_images
            )

        # L3a: 简化重试仍失败 → PromptRewriter 改写重试
        if not result.get('success') and result.get('error_type') == 'content_safety':
            print(f"    ⚠️ {anchor_key} 简化仍失败 → PromptRewriter 改写重试")
            try:
                from app.services.prompt_rewriter import get_rewriter
                rewriter = get_rewriter()
                rewritten = await rewriter.rewrite_scene_ref(prompt)
                if rewritten:
                    result = await image_generator.generate_image(
                        prompt=rewritten,
                        negative_prompt=negative_prompt,
                        aspect_ratio=aspect_ratio,
                        reference_images=reference_images
                    )
            except Exception as rw_err:
                print(f"    ⚠️ PromptRewriter 改写异常: {rw_err}")

        pil_image = None

        if result.get('success') and result.get('pil_image'):
            pil_image = result['pil_image']

            # 保存到 scene_references（使用原始location_id作为key，以便后续查找）
            storage_key = location_id if location_id else anchor_key
            self.set_reference(storage_key, view_type, pil_image)

            # SQ-1: 存储 location_name 用于标注
            loc_name = anchor_info.get('location_name', '') or representative_scene.get('location', '')
            if storage_key and loc_name:
                self.location_names[storage_key] = loc_name

            # 构建描述
            description = self._build_anchor_description(location_info, view_type)
            self.anchor_descriptions[anchor_key] = description

            result_dict = {
                'image': pil_image,
                'view_type': view_type,
                'description': description,
                'representative_scene_id': representative_scene.get('scene_id'),
                'used_interior_reference': reference_image is not None
            }
            ref_note = "（使用内景参考）" if reference_image else ""
            print(f"    ✅ {anchor_key} 锚点图生成成功{ref_note}")
        else:
            result_dict = {'error': result.get('error')}
            print(f"    ❌ {anchor_key} 锚点图生成失败: {result.get('error')}")

        return pil_image, result_dict

    def _analyze_anchor_needs(
        self,
        scenes: List[Dict[str, Any]],
        unique_locations: List[Dict[str, Any]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        分析锚点需求

        优先使用story.json中的unique_locations（新格式）
        如果没有，回退到规则匹配（兼容旧格式）

        Args:
            scenes: 场景列表
            unique_locations: 结构化场景列表（新格式，可选）

        Returns:
            {
                "convenience_store_interior_anchor": {...},
                "convenience_store_exterior_anchor": {...},
                ...
            }
        """
        # 新格式：直接使用unique_locations
        if unique_locations:
            print("  [SceneRefManager] ✅ 使用结构化unique_locations")
            return self._analyze_anchor_needs_from_structured(scenes, unique_locations)

        # 旧格式：回退到规则匹配（临时保留，待StoryGenerator稳定后删除）
        print("  [SceneRefManager] ⚠️ 警告: 未找到unique_locations，使用规则匹配fallback")
        print("  [SceneRefManager] ⚠️ 这表示StoryGenerator未输出unique_locations，请检查story_generation.py的prompt")
        return self._analyze_anchor_needs_by_rules(scenes)

    def _analyze_anchor_needs_from_structured(
        self,
        scenes: List[Dict[str, Any]],
        unique_locations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        从结构化unique_locations分析锚点需求（新格式）
        """
        needs = {}

        for loc in unique_locations:
            location_id = loc.get('location_id', '')
            if not location_id:
                continue

            location_type = loc.get('location_type', 'both')
            display_name = loc.get('display_name', location_id)
            interior_desc = loc.get('interior_description', '')
            exterior_desc = loc.get('exterior_description', '')
            key_elements = loc.get('key_visual_elements', [])

            # 根据location_type确定需要哪些锚点
            # 支持多种命名：interior/interior_only, exterior/exterior_only, both
            if location_type in ['interior', 'interior_only', 'both']:
                anchor_key = f"{location_id}_interior_anchor"
                needs[anchor_key] = {
                    'view_type': 'interior',
                    'location_id': location_id,
                    'location_name': display_name,
                    'description': interior_desc,
                    'key_visual_elements': key_elements,
                    'representative_scene': self._find_representative_scene(
                        scenes, location_id, 'interior'
                    ),
                    'time_of_day': '',
                    'signage_text': loc.get('signage_text', '')
                }

            if location_type in ['exterior', 'exterior_only', 'both']:
                anchor_key = f"{location_id}_exterior_anchor"
                needs[anchor_key] = {
                    'view_type': 'exterior',
                    'location_id': location_id,
                    'location_name': display_name,
                    'description': exterior_desc,
                    'key_visual_elements': key_elements,
                    'representative_scene': self._find_representative_scene(
                        scenes, location_id, 'exterior'
                    ),
                    'time_of_day': '',
                    'signage_text': loc.get('signage_text', '')
                }

        return needs

    def _find_representative_scene(
        self,
        scenes: List[Dict[str, Any]],
        location_id: str,
        view_type: str
    ) -> Optional[Dict[str, Any]]:
        """找到使用指定location的第一个scene作为代表"""
        for scene in scenes:
            # 新格式使用 location_ref
            if scene.get('location_ref') == location_id:
                location_type_used = scene.get('location_type_used', '')
                if location_type_used == view_type or not location_type_used:
                    return scene
        # 如果没找到，返回第一个scene
        return scenes[0] if scenes else None

    def _analyze_anchor_needs_by_rules(self, scenes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        通过规则匹配分析锚点需求（兼容旧格式story.json）

        ⚠️ 临时保留的fallback方法
        TODO: 待StoryGenerator稳定输出unique_locations后删除此方法

        规则：
        - 每个独特location生成1-2张锚点（interior/exterior）
        - 同一location的不同时间不生成额外锚点
        - 多场景故事会生成更多锚点
        """
        needs = {}
        seen_locations = {}  # {normalized_location: {'interior': scene, 'exterior': scene}}

        for scene in scenes:
            location_name = scene.get('location', '')
            if not location_name:
                continue

            location_id = self._normalize_location_id(location_name)
            location_type = self._infer_location_type(location_name, scene)

            if location_id not in seen_locations:
                seen_locations[location_id] = {
                    'name': location_name,  # 保留原始名称用于prompt
                }

            # 只记录每种类型的第一个场景（同一location不重复）
            if location_type in ['interior', 'both'] and 'interior' not in seen_locations[location_id]:
                seen_locations[location_id]['interior'] = scene
            if location_type in ['exterior', 'both'] and 'exterior' not in seen_locations[location_id]:
                seen_locations[location_id]['exterior'] = scene

        # 转换为needs格式
        for location_id, location_data in seen_locations.items():
            location_name = location_data.get('name', location_id)

            for view_type in ['interior', 'exterior']:
                if view_type in location_data:
                    scene = location_data[view_type]
                    anchor_key = f"{location_id}_{view_type}_anchor"
                    needs[anchor_key] = {
                        'view_type': view_type,
                        'representative_scene': scene,
                        'location_id': location_id,
                        'location_name': location_name,
                        'time_of_day': scene.get('scene_style', {}).get('time_of_day', '')
                    }

        return needs

    # T31: 含招牌/门面的场景关键词
    _SIGNAGE_KEYWORDS_ZH = {'铺', '店', '坊', '馆', '堂', '楼', '阁', '庄', '号', '行'}
    _SIGNAGE_KEYWORDS_EN = {
        'shop', 'store', 'restaurant', 'café', 'cafe', 'inn', 'tavern',
        'bakery', 'clinic', 'hospital', 'academy', 'studio', 'office',
        'bar', 'pub', 'diner', 'pharmacy', 'boutique', 'gallery',
        'tailor', 'workshop', 'mill', 'forge', 'smithy'
    }

    def _simplify_anchor_prompt(self, prompt: str) -> str:
        """L2: 简化场景参考图 prompt — 去掉人群/动物/活动描述，保留建筑/环境"""
        from app.prompts.prompt_safety_rewrite import apply_simple_replacements
        simplified = apply_simple_replacements(prompt)
        # 正则去除残留人物描述（apply_simple_replacements 可能漏掉的自由文本）
        simplified = re.sub(r'\b(people|persons|humans|men|women|children)\s+(are\s+)?\w+ing\b', '', simplified)
        # 确保 "No people" 在最前面（Gemini 可能在读到触发词时就过滤）
        prefix = "Architectural scene only. No people, no characters, no animals. "
        if not simplified.startswith(prefix):
            simplified = prefix + simplified
        return simplified

    def _detect_signage_name(self, location_name: str, location_desc: str,
                              signage_text: str = '') -> Optional[str]:
        """T-C: 信任 Stage 1 LLM 的 signage_text 决策。

        Stage 1 outline LLM 已经判断:
        - 该地点是否有招牌 (有招牌场所如客栈/店铺/柜台等)
        - 招牌名是什么 (简短名 e.g. "万象珠宝", 而非整段 location 描述)

        不再用 keyword fallback (e.g. 含"楼"字就误判为招牌场所), 因为:
        - keyword 易误判 (办公楼/教学楼/出租屋的"楼"不是招牌)
        - 即使该有招牌, 把整段 display_name 当招牌也是错的 (太长 + 含修饰词)
        - 信任 LLM 决策最 universal (任何故事类型不出错)

        修复历史: 2026-05-18 TASK-T20-FIXBATCH T20-3 P0 招牌污染 (test18 实证).
        """
        if signage_text:
            return signage_text
        return None

    def _build_anchor_prompt(
        self,
        location: Dict[str, Any],
        view_type: str,
        project_style: ProjectStyleConfig,
        has_interior_reference: bool = False,
        num_characters: int = None
    ) -> str:
        """
        构建高质量锚点图的prompt

        Args:
            location: 场景位置信息
            view_type: "interior" 或 "exterior"
            project_style: 项目风格配置
            has_interior_reference: 是否有内景参考图（外景生成时使用）

        优先使用新格式中的description，如果没有则回退到旧格式
        """
        location_name = location.get('name', '') or location.get('location_name', '')
        # 新格式：直接使用description字段（已经是英文）
        location_desc = location.get('description', '')
        time_of_day = location.get('time_of_day', '')
        atmosphere = location.get('atmosphere', '')
        lighting = location.get('lighting', '')
        key_elements = location.get('key_visual_elements', [])
        style_name = project_style.style_preset

        # 构建位置描述
        if location_desc:
            # 新格式：description已经是英文描述
            location_full_desc = location_desc
        else:
            # 旧格式：清洗location名称
            cleaned_location_name = self._clean_location_name(location_name)
            location_full_desc = cleaned_location_name

        # 构建关键视觉元素列表
        elements_str = ""
        if key_elements:
            elements_str = "\n\nKEY VISUAL ELEMENTS TO INCLUDE:\n- " + "\n- ".join(key_elements)

        # 时间和氛围
        context_parts = []
        if time_of_day:
            context_parts.append(time_of_day)
        if atmosphere:
            context_parts.append(f"{atmosphere} atmosphere")
        if lighting:
            context_parts.append(f"{lighting} lighting")
        context_desc = ", ".join(context_parts) if context_parts else ""

        if view_type == 'exterior':
            # 🚨 内外景关联：外景生成时添加内景一致性指令
            interior_consistency_section = ""
            if has_interior_reference:
                interior_consistency_section = """

INTERIOR-EXTERIOR CONSISTENCY (CRITICAL):
The reference image shows the interior of this location.
- Maintain the same overall style, color palette, and architectural details
- Any interior elements visible from outside (through entrances, openings, windows, or transparent surfaces) MUST match the reference
- The exterior should feel like it belongs to the same building/space as the interior
- Preserve the lighting mood and atmosphere from the interior reference"""

            # T31: 检测招牌名称并注入
            signage_section = ""
            signage_name = self._detect_signage_name(location_name, location_full_desc,
                                                         signage_text=location.get('signage_text', ''))
            if signage_name:
                signage_section = f"""
REQUIRED TEXT ON SIGNAGE (CRITICAL):
The storefront/building sign MUST display: "{signage_name}"
Do NOT invent or substitute any other name. The sign text must match EXACTLY."""

            core_prompt = f"""MASTER ANCHOR IMAGE - EXTERIOR
STRICT: No people, no characters, no animals, no moving objects.
This is a PURE ARCHITECTURAL/ENVIRONMENTAL scene.

This is the DEFINITIVE VISUAL REFERENCE for this location's exterior.
ALL subsequent shots will use this image as the visual foundation.

Location: {location_full_desc}
{elements_str}
{interior_consistency_section}
{signage_section}

REQUIREMENTS:
1. WIDE ESTABLISHING SHOT - capture the complete exterior
2. Clear view of all architectural and environmental details
3. High detail quality for all visual elements
4. Consistent lighting throughout the image
{f"Time/Atmosphere: {context_desc}" if context_desc else ""}

COMPOSITION:
- 3/4 angle view to show depth and dimension
- Main subject should fill 60-70% of frame
- Include surrounding context for depth

QUALITY: Highest detail, sharp focus, professional photography"""

        else:  # interior
            # T31: 检测招牌名称（室内也可能有墙面招牌/匾额）
            signage_section = ""
            signage_name = self._detect_signage_name(location_name, location_full_desc,
                                                         signage_text=location.get('signage_text', ''))
            if signage_name:
                signage_section = f"""
If any wall sign, plaque, or banner is visible inside, it MUST display: "{signage_name}"
Do NOT invent or substitute any other name."""

            core_prompt = f"""MASTER ANCHOR IMAGE - INTERIOR
STRICT: No people, no characters, no animals.
This is a PURE ARCHITECTURAL/ENVIRONMENTAL scene.

This is the DEFINITIVE VISUAL REFERENCE for this location's interior.
ALL subsequent shots will use this image as the visual foundation.

Location: {location_full_desc}
{elements_str}
{signage_section}

REQUIREMENTS:
1. WIDE INTERIOR SHOT - capture the complete indoor space layout
2. Clear view of: walls, floor, ceiling, furniture, fixtures
3. High detail quality for all visual elements
4. Consistent lighting throughout the image
{f"Time/Atmosphere: {context_desc}" if context_desc else ""}
{f"5. The space is arranged for {num_characters} people (e.g., {num_characters} seats, table set for {num_characters})" if num_characters else ""}

COMPOSITION:
- High angle (slightly elevated) to show spatial layout
- Interior should fill 80-90% of frame
- Show depth through the space

QUALITY: Highest detail, sharp focus, professional interior photography"""

        # 应用风格强制
        enforced_prompt = StyleEnforcer.enforce_prompt(
            core_prompt,
            style_name,
            add_quality_suffix=True
        )

        return enforced_prompt

    def _build_anchor_description(self, location: Dict[str, Any], view_type: str) -> str:
        """为锚点图构建描述文本，供ShotPromptGenerator使用"""
        location_name = location.get('name', '')
        time_of_day = location.get('time_of_day', '')
        atmosphere = location.get('atmosphere', '')
        lighting = location.get('lighting', '')

        parts = []

        if view_type == 'interior':
            parts.append(f"Interior of {location_name}")
            parts.append("Wide angle view showing complete indoor space")
        else:
            parts.append(f"Exterior of {location_name}")
            parts.append("Establishing shot showing building facade")

        if time_of_day:
            parts.append(f"Time: {time_of_day}")
        if lighting:
            parts.append(f"Lighting: {lighting}")
        if atmosphere:
            parts.append(f"Atmosphere: {atmosphere}")

        return ". ".join(parts)

    # ========== 锚点图获取方法 ==========

    def get_anchor_image(self, view_type: str, location_id: str = None) -> Optional[Image.Image]:
        """
        获取锚点图

        Args:
            view_type: "interior" 或 "exterior"
            location_id: 场景ID（可选，如果不提供则返回第一个匹配的）

        Returns:
            锚点图，不存在则返回None
        """
        # 如果指定了location_id，精确匹配
        if location_id:
            anchor_key = f"{location_id}_{view_type}_anchor"
            if anchor_key in self.scene_references:
                refs = self.scene_references[anchor_key]
                if view_type in refs:
                    return refs[view_type]

        # 否则返回第一个匹配view_type的锚点
        for key, refs in self.scene_references.items():
            if f"_{view_type}_anchor" in key and view_type in refs:
                return refs[view_type]

        return None

    def get_anchor_description(self, view_type: str, location_id: str = None) -> str:
        """获取锚点图的描述文本"""
        if location_id:
            anchor_key = f"{location_id}_{view_type}_anchor"
            if anchor_key in self.anchor_descriptions:
                return self.anchor_descriptions[anchor_key]

        # 返回第一个匹配的
        for key, desc in self.anchor_descriptions.items():
            if f"_{view_type}_anchor" in key:
                return desc

        return f"{view_type.capitalize()} anchor image"

    def get_all_anchor_keys(self) -> List[str]:
        """获取所有锚点的key列表"""
        return list(self.anchor_descriptions.keys())

    def save_all_references(self, output_dir: str) -> Dict[str, Dict[str, str]]:
        """
        保存所有参考图到指定目录

        Args:
            output_dir: 输出目录路径

        Returns:
            保存路径映射 {location_id: {view_type: filepath}}
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        saved_paths = {}

        for location_id, views in self.scene_references.items():
            saved_paths[location_id] = {}
            for view_type, image in views.items():
                filename = f"{location_id}_{view_type}.png"
                filepath = os.path.join(output_dir, filename)
                image.save(filepath)
                saved_paths[location_id][view_type] = filepath
                print(f"  💾 保存参考图: {filename}")

        return saved_paths


def create_scene_reference_manager() -> SceneReferenceManager:
    """创建SceneReferenceManager实例"""
    return SceneReferenceManager()
