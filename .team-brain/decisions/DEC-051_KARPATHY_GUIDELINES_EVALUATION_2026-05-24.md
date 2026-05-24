# DEC-051: karpathy-guidelines 编码规范 skill 引入评估

**评估日期**: 2026-05-24
**评估人**: PM (产品守护者 + 团队协调者视角)
**评估对象**: `/Users/kaisbabybook/.claude/skills/karpathy-guidelines/SKILL.md` (65 行, 4 条编码行为规范)
**Founder 要求**: 地毯式深挖 + 明确裁决 (该不该用 / 怎么用 / 谁用)

---

## 事实校准 (评估前提)

- 非 Karpathy 本人写, 是第三方"受其观点启发"整理 — 归属是营销包装
- "准确率 65%→94%" 查无一手出处, 杜撰
- 唯一严肃实验 (ETH Zurich SWE-bench): 这类 context 文件对 agent 成功率**无提升甚至略降 ~3%**
- **本评估完全基于"4 条规则本身是否适配序话Story"判断, 不因名气倾向, 不因神话破灭一票否决**

---

## ① 逐条对标表 (规则 × 重叠/冲突/补强/无关 + 依据)

| karpathy 规则 | 序话Story 现状 | 判定 | 依据 (文件:行) |
|---|---|---|---|
| **1. Think Before Coding** (陈述假设 / 不确定就问 / 多解释不默选 / 不清楚停下问) | 已分散覆盖, 但偏"问 PM"非"陈述假设" | **🟡 重叠 + 部分补强** | backend.md L429+L570 "需要需求确认 → @pm" / backend.md L467 "改高风险文件前先说我要改这个会跑回归" / ai-ml.md L375 "待验证的假设" 标注 / pm.md L154-162 需求过滤器 / xhteam skill "如有困惑立即 SendMessage 告知 PM, 不带疑问开干" |
| **2. Simplicity First** (最少代码 / 无投机功能 / 无单用途抽象 / 无不必要防御) | 高度重叠 (核心原则) | **🟢 重叠 + ⚠️ 1 处冲突** | CLAUDE.md "代码质量原则 15 No backward compatibility" / backend.md L191+L469 "拒绝兼容代码, 兼容会变屎山" / pm.md L162+L373 需求过滤器拒绝兼容 / 全局 CLAUDE.md 5/24 已加 Simplicity First 完整章节。**⚠️ 冲突**: 规则 2 "No error handling for impossible scenarios" vs 项目 CLAUDE.md "错误处理: LLM 失败 fallback / 图像失败重试 3 次 / 所有服务都有降级策略" |
| **3. Surgical Changes** (只动必须 / 不顺手优化 / 匹配风格 / 每行可追溯 / 不删别人死代码) | 高度重叠 (协作机制核心) | **🟢 重叠** | backend.md L490 文件范围 + L500 禁止修改 / ai-ml.md L633+L643 同 / CLAUDE.md 关键文件警示 (image_generator.py 🔴) / memory feedback_stay_in_role + feedback_carpet_review_deep_dive (越权 check) / 全局 CLAUDE.md 5/24 已加 Surgical Changes 完整章节 |
| **4. Goal-Driven Execution** (任务转可验证目标 / 先写复现/验证测试再实现 / 循环到通过) | 部分重叠 — 项目是"生成→回归验证"非严格 TDD | **🟡 补强 + 1 处不匹配** | backend.md L198 改高风险跑回归 / ai-ml.md L447/L486/L560 通知 tester 跑回归 / tester.md 全套回归文化 (test_*_regression.py) / CLAUDE.md "回归不通过必须回滚" / KEY_LEARNINGS #47 PM 自跑 verify。**不匹配**: 规则 4 的"先写复现测试再实现 (TDD)" — 项目实际是"图像生成后跑一致性回归", 不是严格测试先行 (生图无法 TDD) |

---

## ② 重叠度与红线校验结论

### 重叠度: ~85% 已被现有体系覆盖

- 规则 2 + 规则 3 = **全局 CLAUDE.md 5/24 已加完整章节** (Founder 已落地) + 项目 backend.md/ai-ml.md/pm.md 早有等价约定
- 规则 1 = 分散在 agent "需求确认 → @pm" + xhteam "不带疑问开干"
- 规则 4 = tester.md 回归文化 + CLAUDE.md 回归要求 + KEY_LEARNINGS #47

**再引入 karpathy-guidelines 独立 skill = 噪声 + 占 token + 重复**。叠加 ETH 实验"context 文件无提升", 引入独立 skill 收益接近 0。

### 红线校验 (按序话Story验收红线逐项过)

| 红线 | 规则是否诱导破坏 | 结论 |
|---|---|---|
| 角色一致性 | 规则 3 "match existing style" 跟"不破坏一致性"**同向** | ✅ 安全 |
| 通用性 (不硬编码故事/角色/风格) | 4 条规则均无关 | ✅ 无关 |
| 中文泄露到 image_prompt | 4 条规则均无关 | ✅ 无关 |
| 风格漂移 | 规则 3 不动无关代码, 反而保护 StyleEnforcer | ✅ 安全 |
| **防御性 fallback 完整性** | 🔴 **规则 2 "No error handling for impossible scenarios" 有诱导风险** | ⚠️ **需明文豁免** |

**🔴 唯一真红线**: 规则 2 若被 agent 教条执行, 可能删掉序话Story的 critical fallback —
- `LLMFallbackChain` (T22-NEW-4 Haiku→Gemini→Sonnet)
- T20-14 Gemini→Claude fallback (5/22 Google revoke key 时救了整个 Pipeline)
- `ShotValidator` retry (T17, 多次救回 chars 错图)
- Layer 1 inject try/except 兜底 (W9-1/W9.1)
- CLAUDE.md "所有服务都有降级策略"

这些**不是 "impossible scenarios"**, 是**已知高频 transient error** (API overload / key revoke / 模型不听话)。必须明文区分, 否则 agent "简化"时误删 = P0 生产灾难。

---

## ③ 最终裁决与落地方案

### 裁决: **部分采纳 — 不引入独立 skill, 仅补 1 条红线豁免**

| 维度 | 决定 |
|---|---|
| 全局 CLAUDE.md (Founder 5/24 已加 Simplicity First + Surgical Changes) | **保留不动** — 已生效, 措辞克制, 覆盖规则 2+3 |
| karpathy-guidelines 独立 skill | **不引入项目** — 85% 重复 + ETH 实验无提升 + 占 token 噪声 |
| 项目 CLAUDE.md | **补 1 条防御性 fallback 豁免** (红线, 防教条简化误删 fallback) |
| 规则 1 (Think Before Coding) | **不单独写** — agent "需求确认 → @pm" + xhteam "不带疑问开干" 已覆盖。**且自动 Pipeline 不适用"不确定就停"** (Pipeline 跑 Stage 1-6 不能每步停下问, 靠 fallback 兜底而非停下) |
| 规则 4 (测试先行 TDD) | **不强推 TDD** — 维持"生成→回归验证"文化 (生图无法 TDD)。已有 backend.md L198 + tester 回归足够 |

### 谁用 / 谁不用

| Agent | 适用性 |
|---|---|
| backend / ai-ml | ✅ 全局 Simplicity + Surgical 适用 (写代码) + 新增 fallback 豁免红线 |
| tester | ✅ Goal-Driven 天然契合 (本就写回归测试) |
| frontend | ✅ 全局 Simplicity + Surgical 适用 |
| devops | 🟡 部分 (脚本/配置适用, 部署流程靠 SOP 不靠这套) |
| **pm / resonance** | ❌ **不写代码, 4 条规则均不适用**。PM 已有需求过滤器 + xhteam 审查铁律 |

### 可直接粘贴文本 (加到项目 CLAUDE.md "### 代码质量原则" 第 15 条之后)

```markdown
16. **简化的红线 — 防御性 fallback 不可删（Karpathy Simplicity 规则的项目豁免）**：
    全局 CLAUDE.md 的 "Simplicity First / No error handling for impossible scenarios"
    适用于**真正不可能的场景**，但**严禁**以"简化"名义删除以下已知 transient error 的兜底：
    - LLMFallbackChain (Haiku→Gemini→Sonnet, T22-NEW-4)
    - Stage 1-5 LLM 的 Gemini→Claude fallback (T20-14)
    - ShotValidator retry (T17)
    - Layer 1 inject 的 try/except 兜底 (W9-1/W9.1)
    - image_generator 重试 3 次 / 所有服务降级策略
    判据：API overload / key 失效 / 模型不听话 = **已知高频场景**，不是 impossible。
    删任何 fallback 前必须 @pm 确认。（DEC-051）
```

### 优先级: **P3** (规范优化, 不阻塞内测)

理由: 全局 2 条已由 Founder 落地生效, 真正新增的只有 1 条红线豁免 (防御性)。不是新功能、不阻塞内测启动、无紧迫性。内测后 Wave 11 一并处理即可。

---

## ④ 一句话给 Kai 的结论

**不值得引入这个 skill** —— 它 85% 是我们 CLAUDE.md + agent 规范早有的东西 (No backward compatibility / 文件范围边界 / 回归文化), 你 5/24 已把最有用的 2 条 (Simplicity + Surgical) 加进全局 CLAUDE.md 就够了; 唯一要补的是 **1 条红线** —— 明文禁止 agent 借"简化"删掉我们的 fallback (上次 Google 封 key 全靠 fallback 救场), 我已写好可直接粘贴。规则 1"不确定就停下问"对写代码的 agent 有用、但**对自动 Pipeline 不适用** (跑生成不能每步停), 规则 4"测试先行 TDD"我们生图场景本就做不了, 维持现有"生成→回归"即可。定 P3, 内测后再落地那条红线, 不急。
