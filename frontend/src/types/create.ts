// TASK-CREATE-UPGRADE: DEC-013 Create 流程类型定义

// ============ Stage A: Input ============

export type StoryLength = "flash" | "short" | "medium" | "epic";
export type AspectRatio = "16:9" | "2:3" | "3:4" | "1:1";
export type ContinuationMode = "auto" | "user-directed";

export interface CharacterAnalysisResult {
  description_zh: string;
  description_en: string;
  gender: string;
  age_range: string;
  display_name: string;
}

export interface CharacterRef {
  id: string;
  name: string;
  uploadedImage: File | null;
  uploadedImageUrl: string | null;
  analysisResult: CharacterAnalysisResult | null;
  portraitUrl: string | null;
  fullbodyUrl: string | null;
}

export interface SceneAnalysisResult {
  description_zh: string;
  description_en: string;
  location_type: string;
  atmosphere: string;
  display_name: string;
}

export interface SceneRef {
  id: string;
  name: string;
  uploadedImage: File | null;
  uploadedImageUrl: string | null;
  analysisResult: SceneAnalysisResult | null;
  interiorUrl: string | null;
  exteriorUrl: string | null;
}

// ============ Stage B: Outline ============

export interface PlotPoint {
  id: string;
  description: string;
  order: number;
}

export interface OutlineCharacter {
  id: string;
  name: string;
  nameEn: string;
  description: string;
  personality: string;
  portrait_url?: string | null;  // UX-1: backend Stage 2 adds portrait after character design
}

export interface EndingOption {
  id: string;
  description: string;
  isSelected: boolean;
}

export interface OutlineScene {
  id: string;
  name: string;
  description: string;
  description_zh?: string; // F-3 (R3): Stage 1 Chinese scene description, preferred over English description
  locationType: string;
}

export interface StoryOutline {
  title: string;
  titleEn: string;
  summary: string;
  characters: OutlineCharacter[];
  plotPoints: PlotPoint[];
  endings: EndingOption[];
  mood: string;
  scenes: OutlineScene[];
}

// ============ Stage C-D: Generation & Preview ============

export interface Shot {
  shotId: number;
  sceneId: number;
  imagePrompt: string;
  narrationSegment: string;
  shotType: string;
  cameraAngle: string;
  textType: string;
  chineseText: string[];
  imageUrl: string | null;
  charactersInScene: string[];
  // D.17: content safety fields (populated when image generation is blocked)
  safetyAdvice?: string | null;
  errorMessage?: string | null;
}

// ============ Stage C: Generation Log ============

export interface GenerationLogEntry {
  timestamp: number;
  message: string;
  progress: number;
}

// ============ Stage D: BGM ============

export interface BGMTrack {
  id: string;
  name: string;
  artist: string;
  duration: string;
  mood: string;
  previewUrl: string | null;
}

// BGM Player — real API types (Wave 3, Step 6)
export type BgmMetaVersion = "mixed" | "en" | null;

export interface BgmInfo {
  bgm_url: string | null;
  bgm_volume: number;        // 0-1
  meta_version: BgmMetaVersion;
  credits_used: number;
  bgm_exists: boolean;
}

export interface BgmRegenerateResponse {
  success: boolean;
  bgm_url: string;
  meta_version: string;
  credits_used_this_call: number;
  total_credits_used: number;
}

export interface BgmVolumeResponse {
  success: boolean;
  bgm_volume: number;
}

// BGM player UI state
export type BgmStatus = "idle" | "loading" | "generating" | "ready" | "error";

export interface BgmPlayerState {
  status: BgmStatus;
  bgmUrl: string | null;
  volume: number;           // 0-100 (display), maps to 0-1 for API
  metaVersion: BgmMetaVersion;
  creditsUsed: number;
  errorMessage: string | null;
}

// ============ Stage E: Delivery ============

export type DeliveryFormat = "comic" | "video";

// ============ Dashboard ============

export interface StoryCard {
  id: string;
  title: string;
  coverImageUrl: string;
  style: string;
  length: StoryLength;
  shotCount: number;
  mood: string | null;
  createdAt: string;
  updatedAt: string;
  status: "draft" | "generating" | "complete";
  canContinue: boolean;
}

// ============ Auth ============

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl: string | null;
  plan?: string;
  credits?: number;
  createdAt: string;
}

export interface RegisterForm {
  email: string;
  password: string;
  inviteCode: string;
}

// ============ Dashboard: Story Detail ============

export interface StoryDetail extends StoryCard {
  summary: string;
  characters: { name: string; description: string; portrait_url?: string | null }[];  // Bug F: portrait_url from backend Stage 2
  shots: Shot[];
  mood: string | null;  // D.16: consistent with StoryCard.mood (string | null)
  aspectRatio: AspectRatio;
}

// ============ Stage C: Character/Scene Preview Checkpoints ============

export type GenerationSubPhase = "text-gen" | "char-preview" | "scene-preview" | "shot-gen";

export interface PreviewCharacter {
  id: string;
  name: string;
  description: string;
  fullbodyUrl: string;
  portraitUrl?: string | null;  // UX-1: real portrait from Stage 2 backend, null = fallback silhouette
  adjustments: string[];
}

export interface PreviewScene {
  id: string;
  name: string;
  description: string;
  userEdit: string;
}

// ============ Stage Navigation ============

export type CreateStage = "input" | "confirm" | "generate" | "preview" | "deliver";

// ============ Create State (全流程) ============

export interface CreateState {
  currentStage: CreateStage;

  // Stage A: Input
  idea: string;
  documentFile: File | null;
  documentText: string;
  length: StoryLength;
  aspectRatio: AspectRatio;
  stylePreset: string | null;
  customStyleImage: File | null;
  customStyleImageUrl: string | null;
  customStyleKeywords: string[];
  customStyleAnalysis: Record<string, unknown> | null;
  characters: CharacterRef[];
  scenes: SceneRef[];

  // Stage A → B bridge
  projectId: string | null;

  // Stage B: Outline
  outline: StoryOutline | null;
  outlineConfirmed: boolean;

  // Stage C: Generation + Checkpoints
  generationStatus: "idle" | "generating" | "complete" | "error";
  generationProgress: number;
  generationMessage: string;
  generationLog: GenerationLogEntry[];
  generationSubPhase: GenerationSubPhase;
  previewCharacters: PreviewCharacter[];
  previewScenes: PreviewScene[];
  charactersConfirmed: boolean;
  scenesConfirmed: boolean;
  shots: Shot[];

  // Stage D: Preview
  bgm: BGMTrack | null;

  // Stage D: BGM Player (Wave 3 real API)
  bgmPlayer: BgmPlayerState;

  // Stage E: Delivery
  deliveryFormat: DeliveryFormat;

  // Continuation
  continuationMode: ContinuationMode | null;
  continuationPrompt: string;
  previousStoryId: string | null;
}

// ============ Create Actions ============

export type CreateAction =
  | { type: "SET_STAGE"; payload: CreateStage }
  | { type: "SET_IDEA"; payload: string }
  | { type: "SET_DOCUMENT"; payload: { file: File | null; text: string } }
  | { type: "SET_LENGTH"; payload: StoryLength }
  | { type: "SET_ASPECT_RATIO"; payload: AspectRatio }
  | { type: "SET_STYLE_PRESET"; payload: string | null }
  | { type: "SET_CUSTOM_STYLE"; payload: { image: File | null; imageUrl: string | null; keywords: string[]; analysis?: Record<string, unknown> | null } }
  | { type: "ADD_CHARACTER"; payload: CharacterRef }
  | { type: "REMOVE_CHARACTER"; payload: string }
  | { type: "UPDATE_CHARACTER"; payload: { id: string; updates: Partial<CharacterRef> } }
  | { type: "ADD_SCENE"; payload: SceneRef }
  | { type: "REMOVE_SCENE"; payload: string }
  | { type: "SET_PROJECT_ID"; payload: string }
  | { type: "SET_OUTLINE"; payload: StoryOutline }
  | { type: "CONFIRM_OUTLINE" }
  | { type: "UPDATE_OUTLINE_TITLE"; payload: string }
  | { type: "UPDATE_OUTLINE_SUMMARY"; payload: string }
  | { type: "UPDATE_OUTLINE_CHARACTER"; payload: { id: string; updates: Partial<OutlineCharacter> } }
  | { type: "UPDATE_PLOT_POINTS"; payload: PlotPoint[] }
  | { type: "ADD_PLOT_POINT"; payload: PlotPoint }
  | { type: "DELETE_PLOT_POINT"; payload: string }
  | { type: "SELECT_ENDING"; payload: string }
  | { type: "SET_MOOD"; payload: string }
  | { type: "SET_GENERATION_SUB_PHASE"; payload: GenerationSubPhase }
  | { type: "SET_PREVIEW_CHARACTERS"; payload: PreviewCharacter[] }
  | { type: "SET_PREVIEW_SCENES"; payload: PreviewScene[] }
  | { type: "UPDATE_PREVIEW_CHARACTER"; payload: { id: string; updates: Partial<PreviewCharacter> } }
  | { type: "UPDATE_PREVIEW_SCENE"; payload: { id: string; userEdit: string } }
  | { type: "CONFIRM_CHARACTERS" }
  | { type: "CONFIRM_SCENES" }
  | { type: "START_GENERATION" }
  | { type: "CONTINUE_GENERATION" }
  | { type: "UPDATE_GENERATION_PROGRESS"; payload: { progress: number; message: string } }
  | { type: "GENERATION_COMPLETE"; payload: Shot[] }
  | { type: "GENERATION_ERROR"; payload: string }
  | { type: "UPDATE_SHOT_TEXT"; payload: { shotId: number; field: "narrationSegment" | "chineseText"; value: string | string[] } }
  | { type: "REGENERATE_SHOT"; payload: number }
  | { type: "REGENERATE_SHOT_SUCCESS"; payload: { shotId: number; imageUrl: string } }
  | { type: "DELETE_SHOT"; payload: number }
  | { type: "SET_BGM"; payload: BGMTrack | null }
  // BGM Player actions (Wave 3)
  | { type: "BGM_LOADING" }
  | { type: "BGM_GENERATING" }
  | { type: "BGM_READY"; payload: { bgmUrl: string; volume: number; metaVersion: BgmMetaVersion; creditsUsed: number } }
  | { type: "BGM_ERROR"; payload: string }
  | { type: "BGM_SET_VOLUME"; payload: number }
  | { type: "BGM_NO_BGM" }
  | { type: "SET_DELIVERY_FORMAT"; payload: DeliveryFormat }
  | { type: "SET_CONTINUATION_MODE"; payload: ContinuationMode | null }
  | { type: "SET_CONTINUATION_PROMPT"; payload: string }
  // UX-16: Hydrate full state from backend on URL-based deep link / refresh
  | { type: "HYDRATE_FROM_BACKEND"; payload: Partial<CreateState> & { projectId: string } }
  | { type: "RESET" };

// ============ Style Presets ============

export interface StylePreset {
  key: string;
  label: string;
  description: string;
  gradient: string; // CSS gradient fallback
  thumbnail: string; // path to style thumbnail image
}

// 前 8 个为默认显示，其余需点击"更多"展开
export const STYLE_PRESETS: StylePreset[] = [
  // — 默认显示 8 个 —
  { key: "pixar_3d", label: "皮克斯3D", description: "家庭温情", gradient: "linear-gradient(135deg, #4facfe, #00f2fe)", thumbnail: "/styles/pixar_3d.jpg" },
  { key: "ghibli", label: "吉卜力", description: "治愈系", gradient: "linear-gradient(135deg, #89f7fe, #66a6ff)", thumbnail: "/styles/ghibli.jpg" },
  { key: "illustration", label: "数字插画", description: "通用", gradient: "linear-gradient(135deg, #f6d365, #fda085)", thumbnail: "/styles/illustration.jpg" },
  { key: "ink", label: "中国水墨", description: "古风武侠", gradient: "linear-gradient(135deg, #2c3e50, #bdc3c7)", thumbnail: "/styles/ink.jpg" },
  { key: "slam_dunk", label: "井上雄彦", description: "运动/热血", gradient: "linear-gradient(135deg, #1a1a2e, #e94560)", thumbnail: "/styles/slam_dunk.jpg" },
  { key: "korean_webtoon", label: "韩漫", description: "都市恋爱", gradient: "linear-gradient(135deg, #667eea, #764ba2)", thumbnail: "/styles/korean_webtoon.jpg" },
  { key: "oil_painting", label: "油画", description: "复古文艺", gradient: "linear-gradient(135deg, #8B6914, #DAA520)", thumbnail: "/styles/oil_painting.jpg" },
  { key: "cyberpunk", label: "赛博朋克", description: "科幻", gradient: "linear-gradient(135deg, #0f0c29, #302b63)", thumbnail: "/styles/cyberpunk.jpg" },
  // — 点击"更多"展开 —
  { key: "realistic", label: "写实摄影", description: "都市情感", gradient: "linear-gradient(135deg, #2c3e50, #4ca1af)", thumbnail: "/styles/realistic.jpg" },
  { key: "cartoon", label: "卡通动画", description: "轻松喜剧", gradient: "linear-gradient(135deg, #f093fb, #f5576c)", thumbnail: "/styles/cartoon.jpg" },
  { key: "anime", label: "日式动画", description: "青春校园", gradient: "linear-gradient(135deg, #a18cd1, #fbc2eb)", thumbnail: "/styles/anime.jpg" },
  { key: "watercolor", label: "水彩", description: "文艺清新", gradient: "linear-gradient(135deg, #a1c4fd, #c2e9fb)", thumbnail: "/styles/watercolor.jpg" },
  { key: "children_book", label: "儿童绘本", description: "童话寓言", gradient: "linear-gradient(135deg, #ffecd2, #fcb69f)", thumbnail: "/styles/children_book.jpg" },
  { key: "manga", label: "日漫", description: "热血/搞笑", gradient: "linear-gradient(135deg, #ff9a9e, #fecfef)", thumbnail: "/styles/manga.jpg" },
  { key: "pixel", label: "像素艺术", description: "怀旧游戏", gradient: "linear-gradient(135deg, #11998e, #38ef7d)", thumbnail: "/styles/pixel.jpg" },
  // — Phase 1 新增 13 个风格 —
  { key: "ukiyo_e", label: "浮世绘", description: "日本传统", gradient: "linear-gradient(135deg, #c2185b, #f48fb1)", thumbnail: "/styles/ukiyo_e.jpg" },
  { key: "vintage_film", label: "复古胶片", description: "80/90怀旧", gradient: "linear-gradient(135deg, #d4a574, #8b6914)", thumbnail: "/styles/vintage_film.jpg" },
  { key: "pencil_sketch", label: "铅笔素描", description: "文艺手绘", gradient: "linear-gradient(135deg, #636363, #a2a2a2)", thumbnail: "/styles/pencil_sketch.jpg" },
  { key: "chibi", label: "Q版卡通", description: "萌系搞笑", gradient: "linear-gradient(135deg, #ff9a9e, #fad0c4)", thumbnail: "/styles/chibi.jpg" },
  { key: "dark_fantasy", label: "暗黑奇幻", description: "魔幻/哥特", gradient: "linear-gradient(135deg, #0f0f23, #4a1942)", thumbnail: "/styles/dark_fantasy.jpg" },
  { key: "pop_art", label: "波普艺术", description: "时尚潮流", gradient: "linear-gradient(135deg, #ff0844, #ffb199)", thumbnail: "/styles/pop_art.jpg" },
  { key: "paper_cut", label: "中国剪纸", description: "民俗文化", gradient: "linear-gradient(135deg, #d32f2f, #ff6659)", thumbnail: "/styles/paper_cut.jpg" },
  { key: "steampunk", label: "蒸汽朋克", description: "维多利亚机械", gradient: "linear-gradient(135deg, #5d4037, #d4a574)", thumbnail: "/styles/steampunk.jpg" },
  { key: "art_nouveau", label: "新艺术", description: "Mucha装饰", gradient: "linear-gradient(135deg, #6d9b7b, #d4a574)", thumbnail: "/styles/art_nouveau.jpg" },
  { key: "noir", label: "黑色电影", description: "高反差黑白", gradient: "linear-gradient(135deg, #1a1a1a, #4a4a4a)", thumbnail: "/styles/noir.jpg" },
  { key: "comic_western", label: "欧美漫画", description: "超英/动作", gradient: "linear-gradient(135deg, #1565c0, #e53935)", thumbnail: "/styles/comic_western.jpg" },
  { key: "pastel_dream", label: "梦幻马卡龙", description: "柔美少女", gradient: "linear-gradient(135deg, #fbc2eb, #a6c1ee)", thumbnail: "/styles/pastel_dream.jpg" },
  { key: "gothic", label: "哥特风", description: "暗色/神秘", gradient: "linear-gradient(135deg, #1a0a2e, #6a1b4d)", thumbnail: "/styles/gothic.jpg" },
];

export const STYLE_PRESETS_DEFAULT_COUNT = 10;

// ============ Length Options ============

export interface LengthOption {
  key: StoryLength;
  label: string;
  shotCount: string;
  description: string;
  icon: string; // lucide icon name
}

export const LENGTH_OPTIONS: LengthOption[] = [
  { key: "flash", label: "快闪", shotCount: "~10张", description: "一个片段、一个瞬间", icon: "Zap" },
  { key: "short", label: "短篇", shotCount: "~18张", description: "一个完整小故事", icon: "BookOpen" },
  { key: "medium", label: "中篇", shotCount: "~36张", description: "有起承转合的完整叙事", icon: "Layers" },
  { key: "epic", label: "长篇", shotCount: "36张+续写", description: "多章节连续故事", icon: "Library" },
];

// ============ Mood Options ============

export const MOOD_OPTIONS: string[] = [
  "温馨", "紧张", "幽默", "感人", "治愈", "热血", "悬疑", "浪漫",
];

// ============ BGM Tracks (Mock) ============

export const BGM_TRACKS: BGMTrack[] = [
  { id: "bgm_01", name: "城市漫步", artist: "序话原创", duration: "3:24", mood: "温馨", previewUrl: null },
  { id: "bgm_02", name: "暴风前夜", artist: "序话原创", duration: "2:58", mood: "紧张", previewUrl: null },
  { id: "bgm_03", name: "阳光午后", artist: "序话原创", duration: "3:10", mood: "幽默", previewUrl: null },
  { id: "bgm_04", name: "离别站台", artist: "序话原创", duration: "4:02", mood: "感人", previewUrl: null },
  { id: "bgm_05", name: "星空下", artist: "序话原创", duration: "3:35", mood: "治愈", previewUrl: null },
  { id: "bgm_06", name: "燃烧吧", artist: "序话原创", duration: "2:45", mood: "热血", previewUrl: null },
];
