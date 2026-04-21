# AI-ML Agent - 当前任务

> **最后更新**: 2026-04-21（PM 代更新）
> **状态**: ✅ Wave 1 Step B 完成 — 95 风格 music_hint 字段全覆盖

---

## 刚完成

### ✅ Wave 1 Step B — 95 风格 music_hint 字段 (2026-04-21)

**改动**:
- `app/services/style_enforcer.py`: `StyleEnforcement` dataclass 加 `music_hint` 字段，28 个 STYLE_ENFORCEMENTS 全加
- `app/models/style_config.py`: 新增 `MUSIC_HINTS` dict + `get_music_hint(style_name)` 模块级函数；覆盖 95+1 风格

**覆盖**: 28 StyleEnforcer + 67 style_config 独有 = **95 个用户可选风格 100% 覆盖** + 1 custom fallback

**V4 哲学遵守**: 全英文，身体感觉/空间氛围描述（"rain-soaked and machine-breathing"），不列乐器清单。中乐用 guqin/dizi/xiao/erhu/pipa/zheng/gayageum 色彩，西方/电子/未来分别有对应色彩

**Backend 消费**: `from app.models.style_config import get_music_hint; hint = get_music_hint(style_preset)`

---

### ✅ v3.2 精修 (2026-04-21)

**背景**: v3.1 加的大块约束（ASCII 分层图 + 输出纯净规则）导致 Haiku 挑金句质量退步（8.4→6.7）。方案 B 回退，配合 Backend 代码层清污。

**改动** `meta_mixed_v3_quote_picking.md`:
- 🗑️ 删除 ASCII 分层示意图（~37 行）
- 🗑️ 删除"输出纯净规则"大段
- ✅ 保留 few-shot 示例无 ``` 围栏（根因消除）
- ✅ 新加 2 行轻量长度建议："BGM prompt ≤400 字符建议；质量优先于长度；金句原文保留"
- 措辞"建议"而非"必须"，降低 Haiku 合规焦虑

**文件大小**: 15,195 bytes（基本等同 v3 原始）

**预估**: 金句质量回到 v3 水平（≥8/10）可信度 ~85%。唯一不确定性：2 行轻量建议是否仍略微分心。

---

### ✅ v3.1 mixed 微调 (已被 v3.2 替代)

---

### ✅ TASK-HAIKU-QUOTE-EXTRACTION Step 1 — v3 quote picking (2026-04-21)

**背景**: Pipeline 集成前置测试，验证 Haiku 4.5 能否自主挑金句，避免硬编码

**产出**:
- `meta_prompts/meta_en_v3_quote_picking.md` (~15.8KB)
- `meta_prompts/meta_mixed_v3_quote_picking.md` (~15.1KB)

**Quote Selection Protocol 核心标准**:
- 正向 5 条: 画面感>情节 / 隐喻通感>直白 / 独立成句 / 代表主基调 / 张力压进一词一动作
- 反向 5 条: 情节总结 / 抽象情绪独白 / 对白 / 姓名密集 / 动作序列中间句
- 位置倾向: 段末>独立画面句>段中；数量: 1-2 句（硬约束）
- 忠实规则: 原文照搬不改标点
- 输出: `<quotes>...</quotes>` 标记 + BGM prompt（方便 PM 独立审查）

**few-shot 示例**: 年夜饭手选 2 句（"父亲的筷子落在桌面"+"手机屏幕是这张桌子上唯一不说谎的东西"）

**Haiku 能力预估**: 相比 Sonnet 独立挑选，Haiku 拿到 Opus 心法后可达 70-80%。en_v3 7/10，mixed_v3 7.5/10

**主要风险**: 位置偏置 / 凑数陷阱 / 专有名词泄漏 / few-shot 偏置（沉重 mood 过拟合 —— 好例 2 秋梨膏温暖对极已保留） / 剧本派故事画面感句本身稀缺

---

### ✅ TASK-MUSIC-LANG-AB-V2 Step 1 — meta-prompt v2 升级 (2026-04-20)

**背景**: V1 盲听揭盲：PM baseline > cn > en > mixed（和 @ai-ml 预估完全相反）
**教训**: mixed 版 Haiku 输出 855 字符稀释主基调；cn 版 265 字符反而最聚焦

**V2 升级**:
- 产出 `meta_en_v2.md` (9.6KB) / `meta_cn_v2.md` (9.4KB) / `meta_mixed_v2.md` (10KB)
- 新增 cross_sensory 4 条元原则（留白/N:1 综合/冲突映射/文化优先）
- 新增 3 精选示例：年夜饭 V4 (沉重) + 外公秋梨膏 V4 (温暖，防 mood 过拟合) + 反例保守格式
- **核心修复**: 硬约束 ≤400 字符（解决 v1 mixed 版 855 字符失控）
- 14 个数据占位符与 v1 完全一致

**预估**:
| 版本 | V1 实测排名 | V2 新预估 |
|------|:--------:|:--------:|
| en | 🥉 | 7/10 |
| cn | 🥈 | 6.5/10 |
| mixed | 末 | 6.5/10（修复长度失控）|

**关键不确定性**: Haiku 是否遵守 ≤400 字符硬约束

---

### ✅ TASK-MUSIC-LANG-AB Step 1 — 3 个语言变体 meta-prompt (2026-04-18)

**背景**: 产品将用 Haiku 4.5 API 生成音乐 prompt，需测试中/英/混合指令哪个效果最好

**产出**: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/meta_prompts/` 下 3 个文件
- `meta_en.md` — 纯英文指令，输出 mixed（跟示例走）
- `meta_cn.md` — 纯中文指令，输出纯中文
- `meta_mixed.md` — 中文讲哲学+英文给示例，输出 mixed

**一致性**: 14 个数据占位符完全一致（方便 @backend 用同一套 story input dict）

**Haiku 质量估计**: mixed 7/10 > en 6/10 > cn 5/10（example-driven few-shot 补偿 Haiku 能力差距）

**交接**: @backend 写 Python 脚本调 Haiku API × 3 + Mureka API × 3

---

### ✅ TASK-MUSIC-EXTRACT — 音乐 Prompt 输入格式定义 (2026-04-17)

定义了从 1_outline.json + 3_screenplay.json 提取"音乐 prompt 创作专用"精简文本的格式规范。
- 产出: `.claude/skills/music-prompt/templates/story_input_format.md`
- 含完整年夜饭示例 + 必须/可选字段标注 + 工作流复盘

### ✅ TASK-MUSIC-TRANSITION — 年夜饭转折测试 Prompt (2026-04-17)

为年夜饭故事写了显式分段转折 prompt（4 Section + 3 硬转折点），测试 Mureka 能否生成有段落变化的音乐。
- 产出: `test_output/manualtest/sq_upgrade_ab_test/20260304_113630/transition_test_prompt.md`
- PM 已调 Mureka API 生成 `bgm_transition_test.mp3`，等 Founder 试听

### ✅ TASK-MUSIC-REWRITE — 3 首 BGM Prompt 重写 (2026-04-17)

Founder 否决 #3/#4/#6 风格。重写后 PM 审查 PASS。

---

## 待处理队列

> **当前状态：空闲。** 等 Founder 试听转折测试 BGM + @backend 写提取脚本。

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 6人场景一致性 90%->95% | P2 | 暂缓 |
