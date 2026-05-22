# test9 前端体验完整时间线 — 4+ Bug 复现素材

> **创建日期**: 2026-05-09 16:05
> **目的**: Founder 实测 test9 时前端从角色预览阶段开始就出错，记录每一步用户体感 + backend 真实状态对照，作为后续 frontend 修复 agent 的无损上下文素材
> **Founder 强调**: "这次 test9 前端在角色预览开始就是错误的，为了更好的修复，之后要毫无遗漏的记下来"

## 测试参数

- project_uuid: `a7a7763b-1737-4ced-bff6-515a485a2ada`
- idea: 55岁数学老师退休那天偷偷报了高考，30年前差0.5分丢的省状元，他想再拼一次。
- mood: **热血**（Stage A 选）
- 风格: illustration（数字插画）
- 画幅: **1:1**
- 篇幅: 短篇 (~18 张)
- 浏览器: Chrome 隐身窗口
- 测试目的: 验证 5-09 修复批 (B33+B34+B26+B27+B28) 在新 mood/aspect_ratio 组合下回归

## 完整时间线对照（用户体感 vs Backend 真实）

| 时刻 | URL | UI 用户看到 | Backend 真实 | 问题/良好 |
|------|-----|----------|-----------|---------|
| **15:50:09** | /create/{uuid}/(input) | 提交 idea + 选项 | INSERT projects: aspect_ratio='1:1', user_selected_mood='热血' | ✅ B33 持久化生效 |
| 15:50:11 | /outline (跳转) | "正在加载你的故事..." spinner | `[GenerateOutline] 传给 LLM: user_selected_mood: 热血` | ✅ B33 注入 |
| 15:50:12 | /outline | spinner | `B34: READ 事务已提交，释放 row lock，开始调 LLM` | ✅ B34 真生效 |
| 15:50:12 | /outline | spinner | `[StoryOutlineGenerator] B33 user_selected_mood: 热血 (强制注入 LLM 约束)` | ✅ |
| ~15:51:58 | /outline | 显示大纲编辑页 (~100s LLM) | LLM 完成，raw_outline_json 写 DB | ✅ outline.visual_tone.overall_mood='heroic' |
| 15:51:58+ | /outline | **大纲编辑页 (Image #3)**：故事标题/简介/角色/情节/结局 | — | ✅ **mood section 真彻底删除**（B33 frontend 闭环） |
| 15:53:36 | /outline | 用户点"确认并开始生成" | ConfirmOutline 收到 + OBS-4: user_selected_mood='热血' (双轨) | ✅ |
| 15:53:50 | /generating | 跳转 + spinner "正在加载..." | ConfirmOutline 完成 (UX-2 一致性检查 fail 非阻塞) | ⚠️ UX-2 解析失败但非阻塞 |
| 15:53:53 | /generating | spinner | StartGeneration ✅ Pipeline 启动 | ✅ |
| 15:53:54 | /generating | "AI 正在创作中" (B28 slow warning, >15s 触发) | character_design stage, progress=2 | ✅ B28 slow warning 真生效 |
| 15:54:02 | /generating | "AI 正在创作中" 持续 | `[CharacterDesigner] [尝试 Claude Sonnet 4.6]` LLM 开始 | — |
| **15:54:15** | /generating | 仍 "AI 正在创作中" | **Monitor 报 backend ok→alive_no_health** | 🚨 **B35 真根因**: sync claude_client 阻塞 event loop |
| 15:55:16-15:55:23 | /generating | 终于显示进度条 2% "大纲已确认，正在设计角色..." | LLM 完成 (~70s) backend 恢复 ok | ✅ 但用户等了 1-2 分钟才看进度条 |
| 15:55-15:56 | /generating | 进度条慢慢爬 | 3 个角色 portrait png 写入 character_refs/ (1MB+/张) | ✅ 1:1 画幅生效 (待 verify 1024×1024) |
| ~15:56-15:57 | /characters | **(Image #5)** "正在加载你的故事..." spinner，**0 角色卡片** | chapter.characters_json 已含 3 角色 + portrait_url | 🔴 **B36 v2: 角色预览页空白** — 数据有但 frontend hydrate 没渲染 |
| ~15:57 | /characters | **(Image #6)** "角色预览" 标题 + "16 秒后自动继续" 倒计时 + "确认角色，继续"按钮 + **3 角色卡片仍 0 个** | job stage=character_ready progress=10 msg=`角色设计完成，请确认角色和场景` | 🔴 **B36 v2 关键体验问题**：用户看不到角色，被强制倒计时，被迫确认 |
| 15:57:07 | /characters | 用户 (被迫) 点"确认角色，继续" 或 16s 倒计时自动跳 | ConfirmCharacters ✅ | ⚠️ 用户没真"确认" — 是被迫 |
| 15:57:09 | /scenes (跳转) | "正在加载你的故事..." spinner | Pipeline R4-1: 用户已确认角色 (等待 28s) | — |
| **15:57:23** | /scenes | spinner 持续 | **backend ok→alive_no_health** (Stage 3 第 1 批 LLM) | 🚨 又是 B35 |
| 15:59:04 | /scenes | spinner 持续 | backend 恢复 ok (第 1 批完成) | — |
| 15:59:34 | /scenes | spinner 持续 | **alive_no_health** (Stage 3 第 2 批 LLM) | 🚨 B35 |
| 15:59:54-16:00:58 | /scenes | spinner 5+ 分钟 | screenplay_writer Claude 响应 12326 chars 耗时 114.7s | — |
| 16:01:00 | /scenes | spinner 6 分钟 | Stage 3 完成 (10 场景 / 21 action_beats), 进入 Stage 4 | ✅ Backend 真在跑，frontend 看不到 |
| **~16:01-16:04** | **/outline (跳回!)** | **(Image #4) 红色感叹号 "服务器正忙（AI 正在创作中），请稍后刷新重试" + "返回工作台" 按钮** | Stage 4 LLM 跑中 alive_no_health | 🚨 **B28 timeout 触发但跳错位置** — 应跳"重试" 不应跳到 /outline （前端路由 fallback 错误） |
| 16:04:05 | /outline 错误页 | (Founder 关 tab) | Stage 4 完成，进入 Stage 5 NB2 图片生成 | ✅ |

## 总结：4+ 个独立 bug 在一次测试连环爆发

### 🔴 B36 v2 — 角色预览页 0 卡片（P1 用户体验灾难）
- 数据完整: 3 角色 portrait png (1MB+/张) + characters_json + portrait_url
- 但 frontend StageC 没渲染卡片 → 只剩标题 + 倒计时 + 按钮
- 用户在不知道角色长啥样的情况下被迫"确认"
- B26 v1 修复（portraitErrors silhouette dark theme）只覆盖了"图加载失败"，没覆盖"characters 数组是空"
- 修复方向: D.21 hydrate chain 必须先 populate state.characters 才能 render StageC; 倒计时只在 characters.length > 0 才启动; 加 placeholder UI

### 🔴 B35 — sync claude_client 阻塞 uvicorn event loop（P1 真根因）
- character_designer.py / screenplay_writer.py / storyboard_director.py / story_outline_generator.py / image_generator.py 都用 `anthropic.Anthropic()` (sync)
- 每次 LLM 调用 30-120s 期间 backend 完全卡死，所有 HTTP 请求暂停
- test9 实测: 70s + 114s × 2 + 多次 Stage 4 LLM = 累计 5-6 分钟前端无响应
- 修复方向: 全替换 `AsyncAnthropic()` + `await messages.create(...)` (Plan A，5 文件)
- **Backend agent 已派活后台修中** (2026-05-09 16:03)

### 🟡 B28 timeout 路由 fallback 错误（P2）
- 5-6 分钟 frontend hydrate 反复失败 → 触发 120s timeout 错误页
- 但**错误页跳到 /outline URL**（Image #4）— 不是 /generating 的"重试"页
- B28 修复时 fallback 路由配错: outline 错误页让用户回退一步而非显示进度
- 修复方向: timeout 错误页应该提供 "重试" / "查看后台进度" 而非自动 fallback /outline

### 🟡 B27 路由表 stale backendStage 兜底缺失（P2）
- 如 createUrl.ts: `if (urlStage === "scenes") { if (POST_CHAR_STAGES.has(backendStage)) return "generating" }`
- 但当 backendStage 是 stale 旧值（hydrate 没刷新成功），`backendStage="character_design"` 不在 POST_CHAR_STAGES set → 返回 "scenes" → spinner 卡
- 用户看到的"5-6 分钟 spinner"很可能是 backendStage stale + 反复 hydrate 拿不到新值
- 修复方向: hydrate 失败时 retain 旧 backendStage 但加显示 "hydrate 失败，正在重试" + 后台进度查询替代方案

### 🟡 UX-2 一致性检查 LLM JSON 解析 fail（P3 非阻塞）
- 15:53:50 `[ConfirmOutline] UX-2: 一致性检查失败（非阻塞）: Unterminated string starting at: line 1 column 573`
- Sonnet 4.6 输出含 markdown 代码块 / 多余字符，json.loads 失败
- 当前 try/except 兜底，warnings 返空
- 修复方向: prompt 加更严格"只输出 JSON 不要 markdown 代码块" 或加更鲁棒解析（截取 ```json...``` 块）

## 用户原话（必须记录）

> "前面的 generating 页面刚开始正在创作中有点慢，大概过了 1-2 分钟才出来进度条，目前来看问题不大，可以记下来之后审查" (15:55)
>
> "仍然看不见角色，被迫继续" (15:57)
>
> "scenes 页面还在加载中 大概 2 分钟了" (15:59)
>
> "scenes 页面还在加载中 又过去了 2 分钟" (16:00)
>
> "可以 按照你的推荐来 选 C 双轨" (16:03)
>
> "那这次 test9 前端在角色预览开始就是错误的，为了更好的修复，之后要毫无遗漏的记下来" (16:04)

## 后续修复清单（按优先级）

| 优先级 | Bug | 修复方向 | 状态 |
|------|-----|---------|------|
| 🔴 P1 | B35 sync claude → AsyncAnthropic | Plan A 5 文件替换 | Backend agent 后台修中 (a67608b18eac244f3) |
| 🔴 P1 | B36 v2 角色预览空白 | StageC placeholder + hydrate 顺序 + 倒计时门控 | 待派 frontend |
| 🟡 P2 | B28 timeout 跳 /outline 错误页 | 改 timeout 错误页内容 + 不自动 fallback | 待派 frontend |
| 🟡 P2 | B27 stale backendStage 兜底 | hydrate 失败时 UI 兜底 + 后台进度替代 | 待派 frontend |
| 🟢 P3 | UX-2 LLM JSON 解析 fail | prompt 严格化 + 解析鲁棒 | 待派 backend (低优先) |

## 测试链路有效信号（B33+B34+干净重启全验证通过）

| 验证项 | 状态 |
|------|------|
| B33 user_selected_mood='热血' DB 持久化 | ✅ INSERT 真带值 |
| B33 LLM 注入约束 | ✅ `B33 user_selected_mood: 热血 (强制注入 LLM 约束)` |
| B33 outline.visual_tone.overall_mood='heroic' | ✅ DB verify |
| B33 confirm-outline 双轨 | ✅ OBS-4: user_selected_mood='热血' |
| B33 start_generation 透传 BGM | ✅ |
| B34 generate_outline commit-before-LLM | ✅ `B34: READ 事务已提交，释放 row lock` |
| B33 outline 编辑页无 mood section | ✅ Image #3 标题/简介/角色/情节/结局 5 区域，无情绪基调 |
| Alembic 003 head | ✅ |
| 1:1 画幅角色 portrait 生成 | ✅ 3 张 png（待 verify 1024×1024）|
| Stage 1 LLM 100s | ✅ B34 commit 真释放锁 |
| Stage 2-4 Pipeline 跑通 | ✅ Backend 真完成 (frontend 看不到) |
| Stage 5 NB2 图片 + Stage 6 BGM | ⏳ 等 ~15 分钟 backend 跑完 |

## 后续修复后回归测试方案

修完 B35 + B36 v2 + B28 + B27 后，应跑 test10:
- 同样参数 (1:1 + illustration + 热血 + 短篇) 看 frontend 是否丝滑
- 改 mood (浪漫 → Romantic 桶) 验证 BGM 桶切换
- 改画幅 (16:9) 验证 aspect_ratio 链路
