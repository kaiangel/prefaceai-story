// TASK-CREATE-UPGRADE: Mock 数据，结构对齐后端实际接口

import type {
  StoryOutline,
  Shot,
  CharacterRef,
  StoryCard,
  StoryDetail,
  PreviewCharacter,
  PreviewScene,
} from "@/types/create";

// ============ Stage C: Mock Character Preview ============

export const mockPreviewCharacters: PreviewCharacter[] = [
  {
    id: "char_001",
    name: "陈默",
    description: "28岁程序员，内向沉稳，戴黑框眼镜",
    fullbodyUrl: "/comics/story-a/shot_01.png",
    adjustments: [],
  },
  {
    id: "char_002",
    name: "林小雨",
    description: "25岁插画师，短发，开朗却此刻脆弱",
    fullbodyUrl: "/comics/story-a/shot_02.png",
    adjustments: [],
  },
  {
    id: "char_003",
    name: "老张",
    description: "55岁出租车司机，热心肠，笑容憨厚",
    fullbodyUrl: "/comics/story-a/shot_03.png",
    adjustments: [],
  },
];

// ============ Stage C: Mock Scene Preview ============

export const mockPreviewScenes: PreviewScene[] = [
  {
    id: "scene_1",
    name: "雨夜公交站",
    description: "昏黄路灯下的积水路面，空无一人的站台，广告灯箱发出微弱的光",
    userEdit: "",
  },
  {
    id: "scene_2",
    name: "24小时便利店",
    description: "暖黄灯光透过落地玻璃窗洒出，货架整齐，收银台旁的热饮机冒着白烟",
    userEdit: "",
  },
  {
    id: "scene_3",
    name: "出租车内",
    description: "后视镜挂着平安符，仪表盘发出绿色微光，雨滴打在车窗上",
    userEdit: "",
  },
];

// ============ Stage B: Mock Outline ============

export const mockOutline: StoryOutline = {
  title: "雨夜公交站",
  titleEn: "Bus Stop in the Rain",
  summary:
    "深夜的公交站台，一个疲惫的加班族和一个刚失恋的女孩，因为同一把被遗忘的伞，在暴雨中产生了短暂而温暖的交集。",
  characters: [
    {
      id: "char_001",
      name: "陈默",
      nameEn: "Chen Mo",
      description: "28岁程序员，戴黑框眼镜，穿灰色卫衣，背双肩包",
      personality: "内向沉稳，不善表达但心思细腻",
    },
    {
      id: "char_002",
      name: "林小雨",
      nameEn: "Lin Xiaoyu",
      description: "25岁插画师，短发，穿米色风衣，眼眶微红",
      personality: "开朗但此刻脆弱，用微笑掩饰悲伤",
    },
  ],
  plotPoints: [
    { id: "pp_1", description: "深夜，陈默加班到最后一班公交", order: 1 },
    { id: "pp_2", description: "暴雨突降，林小雨跑进公交站避雨", order: 2 },
    { id: "pp_3", description: "座位上发现一把被遗忘的伞", order: 3 },
    { id: "pp_4", description: "两人无声地共用这把伞等车", order: 4 },
    { id: "pp_5", description: "公交到来，各自上路，心中留下温暖", order: 5 },
  ],
  endings: [
    {
      id: "end_1",
      description: "各自上了不同的公交，隔着车窗微笑挥手",
      isSelected: true,
    },
    {
      id: "end_2",
      description: "上了同一班公交，坐在相邻的位置，开始聊天",
      isSelected: false,
    },
    {
      id: "end_3",
      description: "陈默把伞留给了林小雨，自己淋雨跑向公交",
      isSelected: false,
    },
  ],
  mood: "温馨",
};

// ============ Stage D: Mock Shots ============

// 实际可用的 shot 文件（源数据跳过了 shot_13）
const MOCK_SHOT_FILES = [
  "shot_01", "shot_02", "shot_03", "shot_04", "shot_05", "shot_06",
  "shot_07", "shot_08", "shot_09", "shot_10", "shot_11", "shot_12",
  "shot_14", "shot_15", "shot_16", "shot_17", "shot_18", "shot_19",
];

export const mockShots: Shot[] = MOCK_SHOT_FILES.map((file, i) => ({
  shotId: i + 1,
  sceneId: Math.floor(i / 3) + 1,
  imagePrompt: `[Mock] Shot ${i + 1} image prompt`,
  narrationSegment: [
    "深夜十一点的城市，霓虹灯在湿漉漉的路面上拖出长长的倒影。",
    "陈默拖着疲惫的身体走出写字楼，抬头看了看阴沉的天空。",
    "公交站台空无一人，只有广告灯箱发出微弱的光。",
    "突然，暴雨倾盆而下。",
    "一个身影从雨中跑来——林小雨气喘吁吁地躲进站台。",
    "她的眼眶微红，雨水混着不知道是不是泪水的液体顺着脸颊滑下。",
    "两个陌生人在狭小的站台下沉默地站着。",
    "陈默注意到座位上有一把被遗忘的透明雨伞。",
    "他犹豫了一下，拿起伞撑开，默默向林小雨那边倾斜。",
    "林小雨愣了一下，抬头看向这个沉默的男生。",
    "\u201c谢谢。\u201d她轻声说，声音有些沙哑。",
    "陈默只是点了点头，目光望向雨幕。",
    "雨声成了他们之间唯一的对话。",
    "远处，公交车的灯光穿透雨帘缓缓驶来。",
    "林小雨深吸一口气，用力擦了擦眼角。",
    "\u201c今天真的很糟糕。\u201d她突然开口。",
    "\u201c但是谢谢你的伞。\u201d",
    "公交到了。陈默收起伞，两人一前一后上了车。",
  ][i],
  shotType: ["close up", "medium shot", "wide shot", "extreme close up", "full shot"][i % 5],
  cameraAngle: ["eye level", "low angle", "high angle", "dutch angle"][i % 4],
  textType: ["dialogue", "thought", "narration", "dialogue_with_thought", "narration_with_thought"][i % 5],
  chineseText: [`第${i + 1}句台词或旁白`],
  imageUrl: `/mock-shots/${file}.png`,
  charactersInScene: i < 4 ? ["char_001"] : i < 7 ? ["char_002"] : ["char_001", "char_002"],
}));

// ============ Stage C: Mock Generation Progress ============

const GENERATION_STEPS = [
  "正在构思故事大纲...",
  "正在设计角色外貌...",
  "正在编写分场剧本...",
  "正在创作分镜脚本...",
  "正在生成角色参考图...",
  "正在生成场景参考图...",
  "正在绘制第 1 张画面...",
  "正在绘制第 6 张画面...",
  "正在绘制第 12 张画面...",
  "正在绘制第 18 张画面...",
  "正在渲染文字...",
  "即将完成...",
];

export function mockGenerationProgress(
  onProgress: (progress: number, message: string) => void,
  onComplete: (shots: Shot[]) => void
): () => void {
  let step = 0;
  const interval = setInterval(() => {
    if (step < GENERATION_STEPS.length) {
      const progress = Math.round(((step + 1) / GENERATION_STEPS.length) * 100);
      onProgress(progress, GENERATION_STEPS[step]);
      step++;
    } else {
      clearInterval(interval);
      onComplete(mockShots);
    }
  }, 1500);

  return () => clearInterval(interval);
}

// ============ Custom Style: Mock AI Analysis ============

export async function mockStyleAnalysis(): Promise<string[]> {
  await new Promise((r) => setTimeout(r, 2000));
  return [
    "warm color palette",
    "soft lighting",
    "detailed backgrounds",
    "expressive characters",
    "cinematic composition",
  ];
}

// ============ Character: Mock AI Extraction ============

export async function mockCharacterExtract(
  file: File
): Promise<Omit<CharacterRef, "id">> {
  await new Promise((r) => setTimeout(r, 1500));
  return {
    name: "未命名角色",
    uploadedImage: file,
    uploadedImageUrl: URL.createObjectURL(file),
    extractedInfo: {
      gender: "unknown",
      ageAppearance: "young_adult",
      hairDescription: "dark hair, medium length",
      clothingDescription: "casual outfit",
    },
    portraitUrl: null,
    fullbodyUrl: null,
  };
}

// ============ Dashboard: Mock Story List ============

export const mockUserStories: StoryCard[] = [
  {
    id: "story_gen",
    title: "深夜便利店的秘密",
    coverImageUrl: "/mock-shots/shot_07.png",
    style: "illustration",
    length: "short",
    shotCount: 18,
    createdAt: "2026-03-22T08:00:00Z",
    updatedAt: "2026-03-22T08:12:00Z",
    status: "generating",
    canContinue: false,
  },
  {
    id: "story_001",
    title: "雨夜公交站",
    coverImageUrl: "/mock-shots/shot_01.png",
    style: "korean_webtoon",
    length: "short",
    shotCount: 18,
    createdAt: "2026-02-28T10:00:00Z",
    updatedAt: "2026-02-28T10:35:00Z",
    status: "complete",
    canContinue: true,
  },
  {
    id: "story_002",
    title: "最后一投",
    coverImageUrl: "/mock-shots/shot_05.png",
    style: "slam_dunk",
    length: "medium",
    shotCount: 32,
    createdAt: "2026-02-27T14:00:00Z",
    updatedAt: "2026-02-27T15:20:00Z",
    status: "complete",
    canContinue: true,
  },
  {
    id: "story_003",
    title: "星际迷途",
    coverImageUrl: "/mock-shots/shot_10.png",
    style: "cyberpunk",
    length: "flash",
    shotCount: 10,
    createdAt: "2026-02-26T09:00:00Z",
    updatedAt: "2026-02-26T09:15:00Z",
    status: "complete",
    canContinue: false,
  },
  {
    id: "story_004",
    title: "竹林听风",
    coverImageUrl: "/mock-shots/shot_14.png",
    style: "ink",
    length: "short",
    shotCount: 18,
    createdAt: "2026-02-25T16:00:00Z",
    updatedAt: "2026-02-25T16:30:00Z",
    status: "complete",
    canContinue: true,
  },
  {
    id: "story_005",
    title: "小兔子找月亮",
    coverImageUrl: "/mock-shots/shot_17.png",
    style: "children_book",
    length: "flash",
    shotCount: 10,
    createdAt: "2026-02-24T11:00:00Z",
    updatedAt: "2026-02-24T11:10:00Z",
    status: "complete",
    canContinue: false,
  },
];

// ============ Dashboard: Mock Story Detail ============

export function getMockStoryDetail(storyId: string): StoryDetail | null {
  const card = mockUserStories.find((s) => s.id === storyId);
  if (!card) return null;

  return {
    ...card,
    summary: "深夜的公交站台，一个疲惫的加班族和一个刚失恋的女孩，因为同一把被遗忘的伞，在暴雨中产生了短暂而温暖的交集。",
    characters: [
      { name: "陈默", description: "28岁程序员，戴黑框眼镜，穿灰色卫衣" },
      { name: "林小雨", description: "25岁插画师，短发，穿米色风衣" },
    ],
    shots: mockShots.slice(0, card.shotCount > 18 ? 18 : card.shotCount),
    mood: "温馨",
    aspectRatio: "2:3",
  };
}
