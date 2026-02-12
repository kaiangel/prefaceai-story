"""
场景风格管理器

确保：
1. 同一场景类型的背景风格一致
2. 室内/室外场景有对应的光影处理
3. 情绪氛围反映在色调上
"""

from typing import Dict, Any, Optional
from app.models.style_config import ProjectStyleConfig


class SceneStyleManager:
    """
    场景风格管理器

    确保：
    1. 同一场景类型的背景风格一致
    2. 室内/室外场景有对应的光影处理
    3. 情绪氛围反映在色调上
    """

    SCENE_TYPE_MODIFIERS = {
        "indoor": "interior scene, indoor lighting",
        "outdoor": "exterior scene, natural environment",
        "urban": "city environment, buildings, streets",
        "nature": "natural landscape, organic elements",
        "fantasy": "magical environment, otherworldly elements",
        "cave": "cave interior, rock formations, dim lighting",
        "mountain": "mountain landscape, rocky terrain, dramatic elevation",
        "sky": "aerial view, sky scene, clouds",
    }

    MOOD_COLOR_MAPPING = {
        "happy": "bright, warm colors, high key lighting",
        "sad": "muted colors, low saturation, soft shadows",
        "tense": "high contrast, dramatic shadows, desaturated",
        "romantic": "warm pink/golden tones, soft focus, dreamy",
        "scary": "dark shadows, cold tones, low key lighting",
        "epic": "grand scale, dramatic lighting, saturated colors",
        "hopeful": "warm golden tones, soft light, uplifting atmosphere",
        "desperate": "dark, cold colors, harsh shadows, bleak atmosphere",
        "peaceful": "soft colors, gentle lighting, serene atmosphere",
        "triumphant": "golden light, heroic atmosphere, warm vibrant colors",
        "melancholic": "muted blues and grays, soft diffused light",
        "magical": "ethereal glow, mystical colors, sparkling effects",
    }

    TIME_LIGHTING_MAPPING = {
        "morning": "soft morning light, warm golden hour",
        "noon": "bright midday sun, short shadows",
        "afternoon": "warm afternoon light, long shadows",
        "evening": "golden hour, orange/pink sky",
        "night": "night scene, moonlight, artificial lights",
        "dawn": "early dawn, purple/pink sky, soft light",
        "dusk": "twilight, blue hour, fading light",
        "golden_hour": "golden hour lighting, warm orange glow, long shadows",
        "midnight": "deep night, minimal light, cold blue tones",
        "timeless": "ethereal timeless lighting, soft glow",
    }

    WEATHER_MODIFIERS = {
        "clear": "clear sky, good visibility",
        "cloudy": "overcast sky, diffused light",
        "rainy": "rain, wet surfaces, gray atmosphere",
        "stormy": "storm clouds, dramatic weather, dark sky",
        "foggy": "fog, mist, limited visibility",
        "snowy": "snow, white landscape, cold atmosphere",
        "blizzard": "heavy snow, strong wind, low visibility, harsh conditions",
    }

    def build_scene_style_prompt(
        self,
        scene: Dict[str, Any],
        project_style: Optional[ProjectStyleConfig] = None
    ) -> str:
        """
        为单个场景构建环境风格描述
        """
        parts = []

        location = scene.get('location', '')
        time = scene.get('time', '')
        mood = scene.get('mood', '')

        # 获取scene_style（如果有）
        scene_style = scene.get('scene_style', {})

        # 场景类型
        scene_type = self._infer_scene_type(location)
        if scene_type in self.SCENE_TYPE_MODIFIERS:
            parts.append(self.SCENE_TYPE_MODIFIERS[scene_type])

        # 时间光影
        time_key = self._normalize_time(time, scene_style)
        if time_key in self.TIME_LIGHTING_MAPPING:
            parts.append(self.TIME_LIGHTING_MAPPING[time_key])

        # 情绪色调
        mood_key = self._normalize_mood(mood, scene_style)
        if mood_key in self.MOOD_COLOR_MAPPING:
            parts.append(self.MOOD_COLOR_MAPPING[mood_key])

        # 天气
        weather = scene_style.get('weather', '')
        if weather:
            weather_key = self._normalize_weather(weather)
            if weather_key in self.WEATHER_MODIFIERS:
                parts.append(self.WEATHER_MODIFIERS[weather_key])

        # 色调覆盖（从scene_style）
        color_palette = scene_style.get('color_palette', '')
        if color_palette:
            parts.append(f"{color_palette} color palette")

        # 光影覆盖（从scene_style）
        lighting = scene_style.get('lighting', '')
        if lighting:
            parts.append(f"{lighting} lighting")

        # 氛围覆盖（从scene_style）
        atmosphere = scene_style.get('atmosphere', '')
        if atmosphere:
            parts.append(f"{atmosphere} atmosphere")

        return ", ".join(parts) if parts else ""

    def _infer_scene_type(self, location: str) -> str:
        """从location推断场景类型"""
        location_lower = location.lower()

        # 定义关键词映射
        keywords_mapping = {
            'cave': ['cave', '洞', '冰洞', '山洞', '洞穴'],
            'mountain': ['mountain', 'cliff', 'peak', '山', '悬崖', '山脉', '山峰'],
            'sky': ['sky', 'cloud', 'air', '天空', '云', '空中', '飞翔'],
            'indoor': ['room', 'house', 'office', 'indoor', '室内', '房间', '屋', '洞内'],
            'urban': ['city', 'street', 'building', '城市', '街道', '建筑'],
            'nature': ['forest', 'valley', 'field', 'garden', '森林', '山谷', '草地', '花园', '树'],
            'fantasy': ['magic', 'rainbow', 'ethereal', '彩虹', '魔法', '奇幻'],
        }

        for scene_type, keywords in keywords_mapping.items():
            if any(kw in location_lower for kw in keywords):
                return scene_type

        return 'outdoor'

    def _normalize_time(self, time: str, scene_style: Dict[str, Any] = None) -> str:
        """标准化时间词"""
        # 优先使用scene_style中的time_of_day
        if scene_style and scene_style.get('time_of_day'):
            time = scene_style['time_of_day']

        time_lower = time.lower() if time else ''

        mappings = {
            '清晨': 'dawn', '早晨': 'morning', '上午': 'morning',
            '中午': 'noon', '下午': 'afternoon', '傍晚': 'evening',
            '黄昏': 'dusk', '夜晚': 'night', '深夜': 'midnight',
            '凌晨': 'dawn', '日出': 'dawn', '日落': 'dusk',
            'golden hour': 'golden_hour', 'golden_hour': 'golden_hour',
            'timeless': 'timeless', 'eternal': 'timeless',
        }

        for cn, en in mappings.items():
            if cn in time_lower:
                return en

        # 如果已经是英文时间词
        if time_lower in self.TIME_LIGHTING_MAPPING:
            return time_lower

        return time_lower if time_lower else ''

    def _normalize_mood(self, mood: str, scene_style: Dict[str, Any] = None) -> str:
        """标准化情绪词"""
        # 优先使用scene_style中的atmosphere
        if scene_style and scene_style.get('atmosphere'):
            mood = scene_style['atmosphere']

        mood_lower = mood.lower() if mood else ''

        mappings = {
            '温馨': 'happy', '欢乐': 'happy', '开心': 'happy',
            '紧张': 'tense', '焦虑': 'tense',
            '悲伤': 'sad', '伤感': 'sad',
            '恐怖': 'scary', '恐惧': 'scary',
            '浪漫': 'romantic',
            '史诗': 'epic', '壮丽': 'epic', '英雄': 'epic',
            '绝望': 'desperate', '黑暗': 'desperate',
            '希望': 'hopeful', '温暖': 'hopeful',
            '平静': 'peaceful', '宁静': 'peaceful', '安详': 'peaceful',
            '胜利': 'triumphant', '凯旋': 'triumphant', '鼓舞': 'triumphant',
            '忧郁': 'melancholic',
            '魔法': 'magical', '梦幻': 'magical', '神奇': 'magical',
            # 英文映射
            'triumphant': 'triumphant', 'hopeful': 'hopeful',
            'desperate': 'desperate', 'peaceful': 'peaceful',
            'tense': 'tense', 'melancholic': 'melancholic',
            'magical': 'magical', 'epic': 'epic',
        }

        for cn, en in mappings.items():
            if cn in mood_lower:
                return en

        # 如果已经是英文情绪词
        if mood_lower in self.MOOD_COLOR_MAPPING:
            return mood_lower

        return ''

    def _normalize_weather(self, weather: str) -> str:
        """标准化天气词"""
        weather_lower = weather.lower()

        mappings = {
            '晴': 'clear', '多云': 'cloudy', '阴天': 'cloudy',
            '雨': 'rainy', '下雨': 'rainy',
            '暴风雪': 'blizzard', '雪': 'snowy',
            '雾': 'foggy', '薄雾': 'foggy', 'mist': 'foggy',
            '风暴': 'stormy', '暴风': 'stormy',
        }

        for cn, en in mappings.items():
            if cn in weather_lower:
                return en

        # 如果已经是英文
        if weather_lower in self.WEATHER_MODIFIERS:
            return weather_lower

        # 部分匹配
        if 'clear' in weather_lower:
            return 'clear'
        elif 'blizzard' in weather_lower:
            return 'blizzard'
        elif 'storm' in weather_lower:
            return 'stormy'
        elif 'snow' in weather_lower:
            return 'snowy'

        return ''
