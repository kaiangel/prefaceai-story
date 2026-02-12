"""
TextOverlayService - 条漫文字叠加服务

统一的文字叠加服务，支持：
- 对话气泡（半透明，支持动态位置）
- 旁白条（自适应透明度）
- 心理独白
- 混合类型文字

架构重构：从8个测试文件整合为统一主服务
- ARCH-1: 创建主服务文件
- ARCH-2: 整合最佳实现
- CORE-1: strip_speaker_prefix全覆盖
- CORE-2: 气泡透明度正确实现（alpha_composite）

作者: @Backend
日期: 2026-02-03
"""

import os
import re
from typing import Optional, List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# 字体配置
# =============================================================================

# 支持多平台的字体路径
FONT_PATHS = [
    # macOS
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/Library/Fonts/Arial Unicode.ttf",
    # Linux
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simsun.ttc",
]

# 字体大小配置
DEFAULT_FONT_SIZE = 42
SPEECH_BUBBLE_FONT_SIZE = 36
EMPHASIS_FONT_SIZE = 52
EMPHASIS_COLOR = "#FF4444"


# =============================================================================
# 工具函数
# =============================================================================

def strip_speaker_prefix(text: str) -> str:
    """
    通用Speaker前缀剥离

    支持格式:
    - "角色名：「内容」" → "「内容」"
    - "角色名内心：「内容」" → "「内容」"
    - "旁白：「内容」" → "「内容」"
    - 支持中英文冒号
    - 支持中日韩引号

    Args:
        text: 原始文字

    Returns:
        剥离前缀后的文字
    """
    if not text:
        return text

    # 匹配：角色名（可选"内心"）+ 冒号 + 可选引号 + 内容 + 可选引号
    pattern = r'^[\w\u4e00-\u9fff]+(?:内心)?[：:]\s*[「"『]?(.+?)[」"』]?$'
    match = re.match(pattern, text.strip())
    if match:
        content = match.group(1)
        # FIX-B2: 直接返回内容，不添加引号
        # 之前的逻辑会给没有引号的内容添加「」，但这是不需要的
        return content
    return text


def get_bubble_position_for_index(index: int, total: int) -> Tuple[int, int]:
    """
    根据气泡索引和总数计算合适的位置 - 支持3+气泡

    布局策略：交替左右布局，y位置按行递增

    Args:
        index: 当前气泡索引（从0开始）
        total: 总气泡数

    Returns:
        (x_percent, y_percent) 位置百分比元组
    """
    # y位置按行递增
    y_positions = [3, 10, 18, 26, 34, 42]

    if total <= 2:
        # 双气泡特殊处理
        if index == 0:
            return (30, 3)
        else:
            return (70, 10)
    else:
        # 3+气泡：交替左右
        row = index // 2
        is_left = (index % 2 == 0)
        x_pct = 30 if is_left else 70
        y_pct = y_positions[min(row, len(y_positions) - 1)]
        return (x_pct, y_pct)


def detect_overlay_collision(existing_bounds: List[Tuple], new_bounds: Tuple) -> bool:
    """
    检测新叠加区域是否与现有区域冲突

    Args:
        existing_bounds: 现有叠加区域列表，每个元素是 (x, y, width, height)
        new_bounds: 新叠加区域 (x, y, width, height)

    Returns:
        True 如果有碰撞，False 如果没有
    """
    new_x, new_y, new_w, new_h = new_bounds
    new_x2 = new_x + new_w
    new_y2 = new_y + new_h

    for (ex, ey, ew, eh) in existing_bounds:
        ex2 = ex + ew
        ey2 = ey + eh
        # 检测重叠
        if not (new_x2 < ex or new_x > ex2 or new_y2 < ey or new_y > ey2):
            return True
    return False


# =============================================================================
# TextOverlayService 主类
# =============================================================================

class TextOverlayService:
    """
    文字叠加服务

    支持功能：
    - 对话气泡（半透明，支持动态位置）
    - 旁白条（自适应透明度）
    - 心理独白
    - 混合类型文字
    - 碰撞检测和垂直堆叠
    """

    def __init__(
        self,
        font_path: Optional[str] = None,
        default_font_size: int = DEFAULT_FONT_SIZE,
        bubble_font_size: int = SPEECH_BUBBLE_FONT_SIZE,
        bubble_alpha: int = 180  # FIX-B4: 配置化，降低默认值从191到180（约70%不透明）
    ):
        """
        初始化文字叠加服务

        Args:
            font_path: 自定义字体路径（可选）
            default_font_size: 默认字体大小
            bubble_font_size: 气泡字体大小
            bubble_alpha: 气泡默认透明度 (0-255)，默认180（约70%不透明）
        """
        self.font_path = font_path or self._find_font()
        self.default_font_size = default_font_size
        self.bubble_font_size = bubble_font_size
        self.default_bubble_alpha = bubble_alpha  # FIX-B4: 存储默认透明度
        self.font_cache = {}
        # FIX-B3: 跟踪已使用的气泡区域，用于碰撞检测
        self._bubble_bounds: List[Tuple[int, int, int, int]] = []

    def _find_font(self) -> str:
        """查找可用的中文字体"""
        for path in FONT_PATHS:
            if os.path.exists(path):
                return path
        raise RuntimeError("未找到可用的中文字体。请安装中文字体或指定font_path参数。")

    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """获取指定大小的字体（带缓存）"""
        if size not in self.font_cache:
            self.font_cache[size] = ImageFont.truetype(self.font_path, size)
        return self.font_cache[size]

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """文字自动换行"""
        lines = []
        current_line = ""
        for char in text:
            test_line = current_line + char
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)
        return lines

    def get_overlay_alpha_by_brightness(
        self,
        image: Image.Image,
        region: str = "bottom",
        height_ratio: float = 0.18
    ) -> int:
        """
        根据图片指定区域的亮度计算适合的overlay透明度

        Args:
            image: 原始图片
            region: 区域位置 ("top", "bottom", "center")
            height_ratio: 区域高度比例

        Returns:
            alpha值 (0-255)
        """
        width, height = image.size
        bar_height = int(height * height_ratio)

        if region == "top":
            crop_box = (0, 0, width, bar_height)
        elif region == "bottom":
            crop_box = (0, height - bar_height, width, height)
        else:  # center
            center_y = (height - bar_height) // 2
            crop_box = (0, center_y, width, center_y + bar_height)

        region_img = image.crop(crop_box)
        grayscale = region_img.convert("L")

        import numpy as np
        brightness = np.array(grayscale).mean()

        if brightness > 180:
            return 100  # 非常亮
        elif brightness > 140:
            return 130
        elif brightness > 100:
            return 160
        else:
            return 190  # 较暗

    def add_monologue(
        self,
        image: Image.Image,
        text: str,
        position: str = "bottom",
        height_ratio: float = 0.18,
        y_offset: int = 0
    ) -> Tuple[Image.Image, int]:
        """
        添加旁白/心理独白（黑底白字）

        Args:
            image: 原始图片
            text: 文字内容
            position: 位置 ("top", "bottom", "center")
            height_ratio: 条带高度比例
            y_offset: 垂直偏移（用于多旁白堆叠）

        Returns:
            (处理后的图片, 条带高度) 元组
        """
        # CORE-1: 所有文字类型都剥离speaker前缀
        clean_text = strip_speaker_prefix(text)

        img = image.copy()
        width, height = img.size
        bar_height = int(height * height_ratio)

        if position == "top":
            bar_y = 0 + y_offset
        elif position == "bottom":
            bar_y = height - bar_height - y_offset
        else:
            bar_y = (height - bar_height) // 2

        # 正确的透明度实现：使用alpha_composite
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        adaptive_alpha = self.get_overlay_alpha_by_brightness(image, position, height_ratio)
        overlay_draw.rectangle([0, bar_y, width, bar_y + bar_height], fill=(0, 0, 0, adaptive_alpha))

        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        img = Image.alpha_composite(img, overlay)

        font = self._get_font(self.default_font_size)
        max_text_width = int(width * 0.9)
        lines = self._wrap_text(clean_text, font, max_text_width)

        line_height = self.default_font_size + 12
        total_text_height = len(lines) * line_height
        text_start_y = bar_y + (bar_height - total_text_height) // 2

        draw = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            text_x = (width - line_width) // 2
            text_y = text_start_y + i * line_height
            draw.text((text_x, text_y), line, font=font, fill="white")

        return (img, bar_height)

    def add_speech_bubble(
        self,
        image: Image.Image,
        text: str,
        bubble_x_percent: int = 50,
        bubble_y_percent: int = 5,
        bubble_alpha: Optional[int] = None  # FIX-B4: 使用None表示使用默认值
    ) -> Image.Image:
        """
        添加对话气泡（半透明）

        CORE-2: 使用alpha_composite正确实现透明度
        FIX-B3: 支持碰撞检测，自动避让已有气泡
        FIX-B4: 透明度配置化

        Args:
            image: 原始图片
            text: 文字内容
            bubble_x_percent: 气泡x位置百分比 (0-100)
            bubble_y_percent: 气泡y位置百分比 (0-100)
            bubble_alpha: 气泡透明度 (0-255)，默认使用self.default_bubble_alpha

        Returns:
            处理后的图片
        """
        # FIX-B4: 使用配置的默认透明度
        if bubble_alpha is None:
            bubble_alpha = self.default_bubble_alpha

        # CORE-1: 剥离speaker前缀
        clean_text = strip_speaker_prefix(text)

        img = image.copy()
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        width, height = img.size
        font = self._get_font(self.bubble_font_size)

        bubble_padding = 18
        max_bubble_width = int(width * 0.5)
        lines = self._wrap_text(clean_text, font, max_bubble_width - bubble_padding * 2)

        line_height = self.bubble_font_size + 8
        text_height = len(lines) * line_height

        max_line_width = 0
        for line in lines:
            bbox = font.getbbox(line)
            max_line_width = max(max_line_width, bbox[2] - bbox[0])

        bubble_width = max_line_width + bubble_padding * 2
        bubble_height = text_height + bubble_padding * 2

        bubble_x = int(width * bubble_x_percent / 100) - bubble_width // 2
        bubble_y = int(height * bubble_y_percent / 100)

        bubble_x = max(5, min(bubble_x, width - bubble_width - 5))
        bubble_y = max(5, min(bubble_y, height - bubble_height - 20))

        # FIX-B3: 碰撞检测 - 如果与已有气泡重叠，向下移动
        new_bounds = (bubble_x, bubble_y, bubble_width, bubble_height)
        max_attempts = 5  # 最多尝试5次避让
        y_step = bubble_height + 10  # 每次向下移动的距离

        for attempt in range(max_attempts):
            if not detect_overlay_collision(self._bubble_bounds, new_bounds):
                break
            # 检测到碰撞，向下移动
            bubble_y += y_step
            bubble_y = min(bubble_y, height - bubble_height - 20)  # 不超出底部
            new_bounds = (bubble_x, bubble_y, bubble_width, bubble_height)

        # 记录这个气泡的区域
        self._bubble_bounds.append(new_bounds)

        # CORE-2: 正确的透明度实现 - 创建单独的气泡层
        bubble_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
        bubble_draw = ImageDraw.Draw(bubble_layer)

        # 半透明白色气泡
        bubble_fill_color = (255, 255, 255, bubble_alpha)

        bubble_rect = [bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height]
        bubble_draw.rounded_rectangle(bubble_rect, radius=18, fill=bubble_fill_color)

        # 尾巴
        tail_size = 15
        tail_center_x = bubble_width // 2
        tail_points = [
            (bubble_x + tail_center_x - 15, bubble_y + bubble_height),
            (bubble_x + tail_center_x, bubble_y + bubble_height + tail_size),
            (bubble_x + tail_center_x + 15, bubble_y + bubble_height)
        ]
        bubble_draw.polygon(tail_points, fill=bubble_fill_color)

        # 合成透明气泡层
        img = Image.alpha_composite(img, bubble_layer)

        # 绘制边框（在合成后的图像上，边框不透明）
        border_draw = ImageDraw.Draw(img)
        border_draw.rounded_rectangle(bubble_rect, radius=18, outline="black", width=2)
        border_draw.polygon(tail_points, outline="black", width=2)
        # 覆盖尾巴底部的边框线
        border_draw.line([tail_points[0], tail_points[2]], fill=(255, 255, 255, 255), width=4)

        # 绘制文字（不透明）
        text_draw = ImageDraw.Draw(img)
        text_y = bubble_y + bubble_padding
        for line in lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            text_x = bubble_x + (bubble_width - line_width) // 2
            text_draw.text((text_x, text_y), line, font=font, fill="black")
            text_y += line_height

        return img

    def process_shot(
        self,
        image: Image.Image,
        shot: Dict,
        bubble_positions: Optional[Dict] = None
    ) -> Image.Image:
        """
        处理单个shot的文字叠加

        统一处理所有text_type，包括：
        - none: 无文字
        - narration: 旁白
        - thought: 心理独白
        - dialogue: 对话
        - dialogue_with_thought: 对话+心理
        - dialogue_with_narration: 对话+旁白
        - narration_with_thought: 旁白+心理
        - narration_with_dialogue: 旁白+对话

        Args:
            image: 原始图片
            shot: Shot配置字典，需包含text_type和chinese_text字段
            bubble_positions: AI检测的气泡位置（可选）

        Returns:
            处理后的图片
        """
        # FIX-B3: 每个shot开始时重置气泡碰撞检测跟踪
        self._bubble_bounds = []

        result = image
        text_type = shot.get("text_type", "none")
        chinese_text = shot.get("chinese_text")

        if text_type == "none" or not chinese_text:
            return result

        # 跟踪各位置已占用的高度，用于垂直堆叠
        position_offsets = {"top": 0, "bottom": 0, "center": 0}

        # 处理不同类型的文字
        if text_type == "narration":
            position = shot.get("speaker_position", "bottom")
            if position in ["top", "bottom", "center"]:
                result, _ = self.add_monologue(result, chinese_text, position=position)

        elif text_type == "thought":
            position = shot.get("speaker_position", "bottom")
            if "," in position:
                position = position.split(",")[0]
            text = chinese_text if isinstance(chinese_text, str) else chinese_text[0]
            result, _ = self.add_monologue(result, text, position=position)

        elif text_type == "dialogue":
            if isinstance(chinese_text, list):
                total_bubbles = len(chinese_text)
                for i, txt in enumerate(chinese_text):
                    x_pct, y_pct = get_bubble_position_for_index(i, total_bubbles)

                    if bubble_positions and i < len(bubble_positions):
                        pos = list(bubble_positions.values())[i] if isinstance(bubble_positions, dict) else bubble_positions[i]
                        x_pct = pos.get("bubble_x_percent", x_pct)
                        y_pct = pos.get("bubble_y_percent", y_pct)

                    result = self.add_speech_bubble(result, txt, bubble_x_percent=x_pct, bubble_y_percent=y_pct)
            else:
                x_pct, y_pct = 50, 5
                if bubble_positions:
                    first_pos = list(bubble_positions.values())[0] if isinstance(bubble_positions, dict) else bubble_positions[0]
                    x_pct = first_pos.get("bubble_x_percent", 50)
                    y_pct = first_pos.get("bubble_y_percent", 5)
                result = self.add_speech_bubble(result, chinese_text, bubble_x_percent=x_pct, bubble_y_percent=y_pct)

        elif text_type in ["dialogue_with_thought", "dialogue_with_narration", "narration_with_thought", "narration_with_dialogue"]:
            # 混合类型：统一处理，跟踪偏移实现垂直堆叠
            texts = chinese_text if isinstance(chinese_text, list) else [chinese_text]

            # FIX-B1: 添加对话气泡索引跟踪，避免重叠
            # 先统计总对话数量
            total_dialogues = sum(1 for t in texts if "：「" in t or ":「" in t or "：\"" in t)
            dialogue_index = 0

            for txt in texts:
                # 使用strip_speaker_prefix统一处理，而不是硬编码字符串匹配
                if txt.startswith("旁白：") or txt.startswith("「"):
                    result, bar_height = self.add_monologue(
                        result, txt, position="bottom",
                        y_offset=position_offsets["bottom"]
                    )
                    position_offsets["bottom"] += bar_height + 5
                elif "内心：" in txt or "内心:" in txt:
                    result, bar_height = self.add_monologue(
                        result, txt, position="bottom",
                        y_offset=position_offsets["bottom"]
                    )
                    position_offsets["bottom"] += bar_height + 5
                elif "：「" in txt or ":「" in txt or "：\"" in txt:
                    # FIX-B1: 对话气泡使用索引计算位置，避免重叠
                    x_pct, y_pct = get_bubble_position_for_index(dialogue_index, total_dialogues)
                    result = self.add_speech_bubble(result, txt, bubble_x_percent=x_pct, bubble_y_percent=y_pct)
                    dialogue_index += 1

        return result


# =============================================================================
# 便捷函数
# =============================================================================

_default_service: Optional[TextOverlayService] = None


def get_text_overlay_service() -> TextOverlayService:
    """获取默认的TextOverlayService实例（单例）"""
    global _default_service
    if _default_service is None:
        _default_service = TextOverlayService()
    return _default_service


def process_shot_with_text(
    image: Image.Image,
    shot: Dict,
    bubble_positions: Optional[Dict] = None
) -> Image.Image:
    """
    便捷函数：处理单个shot的文字叠加

    Args:
        image: 原始图片
        shot: Shot配置字典
        bubble_positions: AI检测的气泡位置（可选）

    Returns:
        处理后的图片
    """
    service = get_text_overlay_service()
    return service.process_shot(image, shot, bubble_positions)
