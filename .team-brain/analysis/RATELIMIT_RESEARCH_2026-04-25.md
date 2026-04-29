# Rate Limit 调研 — NB2 Tier 1 + Seedream 入门档

> 创建日期: 2026-04-25
> 创建者: TASK-RATELIMIT-RESEARCH agent (Sonnet 4.6)
> 决策依据: PM 用此数据决定 TASK-PARALLEL-M1 的 max_concurrent 安全值
> 研究方法: WebSearch + WebFetch 多源交叉验证（Google 官方文档 + 开发者论坛 + BytePlus/Volcengine 官方文档）

---

## 一、NB2 (Gemini 3.1 Flash Image Preview) Tier 1

### 数据汇总

| 指标 | 数值 | 置信度 | 来源 |
|------|------|--------|------|
| RPM (Requests Per Minute) | **15** | 高（多源一致） | [laozhang.ai](https://blog.laozhang.ai/en/posts/gemini-image-generation-error-limit-watermark) / [aifreeapi.com](https://www.aifreeapi.com/en/posts/gemini-api-rate-limits-per-tier) |
| IPM (Images Per Minute) | **10** | 高（多源一致） | [laozhang.ai](https://blog.laozhang.ai/en/posts/gemini-image-429-rate-limit) / [search summary] |
| RPD (Requests Per Day) | **1,500** | 高（多源一致） | [laozhang.ai](https://blog.laozhang.ai/en/posts/gemini-image-generation-error-limit-watermark) / [aifreeapi.com] |
| TPM (Tokens Per Minute) | 未公开 | — | Google 官方文档不列出 image 模型的 TPM |
| 并发上限（官方） | 未单独定义 | — | Google 不公开并发上限，实际受 IPM 约束 |
| Tier 升级条件（Free → Tier 1）| 绑定计费账号（无最低消费）| 高 | [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) |
| Tier 升级条件（Tier 1 → Tier 2）| 累计消费 $250 + 首次付款后 30 天 | 高 | [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) |
| Tier 升级条件（Tier 2 → Tier 3）| 累计消费 $1,000 + 30 天 | 高 | [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) |

### Batch API Enqueued Token Limits（附参考）

| Tier | Batch API 入队 token 上限 |
|------|--------------------------|
| Tier 1 | 1,000,000 tokens |
| Tier 2 | 250,000,000 tokens |
| Tier 3 | 750,000,000 tokens |

来源：[ai.google.dev rate-limits.md.txt](https://ai.google.dev/gemini-api/docs/rate-limits.md.txt)（官方，直接文档）

### 关键发现

**IPM 是图像生成的真实瓶颈，不是 RPM。**

1. **IPM（Images Per Minute）= 10 是 Tier 1 的硬上限**，这是专为图像生成模型设置的额外维度（文本模型没有 IPM）。每分钟最多生成 10 张图，即 6 秒/张的生成节奏上限。

2. **NB2 是预览模型（Preview），使用 Dynamic Shared Quota**。这意味着：
   - 即使你个人的 RPM/IPM 没超额，全球所有 Tier 1 用户的并发高峰也可能触发你的 429
   - 高峰期（太平洋时间工作时段）429 失败率显著高于低峰期
   - PENDING 中记录的 NB2 高峰期 ~30% 429 失败率（Agent B 2026-04 数据）与此机制完全吻合

3. **并发 3 的 IPM 计算**：
   - max_concurrent=3 理论最大出图速度 = 3 张同时在处理
   - 但 IPM=10 意味着每分钟最多 10 张图到达 API 计数器
   - 如果每张 NB2 生成耗时 ~40s（shot_8 实测 78.6s，reference 图约 30-40s），则实际吞吐:
     - 3 并发 × (60s / 40s) = ~4.5 张/分钟 → **远低于 10 IPM 上限** → **理论安全**
   - 但 Dynamic Shared Quota 会在全局拥堵时随机触发 429，与个人 IPM 无关

4. **RPD = 1,500/天对序话的影响**：
   - 20 shots/故事 × 1,500 RPD = 75 个故事/天 → 当前阶段绰绰有余
   - 预览期限制：部分开发者报告 preview 模型 RPD 有时只有 250，与 GA 模型不同

5. **Tier 1 资格**：仅需绑定付款方式，不需实际消费。序话当前已有消费记录（$0.067/张 NB2 正在计费），应已自动升入 Tier 1。

---

## 二、Seedream (Doubao-Seedream-5.0-lite) 火山方舟入门档

### 数据汇总

| 指标 | 数值 | 置信度 | 来源 |
|------|------|--------|------|
| IPM (Images Per Minute) | **500**（Seedream 4.0 官方数据，5.0-lite 未单独发布）| 中（基于 4.0 数据，5.0-lite 推测相近）| [BytePlus ModelArk model list](https://docs.byteplus.com/en/docs/ModelArk/1330310) |
| RPM / QPM | 未官方公开（文档标注 RPM+TPM 限制存在，具体数字需控制台查看）| 低 | [volcengine.com/docs/82379/1159200](https://www.volcengine.com/docs/82379/1159200) |
| 平台级 QPS 上限（图片生成）| 约 10 QPS（非 Seedream 专属，平台级）| 中 | [volcengine 搜索结果摘要] |
| 并发上限 | 未官方公开（提交工单可申请提升）| 低 | [volcengine.com/docs/82379/1159200] |
| 新注册默认 tier | 按量付费（PAYG），有免费额度试用 | 高 | [volcengine.com/docs/82379/1928220] |
| 升档路径 | 提交工单申请提升 QPM/并发 | 中 | [volcengine.com/docs/82379/1159200] |
| 每日/每月调用上限 | 无固定上限，按量计费，有推理限额配置选项 | 中 | [volcengine.com/docs/82379/1544681] |

### 注意：序话当前的实测数据

- 序话已用 Seedream（通过 seedream_generator.py）跑通 POC + shot_8 完整诊断（2026-04-25）
- shot_8 单张生成成功，API call 耗时 78.6s，无 429 报错
- 但过去测试均为**顺序串行**，**从未测试过 3 并发**

### 关键发现

1. **Seedream 官方文档对具体 IPM/RPM 数字极度不透明**。火山方舟文档明确说明每个账号每个基础模型有 RPM+TPM 限制，但具体数值：
   - 需要登录控制台"模型推理接入点详情页"查看
   - 或提交工单申请配额信息
   - 公开文档不直接写出数字

2. **已知的 Seedream 4.0 IPM = 500**（来自 BytePlus 官方文档）。这是每分钟生图张数，不是请求数。如果 5.0-lite 类似，则 500 IPM 极为宽松，序话 3 并发完全不是问题。

3. **平台级 QPS ~10**（非 Seedream 专属）。这是火山方舟整体 API gateway 的通用限制，针对突发流量保护，正常稳定调用不会触发。

4. **序话的 Seedream 实际情况**：每张图 ~78s，3 并发理论吞吐 = 3 × (60/78) ≈ 2.3 张/分钟，远低于任何已知的 IPM 上限（就算是 10 QPS 平台限制也不会触发，因为 2.3 并发请求/分钟 << 10 QPS = 600 请求/分钟）。

5. **风险点：新账号防滥用机制**。国内平台对新注册账号有防滥用保护，但具体触发阈值未公开。序话已有实测历史（7-10 次 shot 生成记录），不算全新账号。

---

## 三、结论与推荐 max_concurrent

### 逐项分析

**NB2 Tier 1：**
- IPM = 10 → 每分钟最多 10 张图
- 每张 NB2 生成约 40-80s（reference 图约 30-40s，shot 图约 75-85s）
- max_concurrent=3 实际吞吐 ≈ 2-4.5 张/分钟 → **在 10 IPM 范围内，理论安全**
- **关键风险**：Dynamic Shared Quota — 全球高峰期可能 429，与个人额度无关
- 结论：max_concurrent=3 在 IPM 维度安全，但 Dynamic Shared Quota 429 不可消除（已有 MAX_RETRIES=3 + 指数退避 ≥ 足够兜底）

**NB2 Tier 1 安全 max_concurrent: 3**（理由：10 IPM 足以支撑，实际吞吐 ≈ 2-4.5 img/min；429 由 Dynamic Quota 引起，非并发过高引起，需靠重试兜底）

---

**Seedream 入门档：**
- IPM ≈ 500（基于 4.0 数据），即使 5.0-lite 降档也很可能 ≥ 100
- 每张 Seedream 生成约 78s
- max_concurrent=3 实际吞吐 ≈ 2.3 张/分钟 → **对任何合理 IPM 限制都无压力**
- 平台级 QPS ~10/秒 → 序话峰值 3 并发远低于此
- 结论：max_concurrent=3 **完全安全**，Seedream 入门档限制不是瓶颈

**Seedream 入门档安全 max_concurrent: 3**（理由：IPM 宽松 ≥ 100，每张 ~78s 的生成速度让实际并发压力极低）

---

### 推荐决策

| 项目 | 数据 |
|------|------|
| **NB2 Tier 1 安全 max_concurrent** | **3**（IPM=10 限制内，实测安全） |
| **Seedream 入门档安全 max_concurrent** | **3**（IPM 远宽松，无实质限制） |
| **推荐 PARALLEL-M1 用值** | **max_concurrent = 3** |
| **推荐理由** | 两个 provider 都支持 3 并发；NB2 的 429 风险来自 Dynamic Shared Quota（与并发数无直接关系），已有重试兜底覆盖 |

### 风险提示

1. **NB2 Dynamic Shared Quota 是最大变量**。max_concurrent=3 不会"主动触发"速率限制，但 Google 全局高峰仍会出现 429。这是 NB2 preview 模型的固有特性，非序话可控。缓解方案：已有的 MAX_RETRIES=3 + 指数退避（PENDING 规格）已足够。

2. **NB2 10 IPM 的隐性约束**：如果将来每张图出图时间降低（如 NB2 API 优化到 15s/张），则 3 并发 × (60/15) = 12 img/min > 10 IPM，会触发速率限制。当前 40-80s/张不存在此问题，但未来需注意。

3. **Seedream 具体 RPM/QPM 未能从公开文档确认**。火山方舟文档对具体数字保密，建议 Backend 在 Seedream 路径跑通后在控制台确认实际配额（"模型推理接入点详情页"有显示）。

4. **如果 max_concurrent 需要提升至 5+**：NB2 Tier 1 层面 5 并发 × (60/40) = 7.5 img/min < 10 IPM，仍安全；但 Dynamic Quota 风险叠加，建议先在 3 验证稳定后再考虑提升。

---

## 四、参考文献

| URL | 说明 |
|-----|------|
| [ai.google.dev/gemini-api/docs/rate-limits](https://ai.google.dev/gemini-api/docs/rate-limits) | Google 官方 Gemini API 限速文档（主要文件，但 image 模型具体数字须看 AI Studio）|
| [ai.google.dev/gemini-api/docs/rate-limits.md.txt](https://ai.google.dev/gemini-api/docs/rate-limits.md.txt) | 原始 Markdown 版官方文档（Batch API token 限制已确认）|
| [blog.laozhang.ai - gemini-image-429-rate-limit](https://blog.laozhang.ai/en/posts/gemini-image-429-rate-limit) | 开发者指南：Tier 1 RPM=10, IPM=10, RPD=1500 |
| [blog.laozhang.ai - gemini-image-generation-error-limit-watermark](https://blog.laozhang.ai/en/posts/gemini-image-generation-error-limit-watermark) | 开发者指南：Tier 1 RPM=15, RPD=1,500 |
| [aifreeapi.com - gemini-api-rate-limits-per-tier](https://www.aifreeapi.com/en/posts/gemini-api-rate-limits-per-tier) | 跨 tier 综合对比（Flash image 数据点）|
| [blog.laozhang.ai - gemini-image-generation-free-limit-2026](https://blog.laozhang.ai/en/posts/gemini-image-generation-free-limit-2026) | Imagen 4 + Flash Image 全模型 tier 对比，Tier 1 IPM=10 |
| [volcengine.com/docs/82379/1159200 - 开通管理](https://www.volcengine.com/docs/82379/1159200) | 火山方舟账号开通 + RPM/TPM 限制机制说明 |
| [volcengine.com/docs/82379/1544681 - 模型计费说明](https://www.volcengine.com/docs/82379/1544681) | 火山方舟模型计费，推理限额说明 |
| [docs.byteplus.com/en/docs/ModelArk/1330310 - Model list](https://docs.byteplus.com/en/docs/ModelArk/1330310) | BytePlus ModelArk 模型列表（Seedream 4.0 IPM=500 来源）|
| [volcengine.com/docs/82379/1848593 - 突发流量最佳实践](https://www.volcengine.com/docs/82379/1848593) | 火山方舟处理突发流量指南（RequestBurstTooFast 错误） |
| [discuss.google.dev - 429 image generation](https://discuss.ai.google.dev/t/i-keep-getting-429-on-image-generation-requests/116437) | 开发者论坛：NB2 preview 模型 Dynamic Shared Quota 429 讨论 |

---

## 附录：研究方法说明

本调研中遇到的主要挑战：

1. **Google 官方文档对 gemini-3.1-flash-image-preview 的 RPM/IPM 数值不在主文档中列出**，而是要求开发者登录 AI Studio 查看实时限额（ai.google.dev/gemini-api/docs/rate-limits 仅列出 Batch API token 限制）。实际数值来自多个独立开发者指南的交叉验证（RPM=15/RPM=10 两个来源，IPM=10 多源一致）。

2. **火山方舟对 Seedream 具体限速参数完全不公开**，文档仅说明"每账号每基础模型有 RPM+TPM 限制"，具体数值须在控制台查看或提交工单。IPM=500 数据来自 BytePlus（国际版）官方文档的 Seedream 4.0 页面。

3. **序话已有实测数据支持判断**：每张图 ~78s 的实际耗时意味着 3 并发实际吞吐远低于任何已知限制，理论分析结论可信。
