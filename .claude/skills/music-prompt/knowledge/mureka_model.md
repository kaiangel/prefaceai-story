# Mureka 模型原理 + 参数敏感度

> 理解 Mureka 如何处理音乐 prompt，哪些参数影响最大，怎么写 prompt 才能最大化模型能力

---

## 一、Mureka 平台概览

**公司**: 全球领先的 AI 音乐生成产品，2024 年上线，近千万用户
**Base URL**: `https://api.mureka.cn`
**认证**: Bearer Token — `Authorization: Bearer $MUREKA_API_KEY`
**完整 API 文档**: `.team-brain/analysis/MUREKA_API_FULL_DOCS.md`

## 二、模型版本

| 模型 | 特点 | 适用场景 |
|------|------|---------|
| `mureka-8` | 最新常规模型，旋律和编曲质量高 | 主力模型 |
| `mureka-9` | 更新的常规模型 | 待测试 |
| `mureka-o2` | 算法择优（类 o1 思路），多语言，上下文 BGM | 需要更高质量时 |
| `mureka-7.6` | 稳定版，纯音乐支持好 | 纯音乐生成 |
| `auto` | 自动选择最新常规模型（非 o 系列） | **推荐默认选择** |

## 三、两种核心能力

### 纯音乐生成 POST /v1/instrumental/generate

**适合序话Story 的 BGM 场景。**

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | string (必填) | 模型版本，推荐 `"auto"` |
| `prompt` | string | 音乐描述，最大 1024 字符。**这是我们要精心设计的** |
| `instrumental_id` | string | 参考音乐 ID（上传获得），不能和 prompt 同时用 |
| `n` | int | 生成数量 1-3，默认 2，按数量计费 |
| `stream` | bool | 流式输出（边生边听） |

**注意**: `prompt` 和 `instrumental_id` **不能同时使用**。

### 歌曲生成 POST /v1/song/generate

**适合主题曲/片尾曲场景。**

| 参数 | 类型 | 说明 |
|------|------|------|
| `lyrics` | string (必填) | 歌词，最大 3000 字符，用 [Verse][Chorus] 等标签 |
| `model` | string (必填) | 模型版本 |
| `prompt` | string | 风格描述，最大 1024 字符 |
| `reference_id` | string | 参考曲 ID |
| `vocal_id` | string | 音色 ID（克隆的声音） |
| `melody_id` | string | 旋律 ID（哼唱/MIDI） |
| `n` | int | 生成数量 1-3 |

**组合规则**:
- `prompt` 可单独 或 `prompt + vocal_id`
- `reference_id` 可单独 或 `reference_id + vocal_id`
- `melody_id` 只能单独使用

## 四、参数敏感度排序

从最影响结果到最不影响的：

```
1. Genre/Style 描述 (影响 80%+)
   → 决定整首曲子的基调和编曲方向
   → 例: "lo-fi hip-hop" vs "cinematic orchestral" = 完全不同的世界

2. Instruments 乐器 (影响 60%)
   → 决定音色和质感
   → 例: "solo piano" vs "full orchestra" = 极大差异

3. Mood/Emotion 情绪 (影响 40%)
   → 影响和声选择和动态
   → 例: "melancholic" → 小调，"joyful" → 大调

4. Tempo/BPM 速度 (影响 30%)
   → 影响节奏感和能量
   → 例: "60 BPM" → 缓慢沉思，"140 BPM" → 紧张兴奋

5. Texture/Effect 质感 (影响 20%)
   → 微调音色特征
   → 例: "reverb-heavy" "dry and intimate" "vinyl crackle"

6. Narrative Imagery 画面 (影响 15%)
   → 引导模型理解情境
   → 例: "rain on empty street" → 模型会选择合适的氛围元素
```

**关键发现**: Genre 和 Instruments 是最敏感的参数——改了它们，整首曲子彻底改变。Mood 和 Tempo 是中等敏感。Texture 和 Imagery 是微调。

## 五、中文 vs 英文

| 维度 | 英文 | 中文 |
|------|------|------|
| 流派 | ✅ 精确（全球通用术语） | 🟡 可以但不如英文 |
| 乐器 | ✅ 精确（"Rhodes piano" "cello pizzicato"） | 🟡 "罗兹电钢琴"含义等价但模型可能不敏感 |
| 情绪 | 🟡 "bittersweet" "nostalgic" | ✅ "欲说还休" "苦中带甜" 更细腻 |
| 画面 | 🟡 | ✅ Mureka 是中国公司，中文理解优化过 |

**最佳策略**: **英文为主体**（音乐技术术语），**中文情绪意象点缀**。

示例:
```
Cinematic solo piano, 65 BPM rubato. Soft felt piano with gentle reverb.
Bittersweet and intimate, 像写一封永远不会寄出的信.
Late autumn, first frost on window glass, warm desk lamp in empty room.
```

## 六、Prompt 不该做的事

| 不要做 | 为什么 | 替代 |
|--------|--------|------|
| "请生成一首悲伤的钢琴曲" | 命令式，不是描述式 | 直接描述音乐本身 |
| "sad slow piano" | 信息密度太低 | "felt piano, heartbeat rubato, rain-streaked window" |
| 同时写太多矛盾的描述 | 模型混乱 | 保持内在一致 |
| 超过 500 词 | prompt 上限 1024 字符 | 压缩到 50-100 词精华 |
| 只写 mood 标签 | 同质化 | 加入故事专属的画面意象 |

## 七、异步任务流程

```
POST /v1/instrumental/generate → 返回 {id, status: "preparing"}
    ↓ 轮询
GET /v1/instrumental/query/{task_id} → status: "running" / "streaming" / "succeeded"
    ↓ succeeded
response.choices[0].url → mp3 下载链接（5 分钟有效）
response.choices[0].wav_url → wav 下载链接（如有）
response.choices[0].duration → 时长（秒）
```

**注意**: URL 有效期短（5 分钟），拿到后立即下载保存。

## 八、计费

- 按次计费，n=2 算 2 次
- 余额 12 个月有效，新充值延长所有余额
- 生成内容完全归用户所有，可商用
- 生成的音频末尾有 5 秒水印（合规要求）

## 九、支持的语言（歌曲）

中文、英文、日文、韩文、葡萄牙语、西班牙语、德语、法语、意大利语、俄语

## 十、时长控制

Mureka 纯音乐 API **没有 duration 参数**，模型自己决定时长（通常 2-3 分钟）。

**⚠️ Prompt 暗示时长无效（2026-04-16 实测验证）**：

测试 `"short 60-second piece"` 暗示词，结果生成 3:07（187 秒），模型完全无视。

**结论**：无法通过 prompt 控制时长。需要短时长 BGM 时，只能**后处理裁剪**（ffmpeg 截取 + 淡出）。

---

## 十一、集成原则：n=1，不多生成

调 Mureka API 时 `n` 必须设为 **1**（只生成 1 首）。

**原因**：n=2 或 n=3 会按数量计费，浪费成本。用户不满意可以点"重新生成"再调一次（和 StageD 重新生成 shot 同理）。不要替用户预生成多个备选。

**2026-04-16 教训**：测试"最后一投"时 @backend 用了 n=2，生成了两首 BGM，多花了一倍费用。

---

## 十一、已知坑：curl 传中文 JSON 报错

**EP-015**：用 curl 的 `-d` 传含中文字符的 JSON body 给 Mureka API 会报 `Invalid JSON`。

**正确做法**：用 Python HTTP client（`urllib.request` 或 `httpx`），`json.dumps(data, ensure_ascii=False).encode('utf-8')`。

**后续集成 Pipeline 时必须用 Python HTTP 调用，不用 curl。**

---

## 十一、强制词 vs 描述式——音乐 prompt 的未验证假设

**图像 prompt 的经验**：序话Story 的 A vs B' 盲测证明，去掉 `MANDATORY`/`DO NOT IGNORE` 等强制词和 `═══` 装饰框线后，图像质量不降反微升。说明图像模型对"命令语气"不敏感，对"信息位置"（开头注意力最高）更敏感。

**音乐 prompt 的假设**：Mureka 音乐模型是否对强制词敏感**尚未验证**。建议：
- 先用**描述式（场域式）prompt** 测试——用画面意象唤起情绪，不用 MUST/DO NOT
- 如果效果不理想，再尝试加入强制词对比
- 这是一个需要通过 A/B 测试验证的开放问题
