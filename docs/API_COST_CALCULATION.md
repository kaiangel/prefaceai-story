# 序话Story API 成本计算（官方定价版）

> **版本**: V5
> **日期**: 2026-04-15
> **校准数据**: 2026-04-14 Anthropic Dashboard (292,794 Sonnet tokens / 2 故事) + Google Dashboard (2.82 AUD / 26 张)
> **定价来源**: [Gemini API Pricing](https://ai.google.dev/gemini-api/docs/pricing) + [Claude API Pricing](https://docs.anthropic.com/en/docs/about-claude/pricing)

---

## 一、官方定价表

### Claude (Anthropic)

| 模型 | Input (/M tokens) | Output (/M tokens) | 用途 |
|------|:-----------------:|:------------------:|------|
| **Sonnet 4.6** | $3.00 | $15.00 | Stage 1-4 文本生成（主力） |
| **Haiku 4.5** | $1.00 | $5.00 | "调整画面"功能（轻量修改 image_prompt） |

### Gemini (Google)

| 模型 | Text Input (/M) | Image Input (per 张) | Text Output (/M) | Image Output (per 张) | 用途 |
|------|:---------------:|:-------------------:|:-----------------:|:--------------------:|------|
| **3.1 Flash Image (NB2)** | $0.25 | $0.00028 (1120 tokens × $0.25/M) | $1.50 | **$0.0672** (1120 tokens × $60/M) | 参考图 + Shot 生成（主力） |
| **3.1 Flash Lite** | $0.25 | $0.00028 (同上) | $1.50 | — | 上传图片分析 + Prompt 翻译安全网 |

### NB2 图像输出按分辨率

| 分辨率 | Output Tokens | 每张费用 |
|--------|:------------:|:--------:|
| 0.5K (512px) | 747 | $0.045 |
| **1K (1024px)** | **1120** | **$0.067** ← 我们用的 |
| 2K (2048px) | 1680 | $0.101 |
| 4K (4096px) | 2520 | $0.151 |

### 其他

| 服务 | 定价 | 用途 |
|------|------|------|
| 火山引擎 TTS | ~$0.002/千字 | 旁白语音合成（未来） |
| OpenAI Whisper | $0.006/分钟 | 语音转文字 + 时间戳（未来） |

---

## 二、完整故事生成流程 — 每个环节的 Input 和 Output

### 用户操作 → API 调用映射

```
用户上传自定义图片 (StageA)
    │
    ├── [Gemini 3.1 Flash Lite] 风格图片 → text 分析
    ├── [Gemini 3.1 Flash Lite] 角色图片 × N → text 分析
    └── [Gemini 3.1 Flash Lite] 场景图片 × N → text 分析
         Input: 图片 (1120 tokens) + prompt (~500 tokens)
         Output: text JSON (~800 tokens)

用户点击生成大纲
    │
    └── [Claude Sonnet 4.6] Stage 1 大纲生成
         Input: system prompt + idea + style + 角色描述 + 场景描述 (~4-5K tokens)
         Output: outline JSON (~3-5K tokens)

用户确认大纲 → Pipeline 启动
    │
    ├── [Claude Sonnet 4.6] Stage 2 角色设计
    │    Input: system prompt + outline (~5-6K tokens)
    │    Output: characters JSON with physical/clothing (~4-8K tokens)
    │
    ├── [Claude Sonnet 4.6] Stage 3 剧本（分 batch）
    │    Input: system prompt + outline + characters × batch (~8K/batch)
    │    Output: screenplay JSON with scenes + action_beats (~5-6K/batch)
    │
    ├── [Claude Sonnet 4.6] Stage 4 分镜（每场景一次）
    │    Input: system prompt + 全部角色数据 + 场景 + 全局方向 (~5-8K/场景)
    │    Output: shots JSON with image_prompt + camera + text_overlay (~3-4K/场景)
    │    ⚠️ 这是 Sonnet 最大的消耗项！每场景的 input 含完整角色数据
    │
    ├── [Gemini 3.1 Flash Image NB2] Stage 5a 参考图生成
    │    每张参考图:
    │      Input: text prompt (~800 tokens) + [portrait 图 input for fullbody] (1120 tokens)
    │      Output: 1 张图像 (1120 tokens @ $60/M = $0.067)
    │
    └── [Gemini 3.1 Flash Image NB2] Stage 5b Shot 生成
         每张 shot:
           Input: B' prompt text (~950-1200 tokens) + 参考图 images (每张 1120 tokens)
           Output: 1 张图像 (1120 tokens @ $60/M = $0.067)

用户在预览页调整画面
    │
    └── [Claude Haiku 4.5] 修改 image_prompt
         Input: system prompt + 原始 image_prompt + 中文意图 (~800 tokens)
         Output: 修改后的 image_prompt (~600 tokens)
```

---

## 三、短篇成本明细 (3 角色, 7 场景, 21 shots)

| # | 环节 | 模型 | Input 明细 | Output 明细 | 费用 |
|---|------|------|-----------|------------|-----:|
| 0 | 上传图片分析 ×7 | Flash Lite | 7×(1120+500) tokens | 7×800 tokens | $0.011 |
| 1 | Stage 1 大纲 | Sonnet 4.6 | ~4K tokens | ~3K tokens | — |
| 2 | Stage 2 角色 | Sonnet 4.6 | ~5K tokens | ~4K tokens | — |
| 3 | Stage 3 剧本 | Sonnet 4.6 | ~15K tokens (batch) | ~10K tokens | — |
| 4 | Stage 4 分镜 ×7 场景 | Sonnet 4.6 | ~56K tokens (7×8K) | ~24K tokens | — |
| | **Sonnet 小计** | | **~102K input** | **~44K output** | **$0.964** |
| 5a | 参考图生成 ×14 | NB2 | 14×800 text + 5×1120 image | 14×1120 image | $0.945 |
| 5b | Shot 生成 ×21 | NB2 | 21×950 text + 63×1120 image | 21×1120 image | $1.434 |
| 6 | Prompt 翻译 ~1 次 | Flash Lite | ~1500 tokens | ~1000 tokens | $0.002 |
| 7 | 调整画面 ×5 | Haiku 4.5 | 5×800 tokens | 5×600 tokens | $0.019 |
| 8 | TTS + Whisper | 火山/OpenAI | 2200 字 + 3 分钟 | — | $0.022 |
| | **总计** | | | | **$3.40** |

### 费用构成

```
Sonnet 文本生成:     $0.96  (28%)
NB2 Shot 生成:       $1.41  (42%) ← 最大项
NB2 参考图生成:      $0.94  (28%)
其他:                $0.07  (2%)
─────────────────────────────
总计:                $3.40
```

---

## 四、中长篇满配成本明细 (6 角色, 12 场景, 45 shots)

| # | 环节 | 模型 | Input 明细 | Output 明细 | 费用 |
|---|------|------|-----------|------------|-----:|
| 0 | 上传图片分析 ×13 | Flash Lite | 13×(1120+500) tokens | 13×800 tokens | $0.021 |
| 1 | Stage 1 大纲 | Sonnet 4.6 | ~5K tokens | ~5K tokens | — |
| 2 | Stage 2 角色 ×6 | Sonnet 4.6 | ~6K tokens | ~8K tokens | — |
| 3 | Stage 3 剧本 ×3 batch | Sonnet 4.6 | ~26K tokens | ~18K tokens | — |
| 4 | Stage 4 分镜 ×12 场景 | Sonnet 4.6 | ~120K tokens (12×10K) | ~48K tokens | — |
| | **Sonnet 小计** | | **~184K input** | **~79K output** | **$1.734** |
| 5a | 参考图生成 ×28 | NB2 | 28×800 text + 10×1120 image | 28×1120 image | $1.890 |
| 5b | Shot 生成 ×45 | NB2 | 45×1200 text + 158×1120 image | 45×1120 image | $3.082 |
| 6 | Prompt 翻译 ~2 次 | Flash Lite | ~3000 tokens | ~2000 tokens | $0.004 |
| 7 | 调整画面 ×10 | Haiku 4.5 | 10×800 tokens | 10×600 tokens | $0.038 |
| 8 | TTS + Whisper | 火山/OpenAI | 5000 字 + 6 分钟 | — | $0.046 |
| | **总计** | | | | **$6.82** |

### 费用构成

```
Sonnet 文本生成:     $1.73  (25%)
NB2 Shot 生成:       $3.02  (44%) ← 最大项
NB2 参考图生成:      $1.88  (28%)
其他:                $0.17  (3%)
─────────────────────────────
总计:                $6.82
```

---

## 五、汇总对比

| 规格 | 总成本 | Sonnet | NB2 图像 | 其他 |
|------|:------:|:------:|:--------:|:----:|
| **短篇** (3 角色, 21 shots) | **$3.40** | $0.96 (28%) | $2.38 (70%) | $0.07 (2%) |
| **中长篇满配** (6 角色, 45 shots) | **$6.82** | $1.73 (25%) | $4.97 (73%) | $0.17 (3%) |

**最大成本项**: NB2 图像输出（$0.067/张 × 图片数），占总成本 70%+。

---

## 六、规模化估算

假设短篇:中长篇 = 7:3，加权平均 **$2.43/故事** (按短篇 $3.40×0.7 + 中长篇 $6.82×0.3)

**修正**: 实际加权 = $3.40×0.7 + $6.82×0.3 = $2.38 + $2.05 = **$4.43/故事**

| 规模 | 月费用 |
|------|-------:|
| 100 故事/月 | $443 |
| 500 故事/月 | $2,215 |
| 1,000 故事/月 | $4,430 |
| 5,000 故事/月 | $22,150 |
| 10,000 故事/月 | $44,300 |

---

## 七、实测验证

### Anthropic (2026-04-14)

| 指标 | Dashboard 数据 | 说明 |
|------|:------------:|------|
| Sonnet 4.6 tokens | 292,794 | 2 个故事（20+21 shots） |
| Haiku 4.5 tokens | 1,671 | 1 次调整画面（API key 失败） |
| 每故事 Sonnet tokens | ~146,000 | 含 Stage 1-4 全部 |

### Google Gemini (2026-04-14)

| 指标 | Dashboard 数据 | 说明 |
|------|:------------:|------|
| 总费用 | 2.82 AUD ($2.00 USD) | 包含盲测 + 上传分析 |
| 生成图片数 | 26 张 | 6 参考图 + 20 shot (A+B') |
| 图像 input 数 | ~63 张 | 20 shots × ~3 参考图/shot |
| 估算 vs 实测 | $1.80 vs $2.00 | 差 10%（可能分辨率>1K） |

---

## 八、成本优化杠杆

| 优化方向 | 潜在节省 | 可行性 |
|---------|:-------:|:-----:|
| NB2 降分辨率到 0.5K | -33%（$0.067→$0.045/张） | 需测试画质 |
| B' prompt 已启用 | 已节省 46% Gemini text input | ✅ 已实施 |
| Prompt caching (Sonnet) | 最高省 90% Sonnet input | 需要实施 |
| Batch API (Sonnet) | 省 50% | 需要非实时场景 |
| 减少参考图传入（如只传 1 张最相关的） | 减少 image input 次数 | 需测试一致性影响 |

---

## 九、历史版本记录

| 版本 | 日期 | 变更 | 短篇成本 |
|------|------|------|:--------:|
| V1 | 2026-02 | Pro 模型，60 shots 基准 | $9.35 |
| V2 | 2026-02 | NB2 替代 Pro | ~$7-8 |
| V3-V4 | 2026-04-14 | B' 格式 + 实测校准（错误：NB2 估 $0.02） | $1.19-$3.54（偏低） |
| **V5** | **2026-04-15** | **官方定价确认 + 双实测校准** | **$3.40** |
