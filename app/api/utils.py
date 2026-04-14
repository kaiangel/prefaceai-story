"""Utils API — OCR + PDF 解析 + AI 分析端点（独立模块）"""

import base64
import json
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from google import genai
from app.config import settings
from app.services.file_storage import validate_image, compress_image

logger = logging.getLogger("xuhua")

router = APIRouter(prefix="/api/utils", tags=["utils"])


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    """用 Gemini 识别图片中的文字"""
    # 校验文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持图片文件")

    # 校验文件大小 (10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过 10MB")

    prompt = "请识别这张图片中的所有文字，按原始排版顺序输出纯文本。只输出识别到的文字，不要添加解释。"

    # 主力: Gemini
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            b64_data = base64.standard_b64encode(contents).decode("utf-8")
            response = await client.aio.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=[
                    {"text": prompt},
                    {"inline_data": {"mime_type": file.content_type, "data": b64_data}},
                ],
            )
            result = {"text": response.text.strip()}
            logger.info(f"[OCR] ✅ 提取 {len(result.get('text',''))} 字")
            return result
        except Exception as e:
            logger.info(f"[OCR] Gemini 失败: {e}")

    # 备用: Claude Haiku
    if settings.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            b64_data = base64.standard_b64encode(contents).decode("utf-8")
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": file.content_type, "data": b64_data}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
            result = {"text": response.content[0].text.strip()}
            logger.info(f"[OCR] ✅ 提取 {len(result.get('text',''))} 字")
            return result
        except Exception as e:
            logger.info(f"[OCR] Claude Haiku 失败: {e}")

    return {"text": "", "error": "识别失败"}


@router.post("/parse-document")
async def parse_document(file: UploadFile = File(...)):
    """解析 PDF/TXT/MD 文档，提取文字"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少文件名")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    # 校验文件大小 (20MB)
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件不能超过 20MB")

    if ext == "pdf":
        try:
            import pdfplumber
            import io
            with pdfplumber.open(io.BytesIO(contents)) as pdf:
                text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
            text = text.strip()
            logger.info(f"[DocParse] ✅ {ext} 文件, 提取 {len(text)} 字")
            return {"text": text}
        except Exception as e:
            return {"text": "", "error": f"PDF 解析失败: {str(e)}"}

    elif ext in ("txt", "md", "markdown"):
        try:
            text = contents.decode("utf-8")
        except UnicodeDecodeError:
            text = contents.decode("gbk", errors="replace")
        text = text.strip()
        logger.info(f"[DocParse] ✅ {ext} 文件, 提取 {len(text)} 字")
        return {"text": text}

    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: .{ext}")


# ────────────────── AI 分析公用 helper ──────────────────

def _extract_json(text: str) -> dict:
    """从 LLM 响应中提取 JSON（处理 markdown 代码块和前后缀文本）"""
    text = text.strip()
    # 去掉 markdown 代码块
    if text.startswith("```"):
        # 去掉 ```json 或 ``` 开头
        first_newline = text.index("\n") if "\n" in text else 3
        text = text[first_newline + 1:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    # 提取第一个 { ... } 块
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


async def _vision_analyze(contents: bytes, content_type: str, prompt: str) -> dict:
    """调用 Gemini/Claude 视觉分析，返回 JSON dict"""
    b64_data = base64.standard_b64encode(contents).decode("utf-8")

    # 主力: Gemini
    if settings.GEMINI_API_KEY:
        try:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            response = await client.aio.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=[
                    {"text": prompt},
                    {"inline_data": {"mime_type": content_type, "data": b64_data}},
                ],
            )
            if not response.text:
                raise ValueError("Gemini 返回空文本")
            return _extract_json(response.text)
        except Exception as e:
            logger.info(f"[Analyze] Gemini 失败: {e}")

    # 备用: Claude Haiku
    if settings.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            response = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": content_type, "data": b64_data}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            )
            raw_text = response.content[0].text
            if not raw_text:
                raise ValueError("Claude 返回空文本")
            return _extract_json(raw_text)
        except Exception as e:
            logger.info(f"[Analyze] Claude Haiku 失败: {e}")

    raise HTTPException(status_code=500, detail="AI 分析失败")


async def _validate_and_read_image(file: UploadFile) -> tuple[bytes, str]:
    """校验上传图片，返回压缩后的 bytes + content_type"""
    contents = await file.read()
    img = validate_image(contents, file.content_type)
    compressed = compress_image(img)
    return compressed, "image/jpeg"


# ────────────────── 3 个分析端点 ──────────────────

STYLE_ANALYSIS_PROMPT = """You are a professional visual style analyst for an AI-powered story illustration system.

Analyze this image and extract its visual style characteristics. Your analysis will be used to enforce this exact style on all generated story illustrations.

Always respond with valid JSON only. No markdown code blocks, no explanation, no text before or after the JSON.

Analyze these dimensions:
1. COLOR PALETTE: Dominant colors, color temperature (warm/cool/neutral), saturation level, contrast range
2. LIGHTING: Light source direction, shadow hardness, ambient light quality, highlight behavior
3. BRUSHWORK/TEXTURE: Visible strokes, edge quality (sharp/soft/painterly), surface texture, medium feel
4. COMPOSITION STYLE: Typical framing, depth of field treatment, background approach
5. MEDIUM/GENRE: What art medium or genre this most resembles (e.g., watercolor, oil painting, anime, photography)
6. MOOD/ATMOSPHERE: Overall emotional tone conveyed by the visual treatment

Output format:
{
  "style_display_name": "A concise English name for this style (e.g., Warm Watercolor Illustration, Moody Film Photography)",
  "mandatory_keywords": ["8-10 English keywords that MUST appear in every image prompt to reproduce this style"],
  "forbidden_keywords": ["10-15 English keywords that must NEVER appear, as they would break this style"],
  "style_description": "A 100-300 word English prose description of this visual style. Describe how light behaves, what colors dominate, how edges and textures feel, what atmosphere pervades. Write as instructions to an image generator: 'You are painting in the style of...' This will be injected before every image generation prompt.",
  "quality_keywords": ["5-8 English quality enhancement keywords specific to this style"],
  "display_tags": ["3-5个中文标签，给用户看的风格特征摘要，如：暖色调、手绘质感、柔和光影"]
}"""


CHARACTER_ANALYSIS_PROMPT = """You are a professional character visual analyst for an AI-powered story illustration system.

Analyze this photo and extract the person's visual appearance characteristics. Your analysis will be used to: (1) guide story outline generation to match this character, and (2) generate consistent character reference images in various art styles.

Always respond with valid JSON only. No markdown code blocks, no explanation, no text before or after the JSON.

Focus on VISUAL characteristics only — what can be seen in the image:
1. GENDER & AGE: Apparent gender and age range
2. FACE: Face shape, skin tone, eye shape/color, eyebrow style, nose, lips, any facial hair
3. HAIR: Color, length, style, texture
4. BUILD: Height impression, body build (slim/medium/athletic/heavy)
5. CLOTHING: What they are currently wearing, from top to bottom, including accessories
6. DISTINCTIVE FEATURES: Any immediately noticeable features (glasses, scars, tattoos, piercings, birthmarks, jewelry)

Output format:
{
  "description_zh": "角色外貌的中文描述，30-50字。写法示例：约25岁年轻女性，黑色长直发及腰，鹅蛋脸，皮肤白皙，穿白色校服衬衫和深蓝色百褶裙，戴细框眼镜",
  "description_en": "Same description in English, 30-60 words. Example: A young woman around 25, with long straight black hair reaching her waist, oval face, fair skin, wearing a white school uniform shirt and dark blue pleated skirt, thin-framed glasses",
  "gender": "male / female",
  "age_range": "child / teen / young_adult / adult / middle_aged / elderly",
  "display_name": "一个简短的中文称呼，基于最显著特征（如：长发女生、眼镜男生、白发老人、红衣少女）"
}

Rules:
- description_zh and description_en must describe the SAME features, just in different languages
- Focus on permanent/semi-permanent features (face, hair, build) over temporary ones (expression, pose)
- If clothing is clearly a uniform or costume, note the type (school uniform, business suit, traditional dress)
- If the photo is unclear or partial (e.g., only showing a hand), describe what is visible and note limitations
- display_name should be 2-5 Chinese characters, immediately recognizable"""


SCENE_ANALYSIS_PROMPT = """You are a professional scene/environment visual analyst for an AI-powered story illustration system.

Analyze this photo and extract the scene's visual and spatial characteristics. Your analysis will be used to: (1) guide story outline generation to include this type of location, and (2) generate consistent scene reference images (interior/exterior).

Always respond with valid JSON only. No markdown code blocks, no explanation, no text before or after the JSON.

Analyze these dimensions:
1. SPACE TYPE: Is this an interior (indoor), exterior (outdoor), or a transitional space (doorway, porch, balcony)?
2. LOCATION CATEGORY: What type of place is this? (e.g., café, classroom, street, park, temple, bedroom)
3. TIME & WEATHER: If discernible — time of day, season, weather conditions
4. ATMOSPHERE: Overall mood and feeling of the space (cozy, grand, cramped, serene, bustling)
5. KEY VISUAL ELEMENTS: The 3-5 most prominent visual features that define this space (e.g., wooden beams, neon signs, cherry blossoms, bookshelves)
6. LIGHTING: Natural/artificial, direction, warmth, notable light effects (e.g., dappled sunlight, candlelight)

Output format:
{
  "description_zh": "场景的中文描述，30-50字。写法示例：日式传统和室，铺着榻榻米，障子门半开，午后阳光从庭院透入，角落放着插花",
  "description_en": "Same description in English, 30-60 words. Example: A traditional Japanese tatami room with sliding shoji doors half-open, afternoon sunlight streaming in from the garden, a flower arrangement in the corner",
  "location_type": "interior / exterior / both",
  "atmosphere": "用1-2个英文词描述氛围（如 warm_cozy / mysterious_quiet / vibrant_bustling / serene_natural）",
  "display_name": "场景的简短中文名，2-6字（如：日式和室、雨夜街头、咖啡馆、竹林小径）"
}

Rules:
- description_zh and description_en must describe the SAME features
- location_type determines whether the system generates interior reference, exterior reference, or both
- If the image shows both indoor and outdoor (e.g., a café with visible street through windows), use "both"
- Focus on spatial and environmental features, not people in the scene
- display_name should be evocative and specific enough to distinguish from generic locations"""


@router.post("/analyze-style")
async def analyze_style(file: UploadFile = File(...)):
    """分析风格参考图，返回 StyleEnforcement 格式"""
    compressed, ct = await _validate_and_read_image(file)
    result = await _vision_analyze(compressed, ct, STYLE_ANALYSIS_PROMPT)
    logger.info(f"[StyleAnalysis] ✅ style: {result.get('style_display_name')}, tags: {result.get('display_tags')}")
    return result


@router.post("/analyze-character")
async def analyze_character(file: UploadFile = File(...)):
    """分析角色参考图，返回角色特征"""
    compressed, ct = await _validate_and_read_image(file)
    result = await _vision_analyze(compressed, ct, CHARACTER_ANALYSIS_PROMPT)
    logger.info(f"[CharAnalysis] ✅ name: {result.get('display_name')}, gender: {result.get('gender')}, age: {result.get('age_range')}")
    return result


@router.post("/analyze-scene")
async def analyze_scene(file: UploadFile = File(...)):
    """分析场景参考图，返回场景特征"""
    compressed, ct = await _validate_and_read_image(file)
    result = await _vision_analyze(compressed, ct, SCENE_ANALYSIS_PROMPT)
    logger.info(f"[SceneAnalysis] ✅ name: {result.get('display_name')}, type: {result.get('location_type')}")
    return result
