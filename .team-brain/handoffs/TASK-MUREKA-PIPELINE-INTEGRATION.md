# TASK-MUREKA-PIPELINE-INTEGRATION

> **完整集成任务规格书**
>
> - 创建: 2026-04-21 | PM
> - 完成: 2026-04-21 17:55 | PM
> - 状态: ✅ **全部完成（Wave 1-4 + VPS 部署）**
> - 优先级: P1

## ✅ 最终完成状态（2026-04-21 17:55）

| Wave | 状态 | 主要产出 |
|------|------|---------|
| Wave 1 数据层 | ✅ | music_hint × 28 styles、67 MUSIC_HINTS、4 BGM 列、MUREKA_API_KEY 配置 |
| Wave 2 服务层 | ✅ | story_music_extractor / music_generation_service / ffmpeg_post_processor，E2E 跑通 |
| Wave 3 API | ✅ | 4 BGM REST 端点 + BgmPlayer.tsx 5 状态 + StageD 集成 build 20 路由 0 错 |
| Wave 4 集成测试 | ✅ | @tester 6P/2W/1S，PM 修 style_preset→get_music_hint bug，Founder 听 3 mp3 通过 |
| VPS 部署 | ✅ | commit `b998cbf` push + rsync + MUREKA_API_KEY + docker rebuild + /health healthy（PM 代执行，@devops Bash 二次被拒）|

**MVP 后 PENDING (P3，已记录 PENDING.md)**: music_hint 在 Haiku 层效用有限、秋梨膏温暖故事金句重试、自定义 BGM 上传

---

> 以下为任务设计原稿，保留归档 ——

---

## 1. 背景

从 2026-04-16 Mureka 手工测试 → 2026-04-17 V4 极简 prompt → 2026-04-18 语言策略研究 + Haiku A/B/C → 2026-04-20 V2 meta-prompt 升级 → 2026-04-21 盲听揭盲：
- **质量验证通过**: Haiku 4.5 + `meta_en_v2` meta-prompt 质量与 PM 手写（Sonnet agent + 完整 context）并列第一
- **成本优势**: Haiku 路径 ~$0.008/首 vs Sonnet agent 路径 ~$0.085/首（便宜 10 倍）
- **下一步**: 集成到 Pipeline 真实跑起来，供用户在 Stage D 预览/交付时使用

---

## 2. Founder 已确认的 12 条产品决策（2026-04-18 ~ 2026-04-21）

| # | 决策 | 落地点 |
|---|------|-------|
| 1 | **不做 TTS / Whisper / 音画对齐** | Phase 3 简化：只有 BGM，没有 TTS 旁白 |
| 2 | **默认 meta-prompt: `meta_en_v2.md`**（v3 quote picking 待验证） | `music_generation_service.py` 默认值 |
| 3 | **换 BGM 逻辑: en → mixed → 之后都 en 重试** | Stage D 的换 BGM 按钮后端逻辑 |
| 4 | **每次用户生成一次完整故事 = 1 章 = 1 首 BGM**（快闪/短篇/中篇都这样）| 每个 generation session 对应一首 BGM，不按 chapter 拆 |
| 5 | **Mureka 水印处理: FFmpeg 切末尾 4 秒** | `ffmpeg_post_processor.py` |
| 6 | **时长适配: FFmpeg 根据故事播放时长裁剪 + 淡入淡出** | 同上 |
| 7 | **风格映射: 方案 B — 每个风格预设手动加 `music_hint` 字段** | 80+ 风格配置更新 + meta-prompt 加 `{{visual_style_hint}}` 占位符 |
| 8 | **失败降级: 3 次重试后跳过 BGM，不卡 Pipeline** | `music_generation_service.py` error handler |
| 9 | **Prompt caching: 启用 Anthropic prompt cache，但必须保证质量无损** | 静态 meta-prompt 放 system（cache 住），动态故事数据放 user |
| 10 | **重新生成不限次数，扣 credits（mock）** | 每次 regenerate = credits_used += X |
| 11 | **QA 自动化: 静音检测 + 音量电平 两者都做** | FFmpeg silencedetect + LUFS 检测 |
| 12 | **Credits 机制 mock 等级 A2: 后端记 `credits_used` 到 user 表，无真实支付系统** | User DB schema 加字段 |

### 音量控制（补充决策）

**采用方案 B（破坏性）**：
- DB: `chapters` 表加 `bgm_volume FLOAT DEFAULT 1.0`
- Frontend: 调节滑块时 PATCH 到后端
- 交付（模式 1 和 模式 2）: FFmpeg 应用音量系数重新渲染，交付的 mp3/视频音量 = 用户调过的音量

---

## 3. 生成流程（最终版）

```
Stage C (Phase 1-5) 完成
    ↓
Phase 3 (简化版，只有 BGM，没有 TTS)
    ├── 1. 提取故事数据:
    │      - 从 confirmed_outline_json（不是 raw_outline_json）读 outline
    │      - 从 screenplay 读 per-scene atmosphere 字段
    │      - per-scene 数组字段限 6 个 scene（中篇故事超过时取关键 plot_points 对应 scene）
    │      - full_narration: 拼接所有 scene 的 narration
    │      - 从用户选的 style_preset 读 music_hint 字段
    ├── 2. 调 Haiku API:
    │      - model: claude-haiku-4-5
    │      - system: meta_en_v2 的静态部分（prompt cache 命中）
    │      - user: 故事数据 + full_narration（+ style music_hint）
    │      - 输出: ≤400 字符 music prompt（含金句意象）
    ├── 3. 调 Mureka API:
    │      - model: auto (mureka-9)
    │      - n: 1
    │      - 3 次重试，失败跳过不卡 Pipeline
    ├── 4. FFmpeg 后处理:
    │      - 切末尾 4 秒（Mureka 水印）
    │      - 根据故事播放时长裁剪（快闪 60s / 短篇 90s / 中篇 180s）
    │      - 淡入淡出（开头 1s 淡入 + 结尾 3s 淡出）
    ├── 5. QA 检查:
    │      - silencedetect (-30dB / 5s)：超标重试 1 次
    │      - LUFS loudness (-23 ~ -14 范围)：超标记录但不重试
    ├── 6. 存储:
    │      - 文件: {story_dir}/bgm.mp3
    │      - DB: chapters.bgm_url + chapters.bgm_meta_version（记录用了哪个 meta-prompt）
    └── 7. credits_used += 10（生成 BGM 扣点）
        ↓
Stage D 预览页面
    ├── 播放器（shot 图片序列 + BGM 双轨，BGM 音量可调）
    ├── 换 BGM 按钮:
    │    - 第 1 次点: 切 meta_mixed_v2（en → mixed）
    │    - 第 2 次及以后点: 都用 meta_en_v2 重试（利用 AI 随机性）
    │    - 每次扣 credits_used（mock）
    ├── 重新生成 BGM 按钮: 同一 meta-prompt 再跑（不限次，扣 credits mock）
    └── 音量滑块: PATCH chapters.bgm_volume（影响交付时 FFmpeg 渲染）
        ↓
Stage E 交付
    ├── 模式 1 打包: shot 图 + bgm.mp3（已应用 volume）
    └── 模式 2 视频: FFmpeg 合成 shot 序列 + BGM（已应用 volume）
```

---

## 4. V2 测试 → 生产集成的 5 个 parity 风险点

| # | 风险 | V2 测试环境 | 生产环境差异 | 处理方案 |
|---|------|-----------|------------|---------|
| 1 | **narration_quotes 动态化** | Backend 硬编码了年夜饭 2 句金句 | 每个用户故事都不同，不能硬编码 | 🔄 当前正在测 TASK-HAIKU-QUOTE-EXTRACTION 验证方案 A（Haiku 自挑）；失败则切方案 B（Sonnet 预调用） |
| 2 | **per-scene 数组字段上限** | 年夜饭 5 scenes 的数组可控 | 中篇 36 shots 可能 10+ scenes | 提取时限 6 scene 上限（超过取关键 plot_points 对应 scene） |
| 3 | **风格差异** | 只测"韩漫"+"warm_nostalgic_yet_tense" | 80+ 风格 × 20+ mood 组合 | 方案 B：每个风格预设加 `music_hint` 字段；meta-prompt 加 `{{visual_style_hint}}` 占位符 |
| 4 | **confirmed_outline_json** | 直接用 Pipeline 自动生成的 raw outline | 用户在 Stage B 可能编辑 mood / plot_points / ending | 提取必须从 `confirmed_outline_json` 读，不从 `raw_outline_json` 读 |
| 5 | **Prompt cache 质量保证** | 测试没启用 cache | 生产启用 cache 省 94% 成本 | 严格分层：静态 meta-prompt（V4 哲学 + cross_sensory + 示例 + Quote Protocol + 输出要求）→ system prompt（cache 住）；故事数据 + style_hint + full_narration → user prompt（每次变化） |

---

## 5. 子任务拆解骨架（等 quote extraction 通过后细化）

| Step | 任务 | 负责人 | 状态 | 产出 |
|------|-----|:----:|:---:|-----|
| A | v3.2 meta-prompt 方案 A 最终版 | @ai-ml Opus+Sonnet | ✅ | `meta_mixed_v3_quote_picking.md` |
| B | 95 风格 music_hint 字段 | @ai-ml Sonnet | ✅ | style_enforcer.py + style_config.py |
| 1 | `app/services/story_music_extractor.py` | @backend Sonnet | ✅ | 15 字段提取，PM 3 测试 PASS |
| 2 | `app/services/music_generation_service.py` | @backend Sonnet | ✅ | 22K, 8 步 flow, PM E2E 年夜饭 PASS |
| 3 | `app/services/ffmpeg_post_processor.py` | @backend Sonnet | ✅ | ebur128 LUFS (-15.5 验证) + 静音检测 |
| 4 | Pipeline orchestrator Stage 6 + DB | @backend Sonnet | ✅ | chapter.py 加 4 列 + alembic 文件（待 Ben/DevOps 跑 MySQL ALTER TABLE）|
| 5 | Stage D BGM REST API 4 端点 | @backend Sonnet | ✅ | chapters.py L1530-1913，asyncio.to_thread 包装 |
| 6 | Stage D Frontend BgmPlayer | @frontend Sonnet | ✅ | BgmPlayer.tsx 新建，build 20 路由 0 错 |
| 7 | 集成测试 | @tester | 🟡 待启动 | 3 风格 × QA × 失败降级 |
| 8 | VPS 部署 | @devops | 🟡 待启动 | .env.production + MySQL ALTER TABLE |

### 依赖关系

```
A, B (并行) → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (生产部署)
```

---

## 6. MVP 后迭代（已记录不阻塞）

- 用户上传自定义 BGM（跳过 Mureka 生成）— 见 PENDING.md "用户自定义 BGM 上传"
- 冷门情绪 BGM 验证（狂喜/疯狂/超现实）
- 多章节故事 BGM 策略优化（当前每个生成 session = 1 首）
- Prompt cache hit rate 监控
- API 成本归档到 `api_cost_logs` 表（依赖 TASK-API-COST-TABLE 完成）

---

## 7. 成本估算

- **生成 1 首 BGM**: ~$0.008（Haiku 用 prompt cache）+ ~$0.02（Mureka auto 生成）= **~$0.028/首**
- **用户换 BGM**: +$0.028（重跑 Haiku + Mureka，Haiku 因 cache 命中极低成本）
- **用户重新生成**: 同上
- **100 万用户场景**: ~$28,000 BGM 成本（credits 转嫁给用户）

---

## 8. 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|------|:---:|:---:|-----|
| Haiku 4.5 稳定性（偶尔输出不符合 V4 哲学）| 中 | 中 | 失败降级 + 重试机制；用户可换/重生成 |
| Mureka API 中文 JSON 编码问题（EP-015）| 低 | 高 | 已用 Python urllib + ensure_ascii=False；有防护 |
| SSL 证书链问题（EP-017 新增）| 低 | 高 | 已用 certifi 全局 default context；有防护 |
| Pipeline 时长超时（BGM 生成约 170s）| 中 | 中 | 和 shot 生图并行执行（不在 critical path）|
| Mureka 账户余额不足 | 低 | 高 | 余额监控 + 预警（@backend + @devops）|
| 用户大量重新生成刷爆成本 | 低 | 中 | credits 机制天然限速（用户 credits 用完必须充值）|

---

## 9. 历史决策链路（溯源）

所有决策和发现的完整链路保留在：
- `.team-brain/TEAM_CHAT.md` 2026-04-16 ~ 2026-04-21 区段
- `.team-brain/analysis/MUSIC_PROMPT_LANGUAGE_RESEARCH.md` — 外部调研报告
- `.claude/skills/music-prompt/` — 音乐 prompt 工程 Skill 知识库
- `.claude/skills/music-prompt/templates/story_input_format.md` — 故事输入格式规范
- `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/` — 所有 meta-prompt v1/v2/v3 版本
- `scripts/test_haiku_music_prompt_languages.py` — 测试脚本（生产集成时复用 `call_haiku` / `call_mureka` 函数）

---

## 10. 审查和推进节点

| 节点 | 触发条件 | 决策人 |
|------|--------|------|
| 当前阻塞 | TASK-HAIKU-QUOTE-EXTRACTION 测试通过 | Founder |
| 方案 A/B 选择 | PM 评审 12 个输出后 | PM 推荐 + Founder 批准 |
| 子任务 A/B 开始 | 方案决定后 | PM spawn |
| 集成测试 → 部署 | 全部子任务完成后 | Tester 验证 + Founder 批准 |
| 生产上线 | DevOps 部署完成后 | Founder 最终签字 |
