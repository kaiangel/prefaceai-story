# TEST29《荷塘渡》全维度地毯式深度回溯

> 日期: 2026-05-26 | 项目: d5a3d409 (id=52) | 风格: watercolor | 情绪: 感人 | 画幅: 3:4
> 故事: 红锦鲤金爷(aquatic) + 菖蒲小蒲(plant) + 荷塘(concept_personified) —— 万物有灵 / 治愈 / 牺牲羁绊
> 执行: full-retrospective skill 6 步 (不凭记忆·不信自报·追完整调用栈·实测纠正纸面·分本地vs生产·像素级看图)
> **Founder 成片评分: 90/100, "22 个 shot 都很不错, BGM 很贴合"**

---

## 0. 测试设计意图与价值

test29 专为踩 **非人类角色盲区** 设计: 红锦鲤(aquatic) + 菖蒲(plant) 两个**真·非穿衣 type** 主角 + 从未 e2e 跑过的 watercolor。结果**价值拉满** —— 一次 e2e 炸出一条完整的「系统人类中心假设链」(5 个缺口), 同时验证了 Wave 13 的全部修复在真实 pipeline 生效。

**核心洞察 (本次最大收获)**:
> Stage 2 (CharacterDesigner) 的**数据层已正确通用化**(所有 type 的属性统一写进 `physical`), 但下游**消费层全部还是人类中心**: prompt builder / ShotValidator / Seedream 多角色构图 / BGM 提取器, 都假设"角色 = 类人结构"。**数据通用了, 消费没跟上** —— 这是 #5/#6/#7/#8 的同一个根。

---

## 1. 时间线 (e2e 全程 ~44 分钟)

| 时刻 | 阶段 | 结果 |
|------|------|------|
| 15:38 | 创建项目 + Stage 1 大纲 | ✅ 98s, 3角色/7情节/4场景 |
| 15:41 | confirm-outline + Stage 2 角色设计 | ✅ 99.9s, **#5e 非穿衣 type 0崩溃** |
| 15:43-45 | 3 角色 portrait (Layer1 watercolor) | ✅ 金爷/小蒲/荷塘 |
| 15:46 | (浏览器 tab 挂起) | 🟡 **#4 Packet 3× 500** (自愈) |
| 15:49-51 | 用户改"红锦鲤→金色锦鲤" reroll | ✅ **#6 adjust 异步**(job+轮询, 不转圈) |
| 15:46-55 | 角色确认页 (R4-1) | ✅ #4A 无误弹返回工作台 / B52 reload |
| 15:55-58 | Stage 3 剧本 | ✅ 161s, 7场景/22节拍 |
| 15:58-16:00 | Stage 4 分镜 | ✅ 22 shots |
| 16:02 | Stage 4.5 场景图 + R4-3 场景确认 | ✅ 4 location / #4B 按钮确认后才显 |
| 16:03-16:23 | **Stage 5 出图 22 张** | 🟡 8/22 同框 shot 融合+重试 (见#6#7) |
| 16:23-25 | Stage 6 BGM (Mureka) | ✅ 148s, 贴合 (#8 小观察) |
| 16:25:46 | **Pipeline 完成** | ✅ 总耗时 2650s, $1.14 |

---

## 2. ✅ 本轮验证通过的成果 (Wave 13 修复 + 既有能力, 全部真实生效)

**实测证据 = 这次 e2e 本身 (比单元测试更强的验证)**:

| 修复/能力 | 验证证据 | 结论 |
|-----------|---------|------|
| **#5e clothing 旁路防崩** | aquatic+plant+concept 三非穿衣 type, Stage 2 Schema 全过, 0 ValueError | ✅ 方案B(prompt指引)源头生效, 未触发A降级 |
| **#6 adjust/reroll 异步** | 改色 reroll → job fae41b97 + 轮询, portrait+fullbody 重生, 不转圈 | ✅ 异步链路完整 |
| **#4A 确认流程自动重试** | R4-1 等待期加载, 无误弹"返回工作台" | ✅ |
| **#4B 后台生成按钮** | 场景确认(R4-3)后才显示 "可以选择后台生成" | ✅ |
| **#5 404 分级** | `[ROUTINE-404]` 正确分级 (chapters/1/status 章节未建时) | ✅ 运行时实锤 (干净重启=新编译, 无 HMR stale 问题) |
| **B52 characters reload** | `B52-fix v3: characters reloaded from DB after R4-1 confirm` | ✅ 改色数据重新入内存 |
| **ETA 不冻结** | 5%→6%→...→95%, 持续递增 | ✅ |
| **T17 retry 硬上限** | `T17 Shot N 已达最大重试次数, 使用当前结果` | ✅ 融合 shot 放行, pipeline 不挂 |
| **条漫中文文字叠加** | shot_10/22 黑底白字旁白+气泡, 零乱码, 位置正 (像素级确认) | ✅ 非人类故事文字渲染正常 |
| **画幅 3:4 真生效** | sips: shot 01/10/22 全 1664×2218 = 0.750 | ✅ 用户选择透传到生成层 |
| **watercolor 画风** | 整体统一+通透, 风景/单主体 shot 很美 (Founder 90分) | ✅ |
| **BGM 贴合** | Mureka 148s, Founder "很贴合" | ✅ (分类有小瑕 见#8) |

---

## 3. 🔍 问题清单 (逐条根因深挖 + 最佳方案)

### 🟡 #4 [P2] Packet sequence —— tab 挂起突发并发→新建连接握手腐败→500

- **现象**: 浏览器 tab 挂起再恢复时, `chapters/1/status` 轮询 **3 次 500** (15:46:00/31/44)。前端标 transient 自动 retry, 用户最终正常进角色页 (自愈)。
- **根因深挖 (完整调用栈)**: 错误在 `aiomysql/connection.py:844 _request_authentication → :629 _read_packet` —— **新建连接的 MySQL 认证握手阶段**, 非查询、非复用脏连接。链: tab挂起→轮询积压→恢复突发并发→`pool_recycle=600s` 已回收 idle 连接→需同时新建多条→公网+Astrill VPN 并发握手→认证响应包序号错位→`pymysql.err.InternalError: Packet sequence number wrong`。
- **#5d 为何漏接**: `db_retry.py _is_transient_connection_error` 只认 `OperationalError/InterfaceError` 且(connection_invalidated 或 msg含2013/2006/2003) 或 OSError errno。此 `InternalError` 虽是 DBAPIError 子类(isinstance命中), 但无 connection_invalidated 也不含那几个码 → 判 False → 不重试 → 500。
- **环境判断**: **本地公网+Astrill VPN 特有**(握手腐败最坏场景)。VPS 内网 42ms 稳定同机房, 并发握手腐败概率大降。前端已 retry-on-resume 自愈。
- **最佳方案 (方案A, Founder 已定内测前修)**: `db_retry.py` 加 `_TRANSIENT_MESSAGE_FRAGMENTS=('packet sequence number wrong',)` 判 transient。安全: GET幂等已gated + retry重新checkout干净连接 + 自愈已证2nd attempt成功。次要: 前端 tab-resume serialize/dedupe 轮询突发。~30min。
- **派**: Backend (内测前)

### 🟡 #5 [P1-correctness/视觉中等] 非人类 type prompt builder 字段错配 → golden 丢 → 金爷红

- **现象**: 用户把金爷改"金色锦鲤", `physical.scale_color` 正确写成 `golden`, 但出图仍是**红橙色** koi (shot_10 像素级确认)。
- **根因深挖 (数据+代码双证据)**: 
  - 数据: 2_characters.json char_001 顶层 keys 有 `physical` **无 `aquatic`** (`'aquatic' in c → False`), aquatic 属性全在 `physical` 下。
  - 代码: portrait 走 `reference_image_manager.py:272 build_character_prompt` → `character_prompt_builder.py:787 _build_aquatic_description` 第 789 行 `a = character.get('aquatic', {})` → **从不存在的 `aquatic` key 读 → 空字典 → scale_color/species 全取空 → fallback "An aquatic creature"**。
  - 结果: 结构化 `golden` 信号在 prompt 层丢失 → 图只剩 description 自由文本("金色锦鲤"与"鳞片曾如烈焰般灿烂/brilliant flame"自相矛盾) + koi 红色强物种先验 → 红橙胜出。
- **🔴 系统性**: Stage 2 把所有非人类 type 属性写 `physical`, 但 `_build_aquatic/plant/insect/object_description` 等各 type 方法仍从 `character[type名]` 读 → **所有非人类角色结构化外观全丢, 只靠 description 兜底**。同源于 Stage 2 两条 `CharacterSchema` warning(plant/concept "无 type 特有字段")。
- **环境判断**: 与环境无关, 代码逻辑 bug, 生产同样复现。
- **最佳方案 (AI-ML)**: 各非人类 type builder 改从 `physical` 读 (Stage 2 实际写入位置), 或 `character.get(type) or character.get('physical')` fallback。这是记忆 `project_schema_humanoid_fallback_remaining` 那条"aquatic等5type待修Wave4.5"在 prompt builder 层的落地。附加: adjust 改色时同步 reconcile description 里矛盾的颜色比喻 + 强物种先验(koi)正向强调"golden NOT red/orange"(Seedream 无 negative_prompt)。
- **派**: AI-ML (内测前/后, Founder 定)

### 🟡 #7 [真缺陷·视觉影响经像素校准为"中等"] Seedream 把金爷(鱼)+小蒲(草)融合成一只怪物

- **现象 (像素级看图)**: shot_10 实图 —— 菖蒲(绿叶+白根)**从金爷鱼背上长出来、根扎进鱼身**, 焊成一只 chimera。非"两个独立角色同框"。自然度警告 3 次捕到 (shot 10/15 等), 描述 "plant growing directly from fish back"。
- **⚠️ 纸面判断纠正 (透明披露)**: 我在监控中曾标 #7 为 **"P1 最毁画面"**, 那是**基于日志文字描述**的判断。**像素级看图 + Founder 90分 纠正了它**: ① 融合是真的、语义错(本该两个独立生命); ② 但**水彩美学把它柔化成诗意/超现实观感**, 配文字"那根须一直在抖……它在用力"反而有"万物一体"意境; ③ **范围是子集** —— 仅 8/22 同框 shot(6,7,8,9,10,11,14,15)受影响, 其余 14 张(环境/单角色/结局)很美。**故降级: 真·通用性缺陷, 但视觉影响中等, 非"毁画面"。**
- **根因推测**: ① 故事文本"菖蒲根须缠住金爷身子"被模型过度字面化→长一起; ② 两个非人类角色各自 portrait 参考图没阻止融合; ③ shot prompt 缺"two SEPARATE beings, not merged"分离指令。
- **二级问题**: 自然度检查检测到融合却**误判为"intentional surrealist artistic choice"放行** —— 实际是 generation error, 检查逻辑对非人类组合过于宽容(自我洗白)。
- **环境判断**: 与环境无关, 模型行为, 生产同样复现。
- **最佳方案 (AI-ML)**: 多角色 shot prompt 强调角色分离("two distinct separate beings: a fish AND a plant, NOT fused, plant beside the fish") + 自然度检查对非预期融合不洗白(区分"故意超现实"vs"该分离却融合")。
- **派**: AI-ML (内测前/后, Founder 定)。**注: #7 是 #6 的真实成因之一** —— ShotValidator 数 0/2 部分是对的(确实没2个独立角色)。

### 🟡 #6 [P2] ShotValidator 视觉角色计数对非人类判 0 → 8/22 shot FAIL + 重试浪费

- **现象**: 8 个 expect-2-chars shot (金爷+小蒲) 全 `valid=False 预期2实际0`, 触发重试。
- **根因**: ShotValidator 用视觉模型"数角色"但人类中心, 水彩里的鱼+草数成 0。**叠加 #7 融合** → 确实没有 2 个独立角色 → 数 0 部分是对的。重试也救不了(再画还是融合/数不出)。
- **影响 (实测量化)**: 8/22 shot 各重试到 T17 上限后放行 → 成片不缺图。代价: **总耗时 44min (vs 正常 ~10-15min) + Seedream 38调用 $1.14 (vs 22基线 $0.66, +73%)**。这是 #6/#7 在规模上的真实账单 —— 不只画面, 还**多花七成钱 + 用户多等近 3 倍**。
- **环境判断**: 与环境无关, 生产同样复现 (非人类多角色故事必中)。
- **最佳方案 (AI-ML/Backend)**: ① 先修 #7(融合)→ 图里真有 2 个独立角色 → 计数自然过半; ② ShotValidator 计数对非人类 type 放宽/跳过(类似 T20-6 environmental 跳过), 或视觉 prompt 明确"count the fish/plant/object as characters"。
- **派**: AI-ML/Backend (内测前/后), 与 #7 联动

### 🟢 #8 [P3 低影响] BGM 提取器无人类时默认 'human' + watercolor 误归 western_realistic

- **现象**: `StoryMusicExtractor` 日志 `character_dominant_type='human'`, 但本故事 0 人类。`style_preset='watercolor' → style_category='western_realistic'`(水彩归西方写实略勉强)。
- **影响**: 低 —— 仅微调 BGM 情绪/风格选择, 不破坏画面/不阻塞。但属同一人类中心主线第 5 个缺口。Founder 实听"很贴合", 实际影响极小。
- **最佳方案**: BGM 提取器无人类时按实际主导 type 选基调; watercolor 等传统画风 style_category 映射校准。
- **派**: AI-ML/Backend (内测后)

---

## 4. 🟢 健康兜底 (正常工作, 无需修)

| 机制 | 表现 | 结论 |
|------|------|------|
| **IncompleteRead 重试** | 6 次网络截断 (公网/VPN), 退避重试全部成功 (shot 11 等) | ✅ 兜底设计奏效, 生产内网少见 |
| **T17 ShotValidator 重试上限** | 8 融合 shot 重试耗尽后放行, pipeline 不挂 | ✅ 硬上限正确 |
| **BGM duration linter** | FAIL→追加 repair_hint 重调 Haiku→2nd pass PASS | ✅ 自检自修 |
| **#5e clothing 降级** | 非穿衣 type 缺衣物降 warning 不 raise | ✅ (本次靠方案B prompt 未触发降级) |
| **CharacterSchema warning** | plant/concept "无 type 特有字段" 降 warning 不崩 | ✅ 不阻塞 (但暴露 #5 同源问题) |
| **幂等守卫** | generate-outline 多次请求返已存数据不重调 LLM | ✅ 不重复烧 LLM |

---

## 5. 🆕 新观察 (低优先, 待定性)

- **结局 shot_22 出现剧本未设定的人类**(撑船老人 + 第三人称旁白"那朵花是一条鱼许下的愿。它兑现了。")。可能是 Stage 3/4 有意加的**叙事框架**(路人见证传说, 艺术上很美很work), 也可能是角色一致性漂移。**倾向 by-design**(旁白视角自然), 但值得确认 Stage 3/4 是否会为无人类故事自动引入人类旁观者。派 AI-ML 评估是否需约束。

---

## 6. 与上轮 (test28) 对比

| 维度 | test28《午夜钟魂》 | test29《荷塘渡》 |
|------|-------------------|-----------------|
| 角色 type | supernatural 灵魂(类人, 有衣物) | aquatic鱼 + plant草 + concept (真非人类) |
| 暴露主线 | 404分级/hydrate性能/clothing旁路 | **非人类人类中心假设链 (5缺口)** |
| 成片质量 | - | **90分** (主骨架立得住) |
| 关键价值 | 验证 Wave12 + 挖 Wave13 | **验证 Wave13 全修复生效 + 系统性暴露非人类消费层缺口** |

---

## 7. 📋 待办汇总表

| # | 优先级 | 问题 | 派 | 时机 |
|---|--------|------|-----|------|
| #4 | 🟡 P2 | Packet sequence (#5d retry 漏接 InternalError) | Backend | **内测前 (Founder已定方案A)** |
| #5 | 🟡 P1-correctness | 非人类 type builder 读错字段 (golden丢) | AI-ML | Founder 定 |
| #7 | 🟡 真缺陷·视觉中等 | Seedream 融合非人类角色 + 自然度洗白 | AI-ML | Founder 定 (修#7连带缓解#6) |
| #6 | 🟡 P2 | ShotValidator 非人类计数 (浪费重试) | AI-ML/Backend | 与#7联动 |
| #8 | 🟢 P3 | BGM 默认 human + 画风误归类 | AI-ML/Backend | 内测后 |
| 新观察 | 🟢 | 结局 uncast 人类旁观者 (疑 by-design) | AI-ML | 内测后评估 |

---

## 8. 🎯 战略建议 (给 Founder)

**这不是 5 个孤立 bug, 是一个架构主题**: 数据层(Stage 2)已通用化, 消费层(prompt builder #5 / ShotValidator #6 / Seedream 构图 #7 / BGM #8)仍人类中心。**最优解不是零敲碎打, 而是一次协调的"非人类角色支持"专项** —— AI-ML 主导, 横扫四个消费层, 统一"角色 ≠ 类人"的假设。

**内测决策建议**: 
- 主骨架(叙事/画风/音乐/情绪/文字/画幅/异步/确认流程)全部 90 分级就绪, 人类故事完全可内测。
- #4 内测前修 (体验毛刺, 30min)。
- #5/#7 是**非人类故事**的硬伤 —— 若内测主推人类/类人题材, 可内测后修; 若想首发就展示"万物皆可"的通用性卖点, 建议 #5/#7 内测前一并修 (AI-ML 专项)。

---

*回溯依据: full-retrospective skill + feedback_carpet_review_deep_dive + feedback_trace_full_callstack_not_pattern + 像素级看图实测纠正纸面*
