# Music Prompt Engineering Skill

> AI 音乐/歌曲生成 Prompt 工程能力包。当 AI-ML 或任何 agent 需要为序话Story 的故事生成 BGM、主题曲、歌词时调用此 skill。

---

## 触发条件

以下场景应调用此 skill：
- 为故事生成 BGM / 背景音乐 prompt
- 为故事生成主题曲 / 片尾曲歌词 + 音乐 prompt
- 评审音乐 prompt 质量
- 描述音乐风格、情绪、乐器选择
- 需要跨感官联想（画面 → 声音）

## 使用方式

```
1. 读 knowledge/mureka_model.md — 理解 Mureka 模型特性和参数
2. 读 knowledge/music_theory.md — 音乐术语速查
3. 读 knowledge/cross_sensory.md — 画面→声音映射
4. 读 knowledge/lijigang_music.md — 压缩/场域/种子原则
5. 参考 templates/ 下的模板和示例
```

## 能力覆盖

| 能力维度 | 文件 |
|---------|------|
| Mureka 模型原理 + 参数敏感度 | `knowledge/mureka_model.md` |
| 音乐专业术语 + 流派 + 乐器 + 技法 | `knowledge/music_theory.md` |
| 跨感官联想（画面→声音） | `knowledge/cross_sensory.md` |
| 李继刚式 Prompt 哲学在音乐的应用 | `knowledge/lijigang_music.md` |
| BGM Prompt 5 层模板 | `templates/bgm_prompt.md` |
| 歌曲 Prompt 模板 | `templates/song_prompt.md` |
| 30+ 优秀 Prompt 示例 | `templates/examples.md` |

## 核心原则

**音乐 Prompt = 场域(Genre) + 骨架(Tempo) + 肌肉(Instruments) + 呼吸(Mood Curve) + 灵魂(Narrative Imagery)**

- 不是命令模型"生成悲伤的音乐"
- 而是描绘一个场景"雨水打在深夜空荡的街道上"，让模型自然感受到情绪
- 每个词都要携带音乐信息，不写废话
- 英文为主体（音乐术语精确），中文情绪意象点缀（Mureka 中文理解好）

## 故事篇幅与 BGM 时长

| 故事篇幅 | shots | 估算播放时长 | Mureka 实际输出 | 时长适配方案 |
|---------|:-----:|:----------:|:------------:|:----------:|
| 快闪 | ~10 张 | ~40-60 秒 | ~3 分钟 | ffmpeg 裁剪 + 淡出 |
| 短篇 | ~18 张 | ~1-2 分钟 | ~3 分钟 | ffmpeg 裁剪 + 淡出 |
| 中篇 | ~36 张 | ~2.5-4 分钟 | ~3 分钟 | 直接使用（自然匹配） |

> **⚠️ 实测结论（2026-04-16）**：Prompt 暗示词（如 "short 60-second piece"）无法控制时长，模型完全无视。需要短 BGM 只能后处理裁剪。

---

## 与序话Story 的集成

```
Pipeline Stage 5 完成 → 读故事大纲+剧本+mood
    ↓
Haiku 读故事内容 + 此 skill 的知识 → 生成音乐 prompt
    ↓
POST Mureka /v1/instrumental/generate (纯音乐 BGM)
或 POST /v1/song/generate (歌曲，需要歌词)
    ↓
轮询 query/{task_id} → 拿到 mp3
    ↓
存为故事 BGM → 交付时合成到视频/漫画包
```
