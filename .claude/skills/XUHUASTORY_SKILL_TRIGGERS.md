# xuhuastory 专属 Skills 中英文触发词映射

> 本文档定义 xuhuastory 项目4个专属 Skill 的中英文触发词，包括专业术语和大白话表达。

---

## 快速查找表

| Skill | 专业中文 | 大白话中文 | English |
|-------|---------|-----------|---------|
| character-consistency | 角色一致性、参考图、Pro模型 | 人物变脸、角色长得不一样、同一个人 | character, consistency, reference image |
| prompt-engineering | 图像Prompt、风格强制、英文描述 | 中文泄露、乱码、风格跑偏 | image prompt, style, English only |
| audio-alignment | 音画对齐、时间戳、繁简转换 | 声音和画面对不上、字幕时间不对 | alignment, timestamp, audio sync |
| context-management | 上下文管理、渐进式披露、记忆层级 | Claude忘了、对话太长、信息混乱 | context, progressive disclosure, memory |

---

## 1. character-consistency.md

### 角色一致性 Skill

**核心职责**: 确保同一角色在所有场景图中保持一致外观

### 触发词

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 角色一致性、参考图、Pro模型、use_pro_model、fullbody、portrait、角色描述、physical字段、clothing字段 |
| **大白话中文** | 人物变脸了、角色长得不一样、同一个人怎么不一样、前后对不上、角色串了、人物混淆、外观不统一 |
| **English** | character consistency, reference image, pro model, character description, physical, clothing, same character, face change |

### 文件触发

修改以下文件时**必须**加载此 Skill：
- `image_generator.py`
- `storyboard_prompts.py`
- `storyboard_service.py`
- `reference_image_manager.py`

### 核心约束速记

```
Shot生成 → use_pro_model=True
参考图 → fullbody + scene_refs 必须传
角色描述 → physical + clothing 完整
```

---

## 2. prompt-engineering.md

### Prompt工程 Skill

**核心职责**: 确保图像生成 Prompt 规范，防止中文泄露和风格漂移

### 触发词

| 类型 | 触发词 |
|------|--------|
| **专业中文** | image_prompt、图像Prompt、风格强制、StyleEnforcer、英文描述、中文例外、shot_type翻译、camera_angle |
| **大白话中文** | 中文泄露到图里了、图片上有乱码、风格跑偏了、画风不统一、怎么变卡通了、写实变动画 |
| **English** | image prompt, style enforcement, English only, Chinese leak, style drift, mandatory style, forbidden keywords |

### 文件触发

修改以下文件时**必须**加载此 Skill：
- `storyboard_prompts.py`
- `storyboard_director.py`
- `style_enforcer.py`

### 核心约束速记

```
图像Prompt → 全英文
风格 → StyleEnforcer开头注入
例外 → 中国地名/服饰/建筑可保留中文
narration → 保留中文（用于TTS）
```

---

## 3. audio-alignment.md

### 音画对齐 Skill

**核心职责**: 确保旁白时间轴与图像停留时长精确匹配（≤80ms误差）

### 触发词

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 音画对齐、时间戳、Whisper、TTS、繁简转换、timeline、word-level、多策略匹配 |
| **大白话中文** | 声音和画面对不上、字幕时间不对、说话和图片不同步、旁白太快/太慢、时间轴错了 |
| **English** | audio alignment, timestamp, whisper, TTS, timeline, sync, audio video sync, duration |

### 文件触发

修改以下文件时**必须**加载此 Skill：
- `alignment_service.py`
- `whisper_service.py`
- `tts_service.py`

### 核心约束速记

```
Whisper输出 → 可能是繁体，需转简体
匹配策略 → 精确→去标点→前缀→子序列
误差目标 → ≤80ms
```

---

## 4. context-management.md

### 上下文管理 Skill

**核心职责**: 管理 Claude 的注意力预算，防止上下文退化

### 触发词

| 类型 | 触发词 |
|------|--------|
| **专业中文** | 上下文管理、渐进式披露、注意力预算、记忆层级、上下文退化、progressive disclosure |
| **大白话中文** | Claude忘了之前说的、对话太长了、信息混乱了、开始重复了、之前的约束不记得了 |
| **English** | context management, progressive disclosure, attention budget, memory, context degradation |

### 场景触发

以下场景时**建议**加载此 Skill：
- 开始新的工作会话
- 感觉上下文变得混乱
- 任务复杂度增加
- 需要多个 agent 协作

### 核心约束速记

```
加载策略 → 按需加载，不要一次全部加载
关键信息 → 放开头或结尾（避免 Lost in the Middle）
退化信号 → 开始重复、忘记决策、混淆内容
```

---

## 组合触发场景

### 场景1: 修改图像生成代码

**触发词**: 图像生成、shot图片、角色变脸

**需要加载**:
1. `character-consistency.md` - 确保一致性约束
2. `prompt-engineering.md` - 确保 Prompt 规范

### 场景2: 修改音视频流程

**触发词**: 时间轴、旁白、视频合成

**需要加载**:
1. `audio-alignment.md` - 确保对齐精度

### 场景3: 复杂多文件修改

**触发词**: 重构、架构调整、多agent协作

**需要加载**:
1. `context-management.md` - 管理上下文
2. 相关业务 Skill

---

## 与 Context Engineering Skills 的关系

| 类型 | 来源 | 范围 | 加载方式 |
|------|------|------|---------|
| **xuhuastory Skills** | 本地 `/.claude/skills/` | 项目专属 | 手动读取文件 |
| **Context Engineering Skills** | 全局 Marketplace Plugin | 所有项目通用 | 触发词自动激活 |

**配合使用示例**:
- 角色一致性问题 → `character-consistency.md` (专属) + `context-degradation` (全局)
- 长对话质量下降 → `context-management.md` (专属) + `context-compression` (全局)

---

## 文件路径快速参考

```
/.claude/skills/
├── character-consistency.md     # 角色一致性
├── prompt-engineering.md        # Prompt工程
├── audio-alignment.md           # 音画对齐
├── context-management.md        # 上下文管理
├── XUHUASTORY_SKILL_TRIGGERS.md # 本文件
├── CONTEXT_ENGINEERING_TRIGGERS.md # Context Engineering触发词
└── SKILL_INDEX.md               # Skills索引
```
