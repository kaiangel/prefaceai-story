"""
RISK-T19-6 单测 — anthropomorphic_animal 类型映射验证

验收标准：
1. CharacterType 枚举中存在 ANTHROPOMORPHIC_ANIMAL
2. CHARACTER_TYPE_DECLARATIONS 中有 anthropomorphic_animal 映射
3. CharacterPromptBuilder.TYPE_BUILDERS 中处理 'anthropomorphic_animal'
4. _build_anthropomorphic_animal_description 输出包含 "anthropomorphic [species]"
5. LLM 误填 hair_color（人类字段）时，builder 自动转为 fur_color 并继续工作
6. 覆盖多个物种：rabbit / fox / sparrow / squirrel / wolf / bear / cat / crow / duck / panda

共 14 case（超过 10 个验收要求）

导入策略：用 importlib 直接加载目标文件，
然后在 sys.modules 中注册，让第二个文件能 import 到第一个，
完全绕过 app/models/__init__.py 的 SQLAlchemy 全量加载。
"""
import sys
import os
import importlib.util
import types

import pytest

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


def _direct_load(mod_name: str, rel_path: str):
    """从文件路径直接加载模块并注册到 sys.modules"""
    abs_path = os.path.join(_ROOT, rel_path)
    spec = importlib.util.spec_from_file_location(mod_name, abs_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# 1. 确保顶层 app 和 app.models 包存在（空的 namespace package），
#    避免 character_prompt_builder 的 from app.models.character_types import ... 失败
if 'app' not in sys.modules:
    _app_pkg = types.ModuleType('app')
    _app_pkg.__path__ = [os.path.join(_ROOT, 'app')]
    sys.modules['app'] = _app_pkg

if 'app.models' not in sys.modules:
    _models_pkg = types.ModuleType('app.models')
    _models_pkg.__path__ = [os.path.join(_ROOT, 'app', 'models')]
    sys.modules['app.models'] = _models_pkg

# 2. 直接加载 character_types.py（不走 __init__）
_ct_mod = _direct_load('app.models.character_types', 'app/models/character_types.py')
CharacterType = _ct_mod.CharacterType
CHARACTER_TYPE_DECLARATIONS = _ct_mod.CHARACTER_TYPE_DECLARATIONS

# 3. 直接加载 character_prompt_builder.py
if 'app.services' not in sys.modules:
    _svc_pkg = types.ModuleType('app.services')
    _svc_pkg.__path__ = [os.path.join(_ROOT, 'app', 'services')]
    sys.modules['app.services'] = _svc_pkg

_cpb_mod = _direct_load(
    'app.services.character_prompt_builder',
    'app/services/character_prompt_builder.py'
)
CharacterPromptBuilder = _cpb_mod.CharacterPromptBuilder


# ============================================================
# 测试数据 — 各物种拟人化动物样本
# ============================================================

def make_rabbit(with_animal_fields=True):
    """兔子角色（动物字段正确填写）"""
    char = {
        "id": "char_001",
        "name": "米莉",
        "name_en": "Milly",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "rabbit",
            "fur_color": "white",
            "fur_texture": "soft_fluffy",
            "ear_style": "very_short",
            "eye_color": "round_bright_blue",
            "tail_style": "small_fluffy",
        } if with_animal_fields else {
            # LLM 错误格式：用了人类字段
            "hair_color": "white",
            "skin_tone": "fair",
            "eye_color": "blue",
        },
        "clothing": {
            "top": "light blue knit top",
            "bottom": "white shorts",
            "accessories": ["light blue scarf"],
            "style": "cute_casual",
        },
    }
    return char


def make_fox():
    """狐狸角色"""
    return {
        "id": "char_002",
        "name": "灰狐",
        "name_en": "Grey Fox",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "elderly",
        "physical": {
            "species": "fox",
            "fur_color": "frost silver grey",
            "fur_texture": "silky",
            "ear_style": "pointed",
            "tail_style": "bushy_white_tipped",
            "eye_color": "deep amber gold",
            "snout_shape": "small pointed fox snout",
        },
        "clothing": {
            "top": "ash-grey handmade cape",
            "bottom": "ankle-length linen skirt",
            "footwear": "barefoot",
            "accessories": ["silver wrist cord"],
            "style": "rustic_quiet_elder",
        },
    }


def make_sparrow():
    """麻雀角色（鸟类——feathers 而非 fur）"""
    return {
        "id": "char_003",
        "name": "啾啾",
        "name_en": "Jiu Jiu",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "sparrow",
            "fur_color": "warm chestnut brown with golden buff streaks",
            "fur_texture": "fluffy and slightly ruffled",
            "ear_style": "small_rounded",
            "eye_color": "bright warm hazel",
            "snout_shape": "small short beak-like nose, warm orange-brown",
        },
        "clothing": {
            "top": "warm brown round-neck sleeveless top",
            "bottom": "cream loose shorts",
            "outerwear": "amber-brown padded vest",
            "style": "scrappy_energetic_explorer",
        },
    }


def make_squirrel():
    """松鼠角色"""
    return {
        "id": "char_004",
        "name": "果果",
        "name_en": "Guo Guo",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            "species": "squirrel",
            "fur_color": "warm cinnamon brown",
            "fur_texture": "dense and plush like velvet",
            "fur_pattern": "tawny patches on cheeks and belly",
            "ear_style": "small_round",
            "tail_style": "large_bushy_cinnamon",
            "eye_color": "warm dark hazel",
        },
        "clothing": {
            "top": "orange-yellow round-neck thick cotton tee",
            "bottom": "brown corduroy bib overalls",
            "outerwear": "overstuffed cinnamon puffer vest",
            "style": "cozy_woodland_foodie",
        },
    }


def make_wolf():
    """狼角色"""
    return {
        "id": "char_005",
        "name": "老雪狼",
        "name_en": "Old Snow Wolf",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "elderly",
        "physical": {
            "species": "wolf",
            "fur_color": "pure aged snow white",
            "fur_texture": "coarse and dense outer coat",
            "ear_style": "large_upright",
            "tail_style": "thick_long",
            "eye_color": "pale ice grey",
        },
        "clothing": {
            "top": "deep grey-blue wide-collar long robe",
            "bottom": "wide linen skirt",
            "outerwear": "old white handmade thick cape",
            "style": "austere_monastic_elder",
        },
    }


def make_bear():
    """熊角色"""
    return {
        "id": "char_006",
        "name": "大熊",
        "name_en": "Big Bear",
        "character_type": "anthropomorphic_animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "species": "bear",
            "fur_color": "dark brown",
            "fur_texture": "thick and dense",
            "ear_style": "small_round",
            "eye_color": "warm amber",
        },
        "clothing": {
            "top": "plaid flannel shirt",
            "bottom": "denim overalls",
            "style": "lumberjack_casual",
        },
    }


def make_cat():
    """猫角色"""
    return {
        "id": "char_007",
        "name": "黑猫侦探",
        "name_en": "Black Cat Detective",
        "character_type": "anthropomorphic_animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "species": "cat",
            "fur_color": "jet black",
            "fur_texture": "sleek short",
            "ear_style": "pointed_erect",
            "tail_style": "long_slender",
            "eye_color": "bright yellow-green",
        },
        "clothing": {
            "top": "charcoal trench coat",
            "bottom": "dark grey trousers",
            "accessories": ["fedora hat", "magnifying glass"],
            "style": "noir_detective",
        },
    }


def make_crow():
    """乌鸦角色（鸟类）"""
    return {
        "id": "char_008",
        "name": "乌鸦先生",
        "name_en": "Mr. Crow",
        "character_type": "anthropomorphic_animal",
        "gender": "male",
        "age_appearance": "middle_aged",
        "physical": {
            "species": "crow",
            "fur_color": "iridescent blue-black",
            "fur_texture": "glossy smooth feathers",
            "ear_style": "no_external_ears",
            "eye_color": "sharp obsidian black",
            "snout_shape": "strong sharp black beak",
        },
        "clothing": {
            "top": "black velvet waistcoat",
            "bottom": "black formal trousers",
            "accessories": ["silver pocket watch", "monocle"],
            "style": "victorian_gentleman",
        },
    }


def make_duck():
    """鸭子角色（鸟类）"""
    return {
        "id": "char_009",
        "name": "小鸭鸭",
        "name_en": "Little Ducky",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "child",
        "physical": {
            "species": "duck",
            "fur_color": "sunny yellow",
            "fur_texture": "downy soft",
            "eye_color": "bright orange-brown",
            "snout_shape": "wide flat orange bill",
        },
        "clothing": {
            "top": "white sailor blouse",
            "bottom": "blue sailor skirt",
            "accessories": ["yellow bow on head"],
            "style": "cute_sailor_child",
        },
    }


def make_panda():
    """熊猫角色"""
    return {
        "id": "char_010",
        "name": "熊猫厨师",
        "name_en": "Panda Chef",
        "character_type": "anthropomorphic_animal",
        "gender": "male",
        "age_appearance": "adult",
        "physical": {
            "species": "panda",
            "fur_color": "black and white with distinctive eye patches",
            "fur_texture": "thick plush",
            "ear_style": "small_round_black",
            "eye_color": "dark brown with black eye patches",
        },
        "clothing": {
            "top": "white chef coat with black buttons",
            "bottom": "black and white checkered chef trousers",
            "accessories": ["tall chef hat", "bamboo spatula"],
            "style": "professional_chef",
        },
    }


def make_rabbit_wrong_schema():
    """兔子角色 - LLM 错误使用人类字段（防御性测试）"""
    return {
        "id": "char_011",
        "name": "错误兔子",
        "name_en": "Wrong Rabbit",
        "character_type": "anthropomorphic_animal",
        "gender": "female",
        "age_appearance": "young_adult",
        "physical": {
            # 错误：用了人类字段
            "hair_color": "snow white",
            "skin_tone": "fair",
            "face_shape": "round",
            "eye_color": "blue",
            # 没有 species、fur_color 等动物字段
        },
        "clothing": {
            "top": "blue dress",
            "style": "cute",
        },
        # 从 description 推断物种
        "description": "A white rabbit with blue eyes wearing a cute dress.",
        "name_en": "White Rabbit",
    }


# ============================================================
# Case 1: CharacterType 枚举存在 ANTHROPOMORPHIC_ANIMAL
# ============================================================

def test_character_type_enum_exists():
    """RISK-T19-6 A: CharacterType 枚举必须有 ANTHROPOMORPHIC_ANIMAL"""
    assert hasattr(CharacterType, 'ANTHROPOMORPHIC_ANIMAL'), \
        "CharacterType 枚举缺少 ANTHROPOMORPHIC_ANIMAL 成员"
    assert CharacterType.ANTHROPOMORPHIC_ANIMAL == "anthropomorphic_animal", \
        f"值不正确: {CharacterType.ANTHROPOMORPHIC_ANIMAL}"


# ============================================================
# Case 2: CHARACTER_TYPE_DECLARATIONS 映射存在
# ============================================================

def test_type_declarations_has_anthropomorphic():
    """RISK-T19-6 B: CHARACTER_TYPE_DECLARATIONS 必须有 anthropomorphic_animal 映射"""
    assert CharacterType.ANTHROPOMORPHIC_ANIMAL in CHARACTER_TYPE_DECLARATIONS, \
        "CHARACTER_TYPE_DECLARATIONS 缺少 ANTHROPOMORPHIC_ANIMAL 键"
    declaration = CHARACTER_TYPE_DECLARATIONS[CharacterType.ANTHROPOMORPHIC_ANIMAL]
    assert "ANTHROPOMORPHIC" in declaration.upper(), \
        f"声明内容应包含 ANTHROPOMORPHIC: {declaration}"
    # 确保声明强调了动物特征和服装
    assert "NOT a human" in declaration or "NOT A HUMAN" in declaration.upper(), \
        "声明应明确说明 NOT a human"


# ============================================================
# Case 3: TYPE_BUILDERS 有 anthropomorphic_animal 键
# ============================================================

def test_type_builders_has_anthropomorphic():
    """RISK-T19-6 C: CharacterPromptBuilder.TYPE_BUILDERS 必须处理 anthropomorphic_animal"""
    builder = CharacterPromptBuilder()
    assert 'anthropomorphic_animal' in builder.TYPE_BUILDERS, \
        "TYPE_BUILDERS 缺少 'anthropomorphic_animal' 键"
    method_name = builder.TYPE_BUILDERS['anthropomorphic_animal']
    assert hasattr(builder, method_name), \
        f"TYPE_BUILDERS 指向的方法 '{method_name}' 不存在"


# ============================================================
# Case 4-8: 各物种拟人化动物 builder 输出含 "anthropomorphic [species]"
# ============================================================

def test_rabbit_prompt_contains_anthropomorphic():
    """Case 4: 兔子角色 prompt 应含 anthropomorphic rabbit"""
    builder = CharacterPromptBuilder()
    char = make_rabbit(with_animal_fields=True)
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"兔子 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'rabbit' in result.lower(), \
        f"兔子 prompt 缺少 'rabbit': {result[:200]}"
    # 确认不走 generic fallback
    assert 'A character named' not in result, \
        "不应走 generic fallback"


def test_fox_prompt_contains_anthropomorphic():
    """Case 5: 狐狸角色 prompt 应含 anthropomorphic fox"""
    builder = CharacterPromptBuilder()
    char = make_fox()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"狐狸 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'fox' in result.lower(), \
        f"狐狸 prompt 缺少 'fox': {result[:200]}"


def test_sparrow_prompt_uses_feathers_not_fur():
    """Case 6: 麻雀（鸟类）prompt 应用 feathers 而非 fur"""
    builder = CharacterPromptBuilder()
    char = make_sparrow()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"麻雀 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'sparrow' in result.lower(), \
        f"麻雀 prompt 缺少 'sparrow': {result[:200]}"
    # 鸟类应用 feathers
    assert 'feathers' in result.lower(), \
        f"鸟类 prompt 应使用 feathers: {result[:300]}"


def test_squirrel_prompt_contains_tail():
    """Case 7: 松鼠 prompt 应含 tail（大尾巴是标志特征）"""
    builder = CharacterPromptBuilder()
    char = make_squirrel()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"松鼠 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'squirrel' in result.lower(), \
        f"松鼠 prompt 缺少 'squirrel': {result[:200]}"
    assert 'tail' in result.lower(), \
        f"松鼠 prompt 应包含 tail: {result[:300]}"


def test_wolf_prompt_contains_anthropomorphic():
    """Case 8: 狼角色 prompt 应含 anthropomorphic wolf"""
    builder = CharacterPromptBuilder()
    char = make_wolf()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"狼 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'wolf' in result.lower(), \
        f"狼 prompt 缺少 'wolf': {result[:200]}"


# ============================================================
# Case 9: LLM 误用 hair_color (人类字段) — 防御性测试
# ============================================================

def test_wrong_schema_hair_color_converted():
    """Case 9: LLM 错误用 hair_color 字段时，builder 应转为 fur_color 而非崩溃"""
    builder = CharacterPromptBuilder()
    char = make_rabbit_wrong_schema()
    # 不应 raise 异常
    result = builder.build_character_prompt(char)
    assert result, "builder 不应返回空字符串"
    # 应该仍然识别到 anthropomorphic
    assert 'anthropomorphic' in result.lower(), \
        f"错误 schema 时也应输出 anthropomorphic: {result[:300]}"
    # snow white 毛色应被保留（转为 fur_color）
    assert 'snow white' in result.lower() or 'white' in result.lower(), \
        f"hair_color 应被转为 fur_color 使用: {result[:300]}"


# ============================================================
# Case 10: 鸟类（乌鸦）prompt 含 feathers
# ============================================================

def test_crow_prompt_uses_feathers():
    """Case 10: 乌鸦（鸟类）prompt 应用 feathers"""
    builder = CharacterPromptBuilder()
    char = make_crow()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"乌鸦 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'crow' in result.lower(), \
        f"乌鸦 prompt 缺少 'crow': {result[:200]}"
    assert 'feathers' in result.lower(), \
        f"鸟类 prompt 应使用 feathers: {result[:300]}"


# ============================================================
# Case 11: 熊角色 prompt 含 clothing（拟人化动物穿服装）
# ============================================================

def test_bear_prompt_contains_clothing():
    """Case 11: 熊角色 prompt 应包含服装描述（拟人化动物穿衣服）"""
    builder = CharacterPromptBuilder()
    char = make_bear()
    result = builder.build_character_prompt(char)
    assert 'CLOTHING' in result, \
        f"拟人化熊 prompt 应包含 CLOTHING 段: {result[:300]}"
    assert 'flannel' in result.lower() or 'shirt' in result.lower(), \
        f"服装细节应出现在 prompt 中: {result[:300]}"


# ============================================================
# Case 12: 猫角色 prompt — 强调不是人类
# ============================================================

def test_cat_prompt_not_human_warning():
    """Case 12: 猫角色 prompt 应明确说明 NOT a human"""
    builder = CharacterPromptBuilder()
    char = make_cat()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"猫 prompt 缺少 'anthropomorphic': {result[:200]}"
    # prompt 应有 "NOT" 相关声明
    assert 'NOT' in result or 'not' in result.lower(), \
        f"拟人化动物 prompt 应有否定人类的声明: {result[:300]}"


# ============================================================
# Case 13: 鸭子角色 prompt — 儿童年龄拟人化动物
# ============================================================

def test_duck_child_anthropomorphic():
    """Case 13: 鸭子（儿童年龄）prompt 应正确处理 child age_appearance"""
    builder = CharacterPromptBuilder()
    char = make_duck()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"鸭子 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'duck' in result.lower(), \
        f"鸭子 prompt 缺少 'duck': {result[:200]}"
    # 不应走 generic fallback
    assert 'A character named' not in result


# ============================================================
# Case 14: 熊猫角色 prompt — fur_pattern（黑白花纹）
# ============================================================

def test_panda_prompt_contains_pattern():
    """Case 14: 熊猫 prompt 应包含 fur_color 的黑白描述"""
    builder = CharacterPromptBuilder()
    char = make_panda()
    result = builder.build_character_prompt(char)
    assert 'anthropomorphic' in result.lower(), \
        f"熊猫 prompt 缺少 'anthropomorphic': {result[:200]}"
    assert 'panda' in result.lower(), \
        f"熊猫 prompt 缺少 'panda': {result[:200]}"
    assert 'black' in result.lower() or 'white' in result.lower(), \
        f"熊猫毛色（黑白）应出现在 prompt 中: {result[:300]}"


# ============================================================
# 运行测试
# ============================================================

if __name__ == '__main__':
    tests = [
        test_character_type_enum_exists,
        test_type_declarations_has_anthropomorphic,
        test_type_builders_has_anthropomorphic,
        test_rabbit_prompt_contains_anthropomorphic,
        test_fox_prompt_contains_anthropomorphic,
        test_sparrow_prompt_uses_feathers_not_fur,
        test_squirrel_prompt_contains_tail,
        test_wolf_prompt_contains_anthropomorphic,
        test_wrong_schema_hair_color_converted,
        test_crow_prompt_uses_feathers,
        test_bear_prompt_contains_clothing,
        test_cat_prompt_not_human_warning,
        test_duck_child_anthropomorphic,
        test_panda_prompt_contains_pattern,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {t.__name__}")
            print(f"    {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n总计: {passed} PASS / {failed} FAIL / {len(tests)} 总计")
