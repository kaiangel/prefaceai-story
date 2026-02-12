"""
角色描述生成器 - 根据角色类型生成详细的图像prompt描述

支持 19 种角色类型：
- human, animal, fantasy_creature, robot, object, hybrid
- insect, aquatic, plant, mythological, supernatural, undead
- elemental, alien, vehicle_character, digital_virtual
- concept_personified, miniature, giant

核心原则：
1. 根据角色类型选择对应的描述模板
2. 包含所有关键视觉特征
3. 强调角色类型以防AI混淆
4. 输出格式统一：[CHARACTER: 名字] 详细描述
"""

from typing import Dict, Any, List, Optional
from app.models.character_types import CHARACTER_TYPE_DECLARATIONS, get_type_declaration


class CharacterPromptBuilder:
    """
    根据角色类型生成对应的图像prompt描述
    支持 19 种角色类型
    """

    # 类型到构建方法的映射
    TYPE_BUILDERS = {
        'human': '_build_human_description',
        'animal': '_build_animal_description',
        'fantasy_creature': '_build_fantasy_description',
        'robot': '_build_robot_description',
        'object': '_build_object_description',
        'hybrid': '_build_hybrid_description',
        'insect': '_build_insect_description',
        'aquatic': '_build_aquatic_description',
        'plant': '_build_plant_description',
        'mythological': '_build_mythological_description',
        'supernatural': '_build_supernatural_description',
        'undead': '_build_undead_description',
        'elemental': '_build_elemental_description',
        'alien': '_build_alien_description',
        'vehicle_character': '_build_vehicle_description',
        'digital_virtual': '_build_digital_description',
        'concept_personified': '_build_concept_description',
        'miniature': '_build_miniature_description',
        'giant': '_build_giant_description',
    }

    def build_character_prompt(self, character: Dict[str, Any]) -> str:
        """
        构建单个角色的完整描述
        自动检测角色类型并调用对应的构建方法
        """
        char_type = self._get_character_type(character)
        name = character.get('name', 'Unknown')
        name_en = character.get('name_en', '')

        # 获取对应的构建方法
        builder_name = self.TYPE_BUILDERS.get(char_type, '_build_generic_description')
        builder_method = getattr(self, builder_name, self._build_generic_description)
        desc = builder_method(character)

        # 统一格式
        name_str = f"{name} ({name_en})" if name_en else name
        return f"[CHARACTER: {name_str}] {desc}"

    def _get_character_type(self, character: Dict[str, Any]) -> str:
        """
        获取角色类型 - 只从 character_type 字段读取

        如果没有 character_type 字段，返回 'unknown' 并打印警告
        这会让错误的数据格式快速暴露，而不是静默fallback到可能错误的类型
        """
        char_type = character.get('character_type')
        if char_type:
            return char_type

        # 没有 character_type 字段，打印警告
        char_name = character.get('name', 'Unknown')
        print(f"  ⚠️ [CharacterPromptBuilder] 角色 '{char_name}' 缺少 character_type 字段，请检查 story.json")
        return 'unknown'

    # ================================================================
    # 基础类型构建方法
    # ================================================================

    def _build_human_description(self, character: Dict[str, Any]) -> str:
        """
        构建人类角色描述

        数据来源：
        1. human 字段 - gender, age_range, height, body_type
        2. physical 字段 - 外貌特征
        3. clothing 字段 - 服装信息
        """
        parts = []

        # 获取数据源
        human = character.get('human', {})
        physical = character.get('physical', {})
        clothing = character.get('clothing', {})

        # === 种族信息（最先声明，影响面部特征渲染）===
        ethnicity = physical.get('ethnicity', '')
        if ethnicity:
            parts.append(f"{ethnicity}")

        # === 基础信息（从 human 字段）===
        gender = human.get('gender', '')
        age = human.get('age_range', '')

        if age and gender:
            parts.append(f"A {age} {gender}")
        elif age:
            parts.append(f"A {age} person")
        elif gender:
            parts.append(f"A {gender}")

        # 身材信息（从 human 字段）
        height = human.get('height', '')
        build = human.get('body_type', '')
        if height and build:
            parts.append(f"{height} height, {build} build")
        elif build:
            parts.append(f"{build} build")

        # === 皮肤 ===
        skin_tone = physical.get('skin_tone', '')
        if skin_tone:
            parts.append(f"{skin_tone} skin")

        # === 面部特征 (FACE section) ===
        face_parts = []
        face_shape = physical.get('face_shape', '')
        eye_shape = physical.get('eye_shape', '')
        eye_color = physical.get('eye_color', '')
        eye_size = physical.get('eye_size', '')
        eyebrows = physical.get('eyebrows', '')
        nose = physical.get('nose', '')
        lips = physical.get('lips', '')

        if face_shape:
            face_parts.append(f"{face_shape} face shape")
        if eye_color or eye_shape:
            eye_desc_parts = [p for p in [eye_size, eye_shape, eye_color] if p]
            if eye_desc_parts:
                face_parts.append(f"{' '.join(eye_desc_parts)} eyes")
        if eyebrows:
            face_parts.append(f"{eyebrows} eyebrows")
        if nose:
            face_parts.append(f"{nose} nose")
        if lips:
            face_parts.append(f"{lips} lips")

        if face_parts:
            parts.append(f"FACE: {', '.join(face_parts)}")

        # === 发型 (HAIR section) ===
        hair_color = physical.get('hair_color', '')
        hair_style = physical.get('hair_style', '')
        hair_texture = physical.get('hair_texture', '')
        if hair_color or hair_style:
            hair_parts = [p for p in [hair_color, hair_texture, hair_style] if p]
            parts.append(f"HAIR: {' '.join(hair_parts)}")

        # === 服装 (CLOTHING section) ===
        clothing_parts = []
        top = clothing.get('top', '')
        bottom = clothing.get('bottom', '')
        footwear = clothing.get('footwear', '')
        accessories = clothing.get('accessories', [])
        style = clothing.get('style', '')

        if top:
            clothing_parts.append(top)
        if bottom:
            clothing_parts.append(bottom)
        if footwear:
            clothing_parts.append(footwear)

        if clothing_parts:
            parts.append(f"CLOTHING: {', '.join(clothing_parts)}")

        # 配饰
        if accessories:
            if isinstance(accessories, list):
                parts.append(f"ACCESSORIES: {', '.join(accessories[:4])}")  # 最多4个
            else:
                parts.append(f"ACCESSORIES: {accessories}")

        # 风格
        if style:
            parts.append(f"STYLE: {style}")

        # === 独特标记 ===
        distinctive_marks = physical.get('distinctive_marks', [])
        if distinctive_marks:
            if isinstance(distinctive_marks, list):
                parts.append(f"DISTINCTIVE MARKS: {', '.join(distinctive_marks)}")
            else:
                parts.append(f"DISTINCTIVE MARKS: {distinctive_marks}")

        # === 表情 ===
        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else "A human character"
        return f"{desc}. This is a HUMAN character."

    def build_face_description(self, character: Dict[str, Any]) -> str:
        """
        构建精确的面部特征描述 - 用于正面肖像参考图
        从 physical 字段读取数据
        """
        physical = character.get('physical', {})
        face_parts = []

        face_shape = physical.get('face_shape', '')
        eye_shape = physical.get('eye_shape', '')
        eye_color = physical.get('eye_color', '')
        eye_size = physical.get('eye_size', 'medium')
        nose = physical.get('nose', '')
        lips = physical.get('lips', '')
        eyebrows = physical.get('eyebrows', '')
        skin_tone = physical.get('skin_tone', '')

        if face_shape:
            face_parts.append(f"{face_shape} face shape")
        if eye_shape and eye_color:
            face_parts.append(f"{eye_size} {eye_shape} {eye_color} eyes")
        elif eye_color:
            face_parts.append(f"{eye_color} eyes")
        if eyebrows:
            face_parts.append(f"{eyebrows} eyebrows")
        if nose:
            face_parts.append(f"{nose} nose")
        if lips:
            face_parts.append(f"{lips} lips")
        if skin_tone:
            face_parts.append(f"{skin_tone} skin tone")

        return ", ".join(face_parts) if face_parts else ""

    def _build_animal_description(self, character: Dict[str, Any]) -> str:
        """构建动物角色描述"""
        a = character.get('animal', {})
        parts = []

        species = a.get('species', '')
        breed = a.get('breed', '') or species
        fur_color = a.get('fur_color', '')
        fur_pattern = a.get('fur_pattern', '')
        fur_length = a.get('fur_length', '')
        fur_texture = a.get('fur_texture', '')
        body_size = a.get('body_size', '')
        body_shape = a.get('body_shape', '')
        eye_color = a.get('eye_color', '')
        eye_shape = a.get('eye_shape', '')
        nose_color = a.get('nose_color', '')
        ear_shape = a.get('ear_shape', '')
        tail = a.get('tail', '')

        # 基础描述
        size_shape = f"{body_size}, {body_shape}" if body_size and body_shape else body_size or body_shape
        if size_shape and breed:
            parts.append(f"A {size_shape} {breed}")
        elif breed:
            parts.append(f"A {breed}")
        elif species:
            parts.append(f"A {species}")

        # 毛发/羽毛外观
        fur_parts = []
        if fur_length:
            fur_parts.append(fur_length)
        if fur_texture:
            fur_parts.append(fur_texture)
        if fur_color:
            fur_parts.append(fur_color)
        if fur_parts:
            # 根据species选择fur或feathers
            bird_species = ['bird', 'sparrow', 'eagle', 'hawk', 'parrot', 'owl', 'penguin', 'chicken']
            material = "feathers" if species and species.lower() in bird_species else "fur"
            parts.append(f"with {' '.join(fur_parts)} {material}")

        if fur_pattern:
            parts.append(f"featuring {fur_pattern} pattern")

        # 眼睛
        if eye_color:
            eye_desc = f"{eye_shape} {eye_color} eyes" if eye_shape else f"{eye_color} eyes"
            parts.append(eye_desc)

        # 鼻子
        if nose_color:
            parts.append(f"{nose_color} nose/beak")

        # 耳朵
        if ear_shape:
            parts.append(f"{ear_shape} ears")

        # 尾巴
        if tail:
            parts.append(f"{tail} tail")

        # 独特标记
        marks = a.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        # 表情
        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        # 额外细节
        extra = character.get('extra_details', '')
        if extra:
            parts.append(f"Additional details: {extra}")

        desc = ", ".join(parts) if parts else f"A {breed or species or 'animal'}"
        return f"{desc}. This is an ANIMAL character, NOT a human."

    def _build_fantasy_description(self, character: Dict[str, Any]) -> str:
        """构建奇幻生物描述"""
        f = character.get('fantasy_creature', {})
        parts = []

        creature_type = f.get('creature_type', '')
        base_form = f.get('base_form', '')
        color_scheme = f.get('color_scheme', '')
        skin_texture = f.get('skin_texture', '')
        size = f.get('size_category', '')

        if creature_type and base_form:
            parts.append(f"A {size} {creature_type}, {base_form}" if size else f"A {creature_type}, {base_form}")
        elif creature_type:
            parts.append(f"A {size} {creature_type}" if size else f"A {creature_type}")

        if color_scheme:
            parts.append(f"{color_scheme} coloring")
        if skin_texture:
            parts.append(f"{skin_texture} texture")

        features = f.get('special_features', [])
        if features:
            parts.append(f"with {', '.join(features)}")

        marks = f.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else "A fantasy creature"
        return f"{desc}. This is a FANTASY CREATURE."

    def _build_robot_description(self, character: Dict[str, Any]) -> str:
        """构建机器人角色描述"""
        r = character.get('robot', {})
        parts = []

        robot_type = r.get('robot_type', '')
        material = r.get('material', '')
        color_scheme = r.get('color_scheme', '')
        size = r.get('size_category', '')
        era = r.get('era_style', '')
        body_shape = r.get('body_shape', '')

        if robot_type:
            type_parts = [p for p in [size, era, robot_type] if p]
            parts.append(f"A {' '.join(type_parts)} robot")

        if body_shape:
            parts.append(f"{body_shape} body")

        if material:
            parts.append(f"made of {material}")
        if color_scheme:
            parts.append(f"{color_scheme} color scheme")

        features = r.get('special_features', [])
        if features:
            parts.append(f"featuring {', '.join(features)}")

        desc = ", ".join(parts) if parts else "A robot"
        return f"{desc}. This is a ROBOT/MECHANICAL character."

    def _build_object_description(self, character: Dict[str, Any]) -> str:
        """构建拟人化物品描述"""
        o = character.get('object_personified', {})
        if not o and character.get('object'):
            print(f"⚠️ [COMPAT WARNING] 使用了旧字段 'object' 而非 'object_personified': {character.get('name', 'Unknown')}")
            o = character.get('object', {})
        parts = []

        object_type = o.get('object_type', '')
        base_object = o.get('base_object', '')
        material = o.get('material', '')
        color_scheme = o.get('color_scheme', '')
        face_location = o.get('face_location', '')
        limb_style = o.get('limb_style', '')
        size = o.get('size_category', '')

        if base_object:
            parts.append(f"A {size} personified {base_object}" if size else f"A personified {base_object}")
        elif object_type:
            parts.append(f"A personified {object_type}")

        if material:
            parts.append(f"made of {material}")
        if color_scheme:
            parts.append(f"{color_scheme} coloring")
        if face_location:
            parts.append(f"face on {face_location}")
        if limb_style:
            parts.append(f"{limb_style} limbs")

        features = o.get('distinctive_features', [])
        if features:
            parts.append(f"Distinctive features: {', '.join(features)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else "A personified object"
        return f"{desc}. This is a PERSONIFIED OBJECT with face and personality."

    def _build_hybrid_description(self, character: Dict[str, Any]) -> str:
        """构建混合类型描述"""
        h = character.get('hybrid', {})
        parts = []

        primary = h.get('primary_type', '')
        secondary = h.get('secondary_type', '')
        human_parts = h.get('human_parts', [])
        non_human_parts = h.get('non_human_parts', [])
        blend_style = h.get('blend_style', '')
        color_scheme = h.get('color_scheme', '')

        if primary and secondary:
            parts.append(f"A {primary}-{secondary} hybrid creature")
        elif primary:
            parts.append(f"A hybrid {primary} creature")

        if blend_style:
            parts.append(f"{blend_style} blend")

        if human_parts:
            parts.append(f"human parts: {', '.join(human_parts)}")
        if non_human_parts:
            parts.append(f"non-human parts: {', '.join(non_human_parts)}")

        if color_scheme:
            parts.append(f"{color_scheme} coloring")

        features = h.get('distinctive_features', [])
        if features:
            parts.append(f"Distinctive features: {', '.join(features)}")

        desc = ", ".join(parts) if parts else "A hybrid creature"
        return f"{desc}. This is a HYBRID character combining multiple forms."

    # ================================================================
    # 扩展类型构建方法
    # ================================================================

    def _build_insect_description(self, character: Dict[str, Any]) -> str:
        """构建昆虫角色描述"""
        i = character.get('insect', {})
        parts = []

        species = i.get('species', '')
        wing_type = i.get('wing_type', '')
        wing_pattern = i.get('wing_pattern', '')
        antennae = i.get('antennae', '')
        body_segments = i.get('body_segments', '')
        exoskeleton_color = i.get('exoskeleton_color', '')
        exoskeleton_pattern = i.get('exoskeleton_pattern', '')
        compound_eyes = i.get('compound_eyes', '')
        eye_color = i.get('eye_color', '')
        body_size = i.get('body_size', '')

        if species:
            parts.append(f"A {body_size} {species}" if body_size else f"A {species}")

        if exoskeleton_color:
            pattern_desc = f" with {exoskeleton_pattern}" if exoskeleton_pattern else ""
            parts.append(f"{exoskeleton_color} exoskeleton{pattern_desc}")

        if wing_type and wing_type != 'none':
            wing_desc = f"{wing_pattern} " if wing_pattern else ""
            parts.append(f"{wing_desc}{wing_type} wings")

        if antennae:
            parts.append(f"{antennae} antennae")

        if compound_eyes:
            eye_desc = f"{compound_eyes} {eye_color} compound eyes" if eye_color else f"{compound_eyes} compound eyes"
            parts.append(eye_desc)

        if body_segments:
            parts.append(f"{body_segments} body segments")

        features = i.get('special_features', [])
        if features:
            parts.append(f"with {', '.join(features)}")

        marks = i.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"An {species or 'insect'}"
        return f"{desc}. This is an INSECT character, NOT a human or mammal."

    def _build_aquatic_description(self, character: Dict[str, Any]) -> str:
        """构建水生生物描述"""
        a = character.get('aquatic', {})
        parts = []

        species = a.get('species', '')
        body_type = a.get('body_type', '')
        fin_type = a.get('fin_type', '')
        fin_color = a.get('fin_color', '')
        scale_pattern = a.get('scale_pattern', '')
        scale_color = a.get('scale_color', '')
        tentacles = a.get('tentacles', '')
        tail_shape = a.get('tail_shape', '')
        gills = a.get('gills', '')
        eye_type = a.get('eye_type', '')
        eye_color = a.get('eye_color', '')
        bioluminescence = a.get('bioluminescence', '')
        body_size = a.get('body_size', '')

        if species:
            parts.append(f"A {body_size} {body_type} {species}" if body_size and body_type else f"A {species}")

        if scale_color:
            pattern_desc = f" {scale_pattern}" if scale_pattern else ""
            parts.append(f"{scale_color}{pattern_desc} scales")

        if fin_type:
            fin_desc = f"{fin_color} " if fin_color else ""
            parts.append(f"{fin_desc}{fin_type} fins")

        if tentacles:
            parts.append(f"{tentacles} tentacles")

        if tail_shape:
            parts.append(f"{tail_shape} tail")

        if eye_type:
            eye_desc = f"{eye_type} {eye_color} eyes" if eye_color else f"{eye_type} eyes"
            parts.append(eye_desc)

        if gills and gills != 'hidden':
            parts.append(f"{gills} gills")

        if bioluminescence:
            parts.append(f"bioluminescent {bioluminescence}")

        marks = a.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"An aquatic {species or 'creature'}"
        return f"{desc}. This is an AQUATIC creature that lives in water."

    def _build_plant_description(self, character: Dict[str, Any]) -> str:
        """构建植物角色描述"""
        p = character.get('plant', {})
        parts = []

        plant_type = p.get('plant_type', '')
        species = p.get('species', '')
        leaf_shape = p.get('leaf_shape', '')
        leaf_color = p.get('leaf_color', '')
        flower_color = p.get('flower_color', '')
        flower_type = p.get('flower_type', '')
        bark_texture = p.get('bark_texture', '')
        bark_color = p.get('bark_color', '')
        root_visible = p.get('root_visible', False)
        root_style = p.get('root_style', '')
        face_location = p.get('face_location', '')
        limb_style = p.get('limb_style', '')
        height_category = p.get('height_category', '')
        seasonal_state = p.get('seasonal_state', '')

        if plant_type:
            parts.append(f"A {height_category} personified {species or plant_type}" if height_category else f"A personified {species or plant_type}")

        if leaf_color and leaf_shape:
            parts.append(f"{leaf_color} {leaf_shape} leaves")
        elif leaf_color:
            parts.append(f"{leaf_color} leaves")

        if flower_color:
            flower_desc = f"{flower_color} {flower_type}" if flower_type else f"{flower_color} flowers"
            parts.append(flower_desc)

        if bark_texture:
            bark_desc = f"{bark_color} {bark_texture} bark" if bark_color else f"{bark_texture} bark"
            parts.append(bark_desc)

        if root_visible and root_style:
            parts.append(f"{root_style} visible roots")

        if face_location:
            parts.append(f"face on {face_location}")

        if limb_style:
            parts.append(f"{limb_style} branch-limbs")

        if seasonal_state:
            parts.append(f"in {seasonal_state} state")

        features = p.get('special_features', [])
        if features:
            parts.append(f"with {', '.join(features)}")

        marks = p.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A plant character"
        return f"{desc}. This is a PLANT character, NOT an animal or human."

    def _build_mythological_description(self, character: Dict[str, Any]) -> str:
        """构建神话生物描述"""
        m = character.get('mythological', {})
        parts = []

        creature_type = m.get('creature_type', '')
        origin_culture = m.get('origin_culture', '')
        base_form = m.get('base_form', '')
        body_size = m.get('body_size', '')
        color_scheme = m.get('color_scheme', '')
        skin_type = m.get('skin_type', '')
        mythical_powers = m.get('mythical_powers', [])
        sacred_symbols = m.get('sacred_symbols', [])
        aura = m.get('aura', '')
        wing_type = m.get('wing_type', '')
        horn_type = m.get('horn_type', '')
        tail_type = m.get('tail_type', '')
        eye_style = m.get('eye_style', '')

        if creature_type:
            origin_desc = f"{origin_culture} " if origin_culture else ""
            parts.append(f"A {body_size} {origin_desc}{creature_type}" if body_size else f"A {origin_desc}{creature_type}")

        if base_form:
            parts.append(f"({base_form})")

        if color_scheme:
            parts.append(f"{color_scheme} coloring")

        if skin_type:
            parts.append(f"covered in {skin_type}")

        if wing_type:
            parts.append(f"with {wing_type} wings")
        if horn_type:
            parts.append(f"{horn_type} horns")
        if tail_type:
            parts.append(f"{tail_type} tail")

        if eye_style:
            parts.append(f"{eye_style} eyes")

        if aura:
            parts.append(f"surrounded by {aura} aura")

        if mythical_powers:
            parts.append(f"emanating {', '.join(mythical_powers)}")

        if sacred_symbols:
            parts.append(f"bearing {', '.join(sacred_symbols)}")

        marks = m.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A mythological {creature_type or 'creature'}"
        return f"{desc}. This is a MYTHOLOGICAL creature from legend."

    def _build_supernatural_description(self, character: Dict[str, Any]) -> str:
        """构建超自然存在描述"""
        s = character.get('supernatural', {})
        parts = []

        being_type = s.get('being_type', '')
        origin_culture = s.get('origin_culture', '')
        base_form = s.get('base_form', '')
        aura_color = s.get('aura_color', '')
        aura_intensity = s.get('aura_intensity', '')
        supernatural_features = s.get('supernatural_features', [])
        skin_appearance = s.get('skin_appearance', '')
        skin_color = s.get('skin_color', '')
        eye_type = s.get('eye_type', '')
        eye_color = s.get('eye_color', '')
        ethereal_quality = s.get('ethereal_quality', '')
        clothing_style = s.get('clothing_style', '')
        accessories = s.get('accessories', [])

        if being_type:
            origin_desc = f"{origin_culture} " if origin_culture else ""
            parts.append(f"A {origin_desc}{being_type}")

        if base_form:
            parts.append(f"{base_form} form")

        if ethereal_quality:
            parts.append(f"{ethereal_quality} appearance")

        if skin_color and skin_appearance:
            parts.append(f"{skin_color} {skin_appearance} skin")
        elif skin_color:
            parts.append(f"{skin_color} skin")

        if eye_type:
            eye_desc = f"{eye_type} {eye_color} eyes" if eye_color else f"{eye_type} eyes"
            parts.append(eye_desc)

        if supernatural_features:
            parts.append(f"with {', '.join(supernatural_features)}")

        if aura_color:
            intensity_desc = f"{aura_intensity} " if aura_intensity else ""
            parts.append(f"{intensity_desc}{aura_color} aura")

        if clothing_style:
            parts.append(f"wearing {clothing_style}")

        if accessories:
            parts.append(f"holding {', '.join(accessories)}")

        marks = s.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A supernatural {being_type or 'being'}"
        return f"{desc}. This is a SUPERNATURAL being with otherworldly qualities."

    def _build_undead_description(self, character: Dict[str, Any]) -> str:
        """构建亡灵角色描述"""
        u = character.get('undead', {})
        parts = []

        undead_type = u.get('undead_type', '')
        original_form = u.get('original_form', '')
        decay_level = u.get('decay_level', '')
        ghostly_transparency = u.get('ghostly_transparency', '')
        ghostly_color = u.get('ghostly_color', '')
        undead_features = u.get('undead_features', [])
        glow_color = u.get('glow_color', '')
        clothing_state = u.get('clothing_state', '')
        accessories = u.get('accessories', [])
        atmosphere = u.get('atmosphere', '')

        if undead_type:
            parts.append(f"An {undead_type}")

        if original_form:
            parts.append(f"(originally {original_form})")

        if ghostly_color and ghostly_transparency:
            parts.append(f"{ghostly_transparency} {ghostly_color} ethereal form")
        elif ghostly_transparency:
            parts.append(f"{ghostly_transparency} form")

        if decay_level and decay_level != 'none':
            parts.append(f"{decay_level} decay")

        if undead_features:
            parts.append(f"with {', '.join(undead_features)}")

        if glow_color:
            parts.append(f"glowing {glow_color} eyes")

        if clothing_state:
            parts.append(f"{clothing_state} clothing")

        if accessories:
            parts.append(f"carrying {', '.join(accessories)}")

        if atmosphere:
            parts.append(f"{atmosphere} atmosphere")

        marks = u.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        desc = ", ".join(parts) if parts else f"An {undead_type or 'undead'}"
        return f"{desc}. This is an UNDEAD character."

    def _build_elemental_description(self, character: Dict[str, Any]) -> str:
        """构建元素生物描述"""
        e = character.get('elemental', {})
        parts = []

        element_type = e.get('element_type', '')
        material_form = e.get('material_form', '')
        energy_color = e.get('energy_color', '')
        secondary_color = e.get('secondary_color', '')
        body_shape = e.get('body_shape', '')
        size_category = e.get('size_category', '')
        surface_texture = e.get('surface_texture', '')
        core_visible = e.get('core_visible', False)
        core_appearance = e.get('core_appearance', '')
        particle_effects = e.get('particle_effects', [])
        intensity_level = e.get('intensity_level', '')

        if element_type:
            parts.append(f"A {size_category} {element_type} elemental" if size_category else f"A {element_type} elemental")

        if body_shape:
            parts.append(f"{body_shape} form")

        if material_form:
            parts.append(f"made of {material_form} {element_type}")

        if energy_color:
            color_desc = f"{energy_color} and {secondary_color}" if secondary_color else energy_color
            parts.append(f"glowing {color_desc}")

        if surface_texture:
            parts.append(f"{surface_texture} surface")

        if core_visible and core_appearance:
            parts.append(f"with {core_appearance} core")

        if particle_effects:
            parts.append(f"emanating {', '.join(particle_effects)}")

        if intensity_level:
            parts.append(f"{intensity_level} energy")

        marks = e.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"An elemental being"
        element_name = element_type.upper() if element_type else "ELEMENT"
        return f"{desc}. This is an ELEMENTAL being made of pure {element_name}."

    def _build_alien_description(self, character: Dict[str, Any]) -> str:
        """构建外星生物描述"""
        a = character.get('alien', {})
        parts = []

        home_planet_type = a.get('home_planet_type', '')
        body_plan = a.get('body_plan', '')
        limb_count = a.get('limb_count', 4)
        limb_type = a.get('limb_type', '')
        sensory_organs = a.get('sensory_organs', [])
        eye_count = a.get('eye_count', 2)
        eye_appearance = a.get('eye_appearance', '')
        skin_texture = a.get('skin_texture', '')
        skin_color = a.get('skin_color', '')
        skin_pattern = a.get('skin_pattern', '')
        special_adaptations = a.get('special_adaptations', [])
        technology_integrated = a.get('technology_integrated', False)
        size_category = a.get('size_category', '')

        if body_plan:
            parts.append(f"A {size_category} {body_plan} alien" if size_category else f"A {body_plan} alien")

        if home_planet_type:
            parts.append(f"from a {home_planet_type} planet")

        if skin_color:
            pattern_desc = f" {skin_pattern}" if skin_pattern else ""
            parts.append(f"{skin_color}{pattern_desc} {skin_texture} skin" if skin_texture else f"{skin_color}{pattern_desc} skin")

        if limb_type and limb_count != 4:
            parts.append(f"{limb_count} {limb_type}")
        elif limb_type:
            parts.append(f"{limb_type}")

        if eye_count != 2 or eye_appearance:
            eye_desc = f"{eye_count} {eye_appearance} eyes" if eye_appearance else f"{eye_count} eyes"
            parts.append(eye_desc)

        if sensory_organs:
            parts.append(f"with {', '.join(sensory_organs)}")

        if special_adaptations:
            parts.append(f"featuring {', '.join(special_adaptations)}")

        if technology_integrated:
            parts.append("with integrated technology")

        marks = a.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else "An alien creature"
        return f"{desc}. This is an ALIEN creature from another world."

    def _build_vehicle_description(self, character: Dict[str, Any]) -> str:
        """构建载具角色描述（汽车总动员风格）"""
        v = character.get('vehicle_character', {})
        parts = []

        vehicle_type = v.get('vehicle_type', '')
        vehicle_subtype = v.get('vehicle_subtype', '')
        body_color = v.get('body_color', '')
        secondary_color = v.get('secondary_color', '')
        paint_finish = v.get('paint_finish', '')
        decals_markings = v.get('decals_markings', [])
        headlight_eyes = v.get('headlight_eyes', '')
        eye_color = v.get('eye_color', '')
        mouth_location = v.get('mouth_location', '')
        wheel_count = v.get('wheel_count', 4)
        wheel_style = v.get('wheel_style', '')
        size_category = v.get('size_category', '')
        era_style = v.get('era_style', '')
        personality_accessories = v.get('personality_accessories', [])

        if vehicle_type:
            subtype_desc = f" {vehicle_subtype}" if vehicle_subtype else ""
            era_desc = f"{era_style} " if era_style else ""
            parts.append(f"A {era_desc}{vehicle_type}{subtype_desc} with personality")

        if body_color:
            color_desc = f"{body_color} and {secondary_color}" if secondary_color else body_color
            finish_desc = f" {paint_finish}" if paint_finish else ""
            parts.append(f"{color_desc}{finish_desc} body")

        if headlight_eyes:
            eye_desc = f"{headlight_eyes} headlight eyes" + (f" ({eye_color})" if eye_color else "")
            parts.append(eye_desc)

        if mouth_location:
            parts.append(f"mouth at {mouth_location}")

        if wheel_style:
            parts.append(f"{wheel_style} wheels")

        if decals_markings:
            parts.append(f"with {', '.join(decals_markings)}")

        if personality_accessories:
            parts.append(f"wearing {', '.join(personality_accessories)}")

        marks = v.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A {vehicle_type or 'vehicle'} character"
        return f"{desc}. This is a VEHICLE character with personality and face."

    def _build_digital_description(self, character: Dict[str, Any]) -> str:
        """构建数字/虚拟角色描述"""
        d = character.get('digital_virtual', {})
        parts = []

        digital_type = d.get('digital_type', '')
        base_form = d.get('base_form', '')
        digital_aesthetic = d.get('digital_aesthetic', '')
        primary_color = d.get('primary_color', '')
        accent_color = d.get('accent_color', '')
        glitch_effects = d.get('glitch_effects', [])
        hologram_color = d.get('hologram_color', '')
        transparency_level = d.get('transparency_level', '')
        interface_elements = d.get('interface_elements', [])
        pixel_resolution = d.get('pixel_resolution', '')
        scan_lines = d.get('scan_lines', False)
        glow_effects = d.get('glow_effects', [])

        if digital_type:
            parts.append(f"A {digital_aesthetic} {digital_type}" if digital_aesthetic else f"A {digital_type}")

        if base_form:
            parts.append(f"{base_form} form")

        if primary_color:
            color_desc = f"{primary_color} with {accent_color} accents" if accent_color else primary_color
            parts.append(f"{color_desc} coloring")

        if transparency_level:
            parts.append(f"{transparency_level} appearance")

        if hologram_color:
            parts.append(f"{hologram_color} holographic projection")

        if pixel_resolution:
            parts.append(f"{pixel_resolution} pixel resolution")

        if scan_lines:
            parts.append("visible scan lines")

        if glitch_effects:
            parts.append(f"with {', '.join(glitch_effects)} glitch effects")

        if interface_elements:
            parts.append(f"surrounded by {', '.join(interface_elements)}")

        if glow_effects:
            parts.append(f"emitting {', '.join(glow_effects)} glow")

        marks = d.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A digital {digital_type or 'entity'}"
        return f"{desc}. This is a DIGITAL/VIRTUAL character."

    def _build_concept_description(self, character: Dict[str, Any]) -> str:
        """构建概念拟人描述"""
        c = character.get('concept_personified', {})
        parts = []

        concept_type = c.get('concept_type', '')
        personification_style = c.get('personification_style', '')
        base_form = c.get('base_form', '')
        symbolic_objects = c.get('symbolic_objects', [])
        abstract_features = c.get('abstract_features', [])
        color_symbolism = c.get('color_symbolism', '')
        aura_effect = c.get('aura_effect', '')
        clothing_style = c.get('clothing_style', '')
        facial_features = c.get('facial_features', '')
        body_type = c.get('body_type', '')
        movement_style = c.get('movement_style', '')

        if concept_type:
            style_desc = f"{personification_style} " if personification_style else ""
            parts.append(f"The {style_desc}personification of {concept_type}")

        if base_form:
            parts.append(f"{base_form} form")

        if body_type:
            parts.append(f"{body_type} figure")

        if color_symbolism:
            parts.append(f"in {color_symbolism} colors")

        if facial_features:
            parts.append(f"{facial_features} face")

        if clothing_style:
            parts.append(f"wearing {clothing_style}")

        if symbolic_objects:
            parts.append(f"holding {', '.join(symbolic_objects)}")

        if abstract_features:
            parts.append(f"with {', '.join(abstract_features)}")

        if aura_effect:
            parts.append(f"surrounded by {aura_effect}")

        if movement_style:
            parts.append(f"{movement_style} movement")

        marks = c.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"Personification of {concept_type or 'a concept'}"
        return f"{desc}. This is a PERSONIFIED CONCEPT."

    def _build_miniature_description(self, character: Dict[str, Any]) -> str:
        """构建微型角色描述"""
        m = character.get('miniature', {})
        parts = []

        base_type = m.get('base_type', '')
        scale_ratio = m.get('scale_ratio', '')
        size_reference_object = m.get('size_reference_object', '')
        body_proportions = m.get('body_proportions', '')
        clothing_style = m.get('clothing_style', '')
        clothing_material = m.get('clothing_material', '')
        tools_items = m.get('tools_items', [])
        skin_color = m.get('skin_color', '')
        hair_style = m.get('hair_style', '')
        hair_color = m.get('hair_color', '')
        eye_style = m.get('eye_style', '')

        if base_type:
            parts.append(f"A {scale_ratio} {base_type}" if scale_ratio else f"A tiny {base_type}")

        if size_reference_object:
            parts.append(f"(shown next to {size_reference_object} for scale)")

        if body_proportions:
            parts.append(f"{body_proportions} proportions")

        if skin_color:
            parts.append(f"{skin_color} skin")

        if hair_color and hair_style:
            parts.append(f"{hair_color} {hair_style} hair")

        if eye_style:
            parts.append(f"{eye_style} eyes")

        if clothing_style:
            material_desc = f" made of {clothing_material}" if clothing_material else ""
            parts.append(f"wearing {clothing_style}{material_desc}")

        if tools_items:
            parts.append(f"carrying {', '.join(tools_items)}")

        marks = m.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A miniature character"
        return f"{desc}. This is a MINIATURE character, very tiny compared to normal objects."

    def _build_giant_description(self, character: Dict[str, Any]) -> str:
        """构建巨型角色描述"""
        g = character.get('giant', {})
        parts = []

        giant_type = g.get('giant_type', '')
        height_category = g.get('height_category', '')
        scale_reference = g.get('scale_reference', '')
        body_build = g.get('body_build', '')
        skin_type = g.get('skin_type', '')
        skin_color = g.get('skin_color', '')
        facial_features = g.get('facial_features', '')
        eye_style = g.get('eye_style', '')
        clothing_style = g.get('clothing_style', '')
        weapons_tools = g.get('weapons_tools', [])
        environmental_effects = g.get('environmental_effects', [])

        if giant_type:
            parts.append(f"A {height_category} {giant_type}" if height_category else f"A {giant_type}")

        if scale_reference:
            parts.append(f"(scale: {scale_reference})")

        if body_build:
            parts.append(f"{body_build} build")

        if skin_color and skin_type:
            parts.append(f"{skin_color} {skin_type} skin")
        elif skin_type:
            parts.append(f"{skin_type} skin")

        if facial_features:
            parts.append(f"{facial_features} face")

        if eye_style:
            parts.append(f"{eye_style} eyes")

        if clothing_style:
            parts.append(f"wearing {clothing_style}")

        if weapons_tools:
            parts.append(f"wielding {', '.join(weapons_tools)}")

        if environmental_effects:
            parts.append(f"causing {', '.join(environmental_effects)}")

        marks = g.get('distinctive_marks', [])
        if marks:
            parts.append(f"Distinctive marks: {', '.join(marks)}")

        expression = character.get('default_expression', '')
        if expression:
            parts.append(f"({expression} expression)")

        desc = ", ".join(parts) if parts else f"A giant character"
        return f"{desc}. This is a GIANT character, enormous in scale."

    def _build_generic_description(self, character: Dict[str, Any]) -> str:
        """通用描述（兜底）"""
        desc = character.get('extra_details', '') or character.get('description', '')
        if desc:
            return desc

        name = character.get('name', 'Unknown')
        return f"A character named {name} with unspecified appearance."

    # ================================================================
    # 辅助方法
    # ================================================================

    def build_characters_prompt_section(
        self,
        characters: List[Dict[str, Any]],
        with_header: bool = True
    ) -> str:
        """
        构建多个角色的完整prompt段落

        Args:
            characters: 角色列表
            with_header: 是否包含 CHARACTERS: 头部

        Returns:
            格式化的角色描述段落
        """
        if not characters:
            return ""

        char_prompts = []
        for char in characters:
            char_prompt = self.build_character_prompt(char)
            char_prompts.append(char_prompt)

        content = "\n".join(char_prompts)

        if with_header:
            return f"CHARACTERS:\n{content}"
        return content

    def get_type_declaration(self, char_type: str) -> str:
        """获取角色类型的强制声明"""
        return get_type_declaration(char_type)
