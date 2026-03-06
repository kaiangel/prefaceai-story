# PM 深度分析 — TASK-BUBBLE-SIMPLIFY 全维度解剖

> **日期**: 2026-03-05
> **分析者**: PM Agent
> **触发**: Founder 要求深挖 TASK-BUBBLE-SIMPLIFY 3 组测试结果
> **状态**: ✅ 分析完成 → Founder 提供新证据推翻 PM 初始结论 → 方向已确定 → TASK-PROMPT-BUBBLE 已派发

---

## 背景

Bug #6 暴露了 `near {中文名}` 对话气泡定位对 NB2 不可靠。Founder 提出简化方案：移除 `TEXT OVERLAY REQUIREMENT` 指令块，把对话直接嵌入 image_prompt，让 NB2 自行理解并渲染气泡。

Backend 执行 3 组对比测试：
- 组 A: `char_001's dialogue: '台词'`
- 组 B: `Lin Chenyu shouts: '台词'`
- 组 C: `The young man in light grey shirt shouts: '台词'`

**结果: 3 组均未渲染对话气泡。**

测试产物: `test_output/manualtest/bubble_simplify/`（3 张图 + 3 个 prompt txt）

---

## 一、根因解剖：为什么 3 组全部「零气泡」？

3 组用了不同的说话者标识方式，结果完全一致 —— **失败原因与说话者标识方式无关**。根因在更深层。

### 根因 #1：语义层级错位

NB2 是图像生成模型，理解的是**视觉描述语言**。Prompt 的 ~70 行内容中：
- 前 69 行全是精确的视觉指令（风格、角色外观、镜头、光线、构图）
- 最后 3 行突然切换成**叙事标注**：`X shouts: '中文台词'`

NB2 将这 3 行解读为**情节上下文补充**（类似导演手记），而非**视觉渲染指令**。这就像给画师一份详细的分镜稿，最后附了句「顺便说一下，这场戏的台词是这些」—— 画师会用台词理解情绪，但不会在画面上写字。

### 根因 #2：质量标签夹层抑制

测试代码的 prompt 拼接逻辑（`test_bubble_simplify.py:218-219`）：

```python
full_prompt = base_prompt + "\n\n" + dialogue_block
full_prompt += "\n\nartstation trending, professional illustration, high detail"
```

而 `base_prompt` 本身已经以 `artstation trending, professional illustration, high detail` 结尾（`StyleEnforcer.enforce_prompt` 的输出）。最终 prompt 结构：

```
... [场景描述]
artstation trending, professional illustration, high detail    ← 第一道质量标签
char_001's dialogue: '你们有没有问过我...'                      ← 对话被夹在中间
artstation trending, professional illustration, high detail    ← 第二道质量标签
```

对话行被两道质量标签「三明治」式夹住。图像模型在注意力分配上，末尾质量标签的权重高于中间的叙事文本。对话行在注意力竞争中被进一步边缘化。

### 根因 #3：缺少视觉渲染指令

对比原始 `build_native_text_prompt()` 输出和测试 prompt 的关键差异：

| 维度 | 原始 TEXT OVERLAY REQUIREMENT | 简化嵌入 |
|------|-------------------------------|----------|
| 视觉元素描述 | "A white rounded rectangular speech bubble" | 无 |
| 颜色/样式 | "clean white fill, thin black outline, rounded corners" | 无 |
| 字体指令 | "display Chinese text '...' in black font, centered" | 无 |
| 定位指令 | "positioned near ..." | 无 |
| 气泡尾巴 | "triangular tail pointing toward ..." | 无 |

简化方案完全没有告诉 NB2「画一个什么形状的东西」。NB2 不会从 `X shouts: '...'` 自动推断出需要画气泡 —— 这不是语义推理问题，是**没有给出视觉指令**。

---

## 二、正面发现：对话嵌入的真正价值

虽然 3 组都没有气泡，但所有 3 张图的**情绪表达质量非常高**：

| 图片 | 角色情绪还原 | 肢体语言 | 场景张力 |
|------|-------------|----------|----------|
| Group A (char_ID) | 三人愤怒表情精准，林德福举手指向 | 林建国握拳、林晨宇仰头叛逆 | 打碎碗碟、倒洒酱汁 |
| Group B (英文名) | 几乎同等质量，嘴部张开程度更大 | 椅子位置更自然 | 春联/灯笼氛围完整 |
| Group C (描述) | 稍弱但仍可接受 | 构图更简洁 | 灯光更集中 |

如果完全去掉对话行，NB2 仅从 `face twisted in mid-shout` 等 image_prompt 描述生成的表情会更泛化。对话嵌入让 NB2 **理解了每个角色在争吵什么**，从而生成更具体的情绪表达。

**结论：对话嵌入对情绪理解有价值，但价值在于「导演指导」而非「文字渲染」。**

**额外发现：对话嵌入不触发 NB2 渲染气泡** —— 这消除了后续与 TextOverlay 后处理「重复渲染」的风险。

---

## 三、第一性原理：NB2 文字渲染的能力边界

回到原始 shot_10（带 TEXT OVERLAY REQUIREMENT 的版本）—— 唯一成功渲染了气泡的版本：

**成功点**：
- 4 个气泡确实被渲染出来
- 中文字体可读
- 气泡样式（白底黑字、圆角矩形）基本正确

**失败点**：
- 林建国台词「你懂什么叫想要！你懂什么叫代价！」出现了**两次**（左上角 + 左下角重复）
- 林德福台词「都给我住口——！」定位在**右下角**（靠近林晨宇），而非画面远端的林德福
- 即林晨宇附近有两个气泡（自己的 + 错误定位的林德福的）

这揭示了 NB2 文字渲染的**系统性局限**：

| 能力维度 | 单文本元素（思想/旁白） | 多文本元素（对话气泡） |
|----------|----------------------|---------------------|
| 渲染成功率 | 高（5/5 历史测试） | 中（有气泡但有错误） |
| 定位准确性 | 高（固定位置：顶/底） | 低（`near X` 不可靠） |
| 重复风险 | 低 | 高（多气泡互相干扰） |
| 中文准确性 | 尚可 | 下降（注意力分散） |

**底层原因**：思想/旁白是全幅半透明条，位置固定（top/bottom），NB2 只需处理一个矩形 + 一段文字。对话气泡需要同时处理 N 个独立视觉元素，每个要精确定位到特定角色附近 —— 这超出了当前图像生成模型的可靠控制能力。

---

## 四、历史数据证据链

| 测试 | 方案 | 结果 | 关键发现 |
|------|------|------|----------|
| TASK-NB2-TEXT-TEST (2/27) | NB2 native 全类型 | 5/5 成功 | 测试样本未严格验证多人对话气泡定位准确性 |
| TextOverlay V5 验收 | TextOverlayV2 全类型 | 42/42, 4.9/5 | 100% 定位准确，包括多人对话 |
| Founder 选择 NB2 native (2/28) | Plan B: NB2 native | 批准 | 决策基于 style-aware 优势 |
| Bug #6 发现 (3/4) | NB2 native 对话 | 定位错误 | `near {中文名}` 跨语言断裂 |
| TASK-BUBBLE-SIMPLIFY (3/5) | 简化嵌入 | 3/3 零气泡 | 无视觉指令 = 无渲染 |

**关键缺失**：2/27 NB2-TEXT-TEST 的 dialogue（shot_09）是双人对话，「成功」定义是「生成了气泡」，并未严格验证每个气泡是否靠近正确说话者。Bug #6 在后续全 10-shot 回归测试中才暴露 —— 样本量和场景复杂度增加后，定位问题浮现。

---

## 五、架构级分析：四条可能的路径

### 路径 A：改进 TEXT OVERLAY REQUIREMENT 的定位指令

修改 `build_native_text_prompt()` 中对话定位逻辑，用英文物理描述替代 `near {中文名}`：

```python
# 当前（Bug #6）
pos_desc = f"near {speaker}"  # speaker = "林德福"

# 改进方案
pos_desc = f"near the {character_description}"  # "near the elderly man in dark navy Mao-jacket"
```

**优势**: 最小改动，保持 NB2 native 路线

**风险**:
- 仍依赖 NB2 理解空间定位 —— 3 人同桌时模型可能仍混淆「谁在哪」
- 重复渲染问题未解决（模型注意力问题，非定位问题）
- 中文渲染质量不可控

**判断: 治标不治本。定位准确性可能从 ~40% 提升到 ~60%，无法达到产品级 95%+。**

### 路径 B：对话嵌入（情绪）+ TextOverlayV2（仅对话气泡）+ NB2 native（思想/旁白）

混合方案：NB2 渲染思想/旁白条（已验证可靠），TextOverlay 渲染对话气泡（100% 可靠），对话嵌入用于情绪增强。

**优势**:
- 各取所长：NB2 做擅长的（固定位置单元素），TextOverlay 做可靠的（动态多元素）
- 保留了思想/旁白的风格融合感

**风险**:
- **两条代码路径 = 两倍维护成本和失败面**
- NB2 native 思想/旁白仅在 illustration + slam_dunk 风格验证过 5/5，其他 14+ 风格未知
- 每次 NB2 模型更新，native 文字渲染行为可能改变
- 同一图中 NB2 native 条 + TextOverlay 气泡可能有视觉不一致

### 路径 C：统一 TextOverlayV2 + 对话嵌入（推荐）

所有文字类型（对话、思想、旁白、复合类型）全部由 TextOverlayV2 后处理，`use_native_text=False`。对话嵌入保留在 prompt 中用于情绪增强。

**优势**:
- **一条代码路径** —— 一种验证标准，可预测的质量输出
- 100% 定位可靠，100% 中文准确（已验证 42/42, 4.9/5）
- **风格无关、模型无关** —— 16 预设 + 自定义风格全部天然覆盖
- Stage D 全类型可编辑（<1s，零 API 成本）
- 模型升级不影响文字渲染
- 对话嵌入不触发 NB2 渲染（已验证），与 TextOverlay 无冲突

**劣势**:
- 思想/旁白的半透明条失去 NB2 style-aware 的视觉融合感（但见下方通用性分析）

### 路径 D：对话嵌入 + 强化 TEXT OVERLAY REQUIREMENT（仅对话）

在 `build_native_text_prompt()` 中对 dialogue 类型使用更强的渲染指令。

**优势**: 保持 NB2 native 路线 + 情绪上下文

**风险**: 仍无法解决空间定位的根本问题，增加 prompt 长度但不增加可靠性

**判断: 更多指令词 ≠ 更可靠执行。NB2 空间定位是模型层面的能力边界，不是 prompt 工程能解决的。**

---

## 六、通用性维度压力测试（Founder 追问触发）

> **Founder**: "时刻牢记：我们是要做一个通用的 AI 短视频生成工具，而不是为了完善单一的故事生成"

上述路径 B（混合方案）在通用场景下的脆弱性：

### 6.1 覆盖矩阵

| 维度 | 当前测试覆盖 | 产品实际需要 |
|------|-------------|-------------|
| 风格 | illustration + slam_dunk (2 种) | **16 预设 + 自定义风格** |
| 文字类型 | 5 种 | 5 种 × 各种组合 |
| 角色数 | 1-3 人 | 1-6+ 人 |
| 故事类型 | 都市情感 + 运动 | **任意题材** |
| 语种 | 中文 | 未来可能多语言 |

NB2 native 思想/旁白条仅在 2 个风格上验证过 —— 在水彩、像素、水墨、儿童绘本、赛博朋克等风格下表现未知。而 TextOverlay 天然风格无关。

### 6.2 模型升级风险

NB2 是 `gemini-3.1-flash-image-preview` —— `preview` 后缀意味着它会迭代。每次模型更新，NB2 native 的文字渲染行为可能改变。混合方案对模型变化是脆弱的。TextOverlay 完全不受模型更新影响。

### 6.3 「风格融合感」实际价值被高估

路径 B 的核心辩护理由是「思想/旁白半透明条与画面风格融合更好」。冷静审视 —— 半透明黑底白字条本质上是 **UI 元素**，不是艺术元素。无论故事是水墨风还是赛博朋克风，旁白条的形态都是标准化的。它的「风格融合」收益远小于「一条代码路径」的维护性收益。

### 6.4 通用性结论

**路径 C（统一 TextOverlay + 对话嵌入）是通用工具最优解**：
- 一条代码路径，一种验证标准
- 风格无关、模型无关、语种无关
- 可预测的质量输出
- Stage D 全类型可编辑

---

## 七、最终推荐

### 推荐路径 C：统一 TextOverlay + 对话嵌入

```
┌──────────────────────────────────────────────────┐
│              NB2 图像生成 Prompt                    │
│                                                    │
│  [风格/角色/场景/镜头 — 现有结构不变]                  │
│                                                    │
│  [对话嵌入 — 仅用于情绪理解]                          │
│  Lin Chenyu shouts: '你们有没有问过我...'            │
│  (NB2 用此理解情绪，不渲染气泡 — 已验证)               │
│                                                    │
│  use_native_text=False                              │
│  (不附加任何 TEXT OVERLAY REQUIREMENT)               │
└──────────────────────────────────────────────────┘
                    ↓
              NB2 生成干净图像
         (含情绪表达，不含任何文字渲染)
                    ↓
┌──────────────────────────────────────────────────┐
│        TextOverlayV2 后处理（全部文字类型）           │
│                                                    │
│  对话气泡 → 程序化定位 + 中文渲染                      │
│  思想旁白 → 半透明条 + 白字渲染                        │
│  叙事旁白 → 条状框 + 文字渲染                          │
│  复合类型 → 按子类型组合渲染                            │
│                                                    │
│  Stage D: 全类型可单独重新渲染（<1s，零 API 成本）      │
└──────────────────────────────────────────────────┘
```

### 代码改动要点

1. `image_generator.py` — `use_native_text` 默认改为 `False`（或移除该参数，统一走 TextOverlay）
2. 新增：对话嵌入逻辑 — 从 `text_overlay.chinese_text` 提取对话行，以叙事描述形式追加到 prompt 末尾（用于情绪增强）
3. Pipeline 中确保所有 text_type 都走 TextOverlayV2 后处理
4. `build_native_text_prompt()` 代码保留但不再被调用（作为历史参考/未来备用）

### 关键前提确认

- 对话嵌入不触发 NB2 自行渲染气泡 → **已由 TASK-BUBBLE-SIMPLIFY 3 组测试验证** ✅
- TextOverlayV2 覆盖全部 5 种 text_type → **已由 V5 验收 42/42, 4.9/5 验证** ✅
- TextOverlayV2 跨风格通用 → **已由交叉验证（都市+韩漫 / 古风+水墨）确认** ✅

---

## 八、Founder 新证据：NB2 完全具备对话气泡能力（PM 初始结论被推翻）

> **时间**: 2026-03-05 ~17:30
> **来源**: Founder 在 Gemini 网页版用 NB2 实测

### 8.1 Founder 测试 #1 — 漫画风格（NB2 自由创作）

**Prompt**: "漫画形式，三个人吵架，需要生成对话泡泡，用中文表示吵架对话的具体内容"（~30 字）

**结果**:
- 黑白漫画风格，3 人争吵场景
- 3 个对话气泡各自靠近正确角色，定位准确
- 中文文字清晰可读，长句多行无乱码
- 气泡样式标准（白底黑字 + 尾巴指向说话者）
- NB2 自行生成了角色名字标签 + 详细对话内容

**迭代测试**: Founder 追问 "对话泡泡里不需要角色名字（比如李伟）的出现"，NB2 准确执行 — 移除气泡内名字前缀，保留对话内容。

### 8.2 Founder 测试 #2 — 写实风格 + 指定中文文本（方向 2 验证）

**Prompt**: "3 characters in a scene... a young man in grey shirt has a speech bubble saying '你们有没有问过我，我想要什么？！'. a man in burgundy tunic has a speech bubble saying '你懂什么叫想要！...'. a elderly man has a speech bubble saying '都给我住口——！'."

**结果**:
- **写实风格**（非漫画）— 证明跨风格可行
- 3 个气泡各自靠近正确角色
- **指定中文文字准确渲染** — 证明不仅是自由创作，指定文本也可行
- 气泡样式自然融入画面

### 8.3 PM 初始结论被推翻

| PM 初始判断 | Founder 证据 | 修正 |
|-------------|-------------|------|
| NB2 无法可靠渲染多人对话气泡 | 漫画 + 写实两个风格均成功 | **NB2 完全具备能力** |
| 问题是模型能力边界 | 简单 prompt 成功 vs 复杂 prompt 失败 | **问题是 prompt 架构** |
| 指定文本准确性存疑 | 测试 #2 准确渲染了指定中文 | **指定文本可行** |
| 推荐 TextOverlay 全部接管 | NB2 native 才是正确方向 | **应修复 prompt 架构** |

### 8.4 根因重定位

**不是模型能力问题，是 prompt 注意力分配问题。**

Founder 的 ~30 字 prompt 中，「对话泡泡」占意图权重 ~40%。
我们的 ~9000 字 prompt 中，对话占权重 < 1%，被 70 行风格/角色/场景约束淹没。

### 8.5 Founder 确定方向

**方向 2+3 融合**:
1. **方向 2**: 对话气泡融入场景描述（"character has a speech bubble saying '...'")
2. **方向 3**: 精简 prompt 冗余（保留必要核心，去掉多余重复）
3. **Stage D**: Founder 倾向 NB2 native，接受改一个字重新生成整张图
4. **验证**: 2 个 10-shot 完整故事（不同内容 + 不同风格），在实际 prompt 复杂度下测试

**执行**: @AI-ML — TASK-PROMPT-BUBBLE

---

## 九、PM Prompt 架构冗余分析（为 AI-ML 执行提供参考）

### 当前 prompt 组装顺序与字符量

| 顺序 | 模块 | 来源 | ~字符数 | 必要性 |
|------|------|------|---------|--------|
| 1 | StyleEnforcer 风格前缀 | `style_enforcer.py` | 1,200-1,500 | 关键 — 不可删 |
| 2 | Critical Header（角色一致性指令） | `storyboard_prompts.py` | ~300 | 关键 — 不可删 |
| 3 | Character Mapping（角色身份描述） | `storyboard_prompts.py` | 400-800 | 关键 — 不可删 |
| 4 | Narrative Context（叙事上下文） | `storyboard_prompts.py` | 400-800 | 高 — 保留 |
| 5 | System Instruction（全局风格指令） | `storyboard_prompts.py` | ~400 | 中 — 可精简 |
| 6 | Continuity Context（连续性） | `storyboard_prompts.py` | 200-400 | 中 — 可选 |
| 7 | Scene Description（场景描述） | shot.image_prompt | 500-1,500 | 关键 — 不可删 |
| 8 | Quality Suffix | `style_enforcer.py` | 100-200 | 低 — 可合并 |
| 9 | TEXT OVERLAY REQUIREMENT | `image_generator.py` | 300-600 | 将被方向 2 替代 |

**总计**: ~4,000-7,000 字符

### 已识别的冗余

1. **风格信息三重叠**: System Instruction 提到 "Style Enforcement: [style]" + StyleEnforcer 前缀 1,200+ 字 + image_prompt 末尾 "Art style: [style]" → **~1,500 字重复**
2. **Quality Suffix 与 StyleEnforcer mandatory 重复**: StyleEnforcer 的 mandatory_keywords 已含质量词，Quality Suffix 再加一遍 → **~150 字可合并**
3. **System Instruction 可精简**: 去掉与 StyleEnforcer 重叠的风格行，保留 Aspect Ratio / Color Grade / Lighting / Lens → **~200 字可省**

**预计可精简**: ~500-800 字符（10-15%），同时为对话气泡指令腾出注意力空间。

---

## 附录：测试产物索引

| 文件 | 说明 |
|------|------|
| `test_output/manualtest/bubble_simplify/group_A.png` | 组 A 生成图（char_ID 标识，无气泡） |
| `test_output/manualtest/bubble_simplify/group_B.png` | 组 B 生成图（英文名标识，无气泡） |
| `test_output/manualtest/bubble_simplify/group_C.png` | 组 C 生成图（角色描述标识，无气泡） |
| `test_output/manualtest/bubble_simplify/group_A_prompt.txt` | 组 A 完整 prompt（~9231 chars） |
| `test_output/manualtest/bubble_simplify/group_B_prompt.txt` | 组 B 完整 prompt |
| `test_output/manualtest/bubble_simplify/group_C_prompt.txt` | 组 C 完整 prompt |
| `tests/test_bubble_simplify.py` | 测试脚本（287 行） |
| `test_output/manualtest/bugfix_regression/20260304_162910/shots/shot_10.png` | 原始 shot_10（带 TEXT OVERLAY，有气泡但定位错误+重复） |

---

## 附录：相关决策和文档

| 文档 | 关联 |
|------|------|
| `.team-brain/decisions/DECISIONS.md` — Bug #6 | 对话气泡定位问题首次记录 |
| `docs/COMIC_TEXT_OVERLAY_V2_DECISION.md` | TextOverlayV2 原始决策 |
| `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW.md` | TextOverlay 质量评估 |
| `.team-brain/analysis/V3_PM_INDEPENDENT_REVIEW_GENERALITY.md` | TextOverlay 14 维度通用性分析 |
| `app/services/image_generator.py:43-153` | `build_native_text_prompt()` 实现 |
| `app/services/text_overlay_service.py` | TextOverlayServiceV2 实现 |
