# 关键经验与教训

> 从开发过程中积累的重要认知
> 避免重复踩坑

---

## 图像生成经验

### 角色一致性的关键

```
成功公式 (2026-04-15 更新):
1. 参考图串行生成 (肖像 → 全身)
2. Shot 生成默认用 NB2 (gemini-3.1-flash-image-preview)，角色一致性 ~95%
3. 角色描述完整复制，不能简化
4. 参考图必须传递到每个 Shot
```

### Prompt 工程要点

```
DO:
✅ 全英文 Prompt（B' 压缩标签格式为默认）
✅ 风格描述放在开头
✅ 角色描述详细完整（identity_line 不动）
✅ 场景描述清晰

DON'T:
❌ 使用中文（会泄露到图像，中文检测阈值 5%）
❌ 简化角色描述
❌ 跳过参考图
```

### 模型选择策略 (2026-04-15 更新)

```
NB2 (gemini-3.1-flash-image-preview，主力，~95%一致性):
- 参考图生成（portrait + fullbody）
- 场景参考图生成
- Shot 图像生成（默认）

Claude Sonnet 4.6 (文本生成):
- Stage 1-4（大纲/角色/剧本/分镜）

Gemini 3.1 Flash Lite (轻量):
- 上传图片分析（风格/角色/场景）
- Prompt 翻译安全网

Gemini 3 Pro Image (贵，~98%一致性):
- 未来 Premium 用户储备，当前不启用
```

---

## 音频处理经验

### TTS 选型

```
火山引擎豆包:
- 中文效果好
- 8种音色
- 支持语速、音量、音调调整
- 成本合理
```

### 时间戳对齐

```
Whisper 返回:
- Word 级别时间戳
- 繁体中文 (需转换)

对齐策略:
1. 精确匹配 (完全相同)
2. 前缀匹配 (开头相同)
3. 子序列匹配 (包含关系)
4. 自动调整误差 ≤80ms
```

### 繁简转换

```
问题: Whisper 返回繁体，TTS 用简体
解决: 统一转换为简体后再匹配
教训: 这个坑花了很长时间才发现
```

---

## 架构设计经验

### 五阶段流程

```
Stage 1: 故事大纲 (Story Outline)
Stage 2: 角色设计 (Character Design)
Stage 3: 剧本编写 (Screenplay)
Stage 4: 分镜脚本 (Storyboard)
Stage 5: 图像生成 (Image Generation)

关键: 必须按顺序，不能跳过
原因: 每个阶段依赖前一阶段的输出
```

### 数据流设计

```
用户输入 (一句话)
    ↓
故事大纲 (JSON)
    ↓
角色设计 (详细描述)
    ↓
剧本 (场景+对话)
    ↓
分镜 (Shot 列表)
    ↓
参考图 (每角色)
    ↓
Shot 图像 (每场景)
    ↓
音频 (TTS)
    ↓
时间轴 (对齐)
    ↓
视频 (合成)
```

---

## 测试经验

### 回归测试重要性

```
每次修改 Prompt 或图像生成逻辑后:
1. 必须运行回归测试
2. 重点检查角色一致性
3. 抽检多种故事类型

教训: 曾经一个小改动导致一致性从100%降到60%
```

### 测试场景覆盖

```
已验证的场景:
✅ 都市情感
✅ 武侠古装
✅ 多人场景 (3人、6人)
✅ 动物角色
✅ 多种视觉风格
```

---

## 成本优化经验

### 当前成本结构 (2026-04-15 更新)

```
NB2 + B' 方案 (官方定价校准):
- 短篇 (3角色, 21shots): ~$3.40/故事
- 中长篇 (6角色, 45shots): ~$6.82/故事
- 费用大头: NB2 图像输出 $0.067/张 (占 70%+)
- 详见 docs/API_COST_CALCULATION.md
```

### 优化方向

```
1. 减少 Shot 数量 (合并相似场景)
2. 优化 Prompt 长度 (精简但保持关键信息)
3. 缓存和复用 (参考图缓存)
4. Flash 精化研究 (特定场景可能可用)
```

---

## 协作经验

### 文档的重要性

```
好的文档 = 减少沟通成本

关键文档:
- claude.md: 核心约束，必读
- ARCHITECTURE.md: 架构设计
- KNOWN_ISSUES.md: 已知问题
- 各 Phase 完成文档
```

### 决策记录的价值

```
记录决策的原因:
1. 避免重复讨论
2. 新人快速了解背景
3. 回顾时知道为什么这样做
```

---

## 产品经验

### 用户视角

```
用户不关心:
- 用了什么模型
- Prompt 怎么写
- 技术实现细节

用户关心:
- 生成的视频好不好看
- 角色一致不一致
- 要等多久
- 要花多少钱
```

### MVP 思维

```
先做核心功能:
1. 能生成故事 ✅
2. 能生成图像 ✅
3. 能生成音频 ✅
4. 能合成视频 (进行中)
5. 有界面使用 (待做)

再迭代优化:
- 更多风格
- 更低成本
- 更快速度
- 更好体验
```

---

## 多 Agent 协作经验

### 自定义 subagent_type 启用 + frontmatter 默认值（2026-04-28 学会）

**之前误判**（2026-04-25 → 2026-04-28 修正）：以为 PM 主对话只能用内置 subagent_type（general-purpose / Explore / Plan / 等），所有 spawn 都得在 prompt 里 paste 角色身份。

**真根因**：CC 扫描自定义 subagent_type 依赖 cwd 下 `.claude/agents/` 可见。本项目 cwd 经常在项目根 `/AIFun/xuhuastory/`，但 agents 真目录在 `xuhua_story/.claude/agents/`，差一层导致扫描为空 → spawn 报 not found。

**修复**：建 symlink `/AIFun/xuhuastory/.claude/agents → xuhua_story/.claude/agents`。验证：spawn `subagent_type: "backend"` 返回 UI 绿色高亮 + 0 tool_uses + 2.8s 完成 + 回复读到 frontmatter color。

**Frontmatter 完整 schema**（官方 https://code.claude.com/docs/en/sub-agents.md L234-256）：
- `name` / `description` / `tools` / `model` / `color` — 已知字段
- `effort` — **5 档**：low / medium / high / xhigh / max（depends on model）
- 其他：`disallowedTools` / `permissionMode` / `mcpServers` / `hooks` / `maxTurns` / `skills` / `initialPrompt` / `memory` / `background` / `isolation`

**项目当前 frontmatter 默认**（DEC-023，2026-04-28 设定）：
- 深度推理类（ai-ml / pm / coordinator）→ `model: opus, effort: xhigh`
- 执行类（backend / devops / frontend / tester / resonance）→ `model: sonnet, effort: xhigh`
- spawn 时显式传 model/effort 可覆盖默认

**教训**：
1. 碰到"X 不工作"先确认环境（cwd / 路径 / 权限），不要凭"工具不工作"下"工具有限制"结论
2. 框架字段是否支持，先查官方文档不要猜（PM 之前用三种可能性猜 effort，官方第一行就写了支持）
3. xhigh 可能是 Opus 4.7 专属（slash command 提示"(Opus 4.7 only)"），Sonnet 写 xhigh 实际可能跑 high — 监控验证

**关联文档**：
- `~/.claude/projects/.../memory/feedback_use_custom_subagent_type.md` — 真根因 + 修复方案 + 验证证据
- `~/.claude/projects/.../memory/reference_subagent_symlink.md` — symlink 路径 + 重建命令
- `.team-brain/decisions/DECISIONS.md` DEC-023 — 8 agent frontmatter 升级决策
