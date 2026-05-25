# test28 全维度地毯式回溯 (gothic + object/灵魂)

**测试**: 《午夜钟魂》gothic + object/灵魂 (初雪 human / 贺时明 老钟匠灵魂 / 贺霜 幻影)
**目的**: 验证 Wave 12 修复 (gothic 画风 + adjust 异步) + object/灵魂 character_type + 单场景密闭剧
**时间**: 2026-05-25 09:59 创建 → 10:41:59 Pipeline 完成 → 10:48 重生 Shot 19 → 回溯
**方法**: 逐条 grep 三日志全量 (09:51 重启后=test28 全程) + 像素级看图 + 根因深挖, 不凭记忆

---

## 一、验证通过的成果 (Wave 12 + 新能力)

| 验证点 | 结果 | 证据 |
|---|---|---|
| **Wave 12 gothic 画风修复** | ✅ | 3 角色统一暗黑浪漫绘画, 初雪非 idol 照 (mandatory dark romantic painting + forbidden anti-anime 生效) |
| **Wave 12 adjust 异步化** | ✅ | 初雪换棕发不转圈, POST 202+job 轮询, 前端显示"肖像完成,重绘全身70%" |
| **Wave 12 identity 保持** | ✅ | 换发色后脸一致 (RISK-T17-9 portrait_ref refs=1 锁脸) |
| **Wave 12 sub-progress** | ✅ | "正在生成角色画像 1/3:初雪" (Stage 2 per-char band 6→10) |
| **object/灵魂 character_type** | ✅ | 贺时明半透明灵魂+齿轮裂纹, 贺霜幻影嫁衣, Layer 1 全程 wire |
| **3:4 画幅透传** | ✅ | shot 实际 1664×2218=0.75=3:4, 用户选择→生成层无 hardcode (含重生) |
| **20/20 shots + BGM** | ✅ | ShotValidator 最终全 PASS, gothic BGM 一次过 (0 linter FAIL) |
| **confirm-outline 接入** | ✅ | 选最后结局 → confirm-outline 200 → generate_images=True |
| **B52-fix reload** | ✅ | 确认角色后从 DB reload count=3 (用棕发初雪最新数据) |

backend 侧 test28 **极干净**: 0 ERROR / 0 CONTENT_SAFETY / 0 MySQL 500 / 0 BGM linter FAIL / 0 Gemini fallback。

---

## 二、问题清单 (逐条根因深挖 + 最佳方案)

### 🟡 P2-1: 每个确认环节(大纲/角色/场景预览)切换后端就绪但前端 10-30s 才显示 (Founder 核心体感)
- **现象** (Founder 用户视角): 大纲确认/角色预览/场景预览每个环节切换时, **后端已就绪但前端要 10-30s 才 get 到显示**。极端 >120s 触发"AI 正在创作中"兜底页 + 刷新 30s
- **根因深挖 (实测铁证, 修正之前"全列表"误判)**:
  - ❌ 之前误判: hydrate 拉全列表 GET /api/projects/ (44项目 N+1) — **错了, 已纠正**
  - ✅ 实际: 前端 hydrate 调**单项目** `GET /projects/{uuid}` (CreateContent L638), 非全列表
  - ✅ 真根因 3 因素叠加: ① **本地连阿里云 MySQL 公网往返实测 333-684ms/次** (TCP 连接实测, 核心) ② hydrate **并发 5 请求** (project + chapter status/story/storyboard/bgm 4 parallel, L660-720 Promise.all), 每个多次 MySQL round-trip ③ chapter **大 JSON 字段** (storyboard_json 20 shots) 传输。三者叠加 = 10-30s
- **关键判断: 生产环境大幅改善**: 本地开发连阿里云走【公网】(333ms/往返), **生产 VPS 在阿里云【内网】(<1ms, 快数百倍)** → 这个慢**主要是本地开发连公网 MySQL 特有**, 生产 VPS 部署后大幅缓解 (不会归零, 仍可优化)
- **最佳方案 (分层)**: ① 生产 VPS 内网部署 (最大头, 333ms→<1ms, 本地无法复现生产速度) ② 合并 hydrate 为 1 个聚合端点 (project+chapter 一次拿, 减并发 round-trip, 内网也有效) ③ chapter status 不拉 storyboard_json 全文 (大字段按需) ④ 连接池复用减握手
- **派**: Backend (聚合端点 + 大字段按需) + DevOps (确认生产 VPS 内网 MySQL) — **内测前必须在 VPS 实测确认生产速度**, 不能用本地公网延迟判断

### 🟡 P2-2: "返回工作台"兜底页 UX (确认流程不该让用户离开)
- **现象**: 角色/场景确认前 hydrate 超时 → 弹"AI 正在创作中 + 返回工作台"兜底页
- **根因**: CreateContent L1149 setHydrateError 兜底 UI 不区分"确认流程中"。确认流程还要确认角色+场景, 这时"返回工作台"会打断流程
- **最佳方案**: 兜底页按 ui_phase 区分 — 确认流程中 (char_review/scene_review 前) 超时改"继续等待/自动重试", 不给"返回工作台"; 仅纯生成/完成阶段才允许离开
- **派**: Frontend (CreateContent 兜底 UI 按 ui_phase 守卫)

### 🟡 P2-3: "后台生成去做别的"按钮忽有忽无 (UX 不一致)
- **现象**: storyboard(分镜)阶段**有**"后台生成" → scene_image_preparation 阶段**没有** → 场景确认后又有。按钮闪烁出现/消失 = 用户困惑
- **根因深挖**: 设计意图对 (StageC L110 "场景确认前不能离开"), STAGE_SUBTITLE 文案也对 (storyboard="请稍候"不带后台生成字样, RISK-T15-1) + scene_preparation 隐藏 (T21-NEW-7 v1.4)。**但"后台生成"按钮 (handleBackground L951) 的显示守卫没同步** — storyboard 阶段文案隐藏了但按钮还显示, 守卫不统一
- **最佳方案**: 按钮显示守卫统一 — 确认前全程 (story_generation/character_design/screenplay/storyboard/scene_image_preparation) 隐藏, 仅场景确认后 (image_generation/image_preparation/bgm/music) 一致显示, 与 STAGE_SUBTITLE 逻辑对齐
- **派**: Frontend (StageC 按钮显示条件)

### 🟢 P3-1: 404 分级 — Frontend Wave B 修复实测未生效 (新深挖)
- **现象**: client.log 18 个 chapters/1/{status,story,storyboard,bgm} 确认前 404 仍记 **level:network** (error 类), **0 个 routine-404**
- **根因深挖**: Frontend Wave B 改了 layout.tsx (L195 正则匹配 status/story/storyboard/bgm → routine-404), 但**实测 0 routine-404 + 18 network** → 修复**未生效**。可能: layout.tsx wrapper 改了但这些 404 走 api.ts 另一记录路径 (level:network), 或正则匹配了但 level 实际没改
- **教训**: **代码审查通过 (tsc/正则存在) ≠ 实测生效** — Wave B 我审查时看代码逻辑通过, 但没 e2e 实测 (当时未重启 backend), test28 实测才暴露
- **最佳方案**: Frontend 复查 layout.tsx routine-404 为何未生效 (是否 api.ts 重复记录 network / 是否 wrapper 未覆盖) + 补 e2e 验证
- **派**: Frontend (复查 404 分级实际生效)

### 🟢 P3-2: 单场景成片视觉单薄 (产品考量, 非 bug)
- **现象**: test28 整个故事单场景 (古董行内部), 20 shots 全在同一空间, 视觉丰富度受限
- **根因**: idea 设定 (密闭空间剧 + 落地钟灵魂), LLM 正确识别 1 物理场景, Pipeline 忠实生成。是 idea 取舍非 bug
- **最佳方案**: Stage 1 大纲/Stage 3 剧本阶段检测单场景 → **建议/提示**用户加场景 (非强制, 单场景剧是合理叙事形式)。提升内测用户成片丰富度
- **派**: PM 产品决策 + AI-ML (大纲 prompt 引导)

### 🟢 P3-3: Shot 19 手部畸形 — 决定【暂不修】(Founder+PM 权衡)
- **现象**: Shot 19 多指/手指畸形, retry 第3次 ShotValidator 判 PASS 但人眼看仍畸形 (用户重生后修复, 但耳朵精灵耳 — Founder 确认普通耳朵接受)
- **根因**: ① Seedream 手部生成局限 (AI 老大难) ② ShotValidator(Haiku) 手部判定阈值偏松 (判 PASS ≠ 人眼无瑕疵, LLM 视觉判手指是盲区)
- **决策**: **暂不收紧** ShotValidator — 收紧会致大量 shot 触发 retry (手部高频) → Pipeline 时间/成本翻倍 + 模型局限致 retry 仍畸形 → 卡循环。**过度 retry 比漏判更糟**
- **兜底**: 用户手动重生 (按需成本可控) + 长期靠 Seedream 模型进步
- **教训**: 不能只信 ShotValidator PASS, 人眼复核必要

---

## 三、健康兜底 (test28 正常工作)

| 机制 | 触发 | 结果 |
|---|---|---|
| adjust LLMFallbackChain (Haiku) | 1 (换棕发) | SUCCESS |
| music_bgm LLMFallbackChain (Haiku) | 1 | SUCCESS |
| IncompleteRead 重试 #1/#2 | 3+1 | 全自愈 (#3+ = 0) |
| ShotValidator + T20-48 anatomy retry | Shot 19 retry 3 次 | 第3次救回 (但人眼仍轻微瑕疵) |
| RISK-T17-9 portrait_ref 锁脸 | adjust 换发 | identity 保持 |
| B52-fix reload + 单模型 + 3:4 透传 | 全程 | 正常 |

---

## 四、与 test26 对比 (Wave 12 修复验证)

| 维度 | test26 (修前) | test28 (修后) |
|---|---|---|
| 画风统一 | ❌ cyberpunk 老周写实/陈明动漫分叉 | ✅ gothic 3 角色统一暗黑绘画 |
| adjust | ❌ 陈明转圈死等 90s | ✅ 初雪换发异步轮询+进度提示 |
| **结论** | — | **Wave 12 两个核心修复 e2e 实战验证通过** |

---

## 五、待办汇总 (内测前/后)

| 编号 | 优先级 | 问题 | 派 | 时机 |
|---|---|---|---|---|
| P2-1 | 🟡 | GET /api/projects/ 列表慢 (确认页拉全列表) | Backend+Frontend | 内测前 |
| P2-2 | 🟡 | "返回工作台"兜底 UX (确认流程不该离开) | Frontend | 内测前 |
| P2-3 | 🟡 | "后台生成"按钮忽有忽无 | Frontend | 内测前 |
| P3-1 | 🟢 | 404 分级 Wave B 修复未生效 | Frontend | 内测前后 |
| P3-2 | 🟢 | 单场景丰富度 (大纲引导多场景) | PM+AI-ML | 内测后 |
| P3-3 | 🟢 | Shot 19 手部 — 决定暂不修 | — | 重新评估触发 |

**P2-2 + P2-3 是同类 UX 原则**: 确认流程中 (角色/场景未确认完) 不让用户离开/困惑。建议合并 1 个 Frontend 任务修。
