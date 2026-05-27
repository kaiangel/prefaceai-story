# test26 全维度地毯式回溯 (cyberpunk + ai_entity)

**测试**: 《深夜小七》cyberpunk + ai_entity (老周 human / 陈明 human / 小七 ai_entity 车载AI)
**时间**: 2026-05-24 17:36 项目创建 → 18:25:54 Pipeline 完成 → 21:14 (回溯时点)
**回溯方法**: 逐条 grep backend.log + frontend.log + client.log 全量 (17:01 重启 → 21:14), 不凭记忆
**回溯人**: PM (Founder 要求"毫无遗漏地毯式深度回溯")

---

## 一、Pipeline 时间线 (全程)

| 时刻 | 阶段 | 结果 |
|---|---|---|
| 17:36 | 项目创建 (duration 3min, 3 角色) | ✅ |
| 17:36-17:41 | Stage 1 大纲 + Stage 2 角色设计 (Claude 97.8s) | ✅ 3角色/7情节/4场景 |
| 17:41-17:44 | portrait + fullbody 生成 (char_001/002/003) | ✅ Layer 1 全注入 |
| 17:44:01 | R4-1 等待确认角色 | — |
| 17:50-17:57 | 陈明 2 次重新生成 (①换年龄 ②转写实) | ⚠️ 转写实失败 |
| 18:01:24 | ✅ 确认角色 (等待 420s) + B52-fix reload | ✅ |
| 18:01-18:04 | Stage 3 剧本 (Claude 168.7s, 21926 chars) | ✅ 7场景/24beats |
| 18:04-18:07 | Stage 4 分镜 (147.8s) | ✅ 24 镜头 |
| 18:08 | Stage 4.5 场景参考 (4 张) | ✅ |
| 18:08:35 | R4-3 等待确认场景 | — |
| 18:10:39 | ✅ 确认场景 (等待 50s) | ✅ |
| 18:10-18:23 | Stage 5 生成 24 shots | ✅ 24/24, ShotValidator 24 PASS/0 FAIL |
| 18:24-18:25 | Stage 6 BGM (Mureka + linter 2-pass) | ✅ |
| 18:25:54 | **Pipeline 完成** | ✅ |
| 21:00-21:03 | MySQL 2003 transient (看片后 2.5h, dashboard) | ⚠️ 自愈 |
| 21:14 | MySQL 恢复 (200 OK) | ✅ |

---

## 二、问题清单 (按严重度, 逐条证据)

### 🔴 P1-1: cyberpunk 画风混搭 (内测前必修)
- **现象**: 老周写实照片 / 陈明日系动漫 / 小七场景 — 同故事 3 角色画风不统一
- **根因**: `style_enforcer.py` cyberpunk 缺 forbidden_keywords 的 anti-anime 条目 (对比 vintage_film L361 有完整防护)
- **实测加剧**: 手动 adjust 加 "photorealistic/去动漫" **无效** — Seedream 对"年轻男性+cyberpunk"有强动漫先验, prompt 关键词压不过
- **扩展**: 全 28 style 扫描发现 6 个非动漫画风缺防护 (cyberpunk/ink/watercolor/ukiyo_e/pixel/pastel_dream)
- **详见**: `STYLE_ANTI_ANIME_FORBIDDEN_GAP_2026-05-24.md`
- **状态**: PENDING TASK-STYLE-ANTI-ANIME-FORBIDDEN, 派 AI-ML, 内测前修 + Tester 复测

### 🟡 P2-1: ETA/progress stage 级粗粒度
- **现象**: ETA 30min 长时间不变 + progress 跳变 (6%→11%→65%→78%)
- **根因**: progress 只在 stage 边界更新, stage 内部 (角色/剧本/分镜耗时步骤) 冻结; 后端 ETA `_calculate_eta_with_progress(stage, progress)` 依赖这两个输入, 输入不变则 ETA 冻结
- **关键观察**: Stage 5 生图阶段 ETA **准** (按 shot 数 4/24→10/24 动态), 问题集中在 Stage 1-4
- **修法**: ① 前端 ETA 接 simulatedTimer 时间插值 (改动小) ② 后端 Stage 1-4 加 sub-progress (根治)
- **状态**: PENDING TASK-ETA-STAGE-LEVEL-GRANULARITY (P2)

### 🟡 P2-2: adjust API 同步阻塞 90s → 前端 loading 卡死 (新发现)
- **现象**: 陈明"重新生成"点击后**一直转圈**, 后端图 17:57 已生成完, 前端 UI loading 不解除
- **根因**: `/characters/char_002/adjust` API **同步阻塞** (17:55:36 调整文字 → 17:57:06 fullbody 完成, 90s 才返回 200)。前端 fetch 等这 90s, 期间 loading 转圈; POST adjust 出现 3 次 (疑前端超时重试)
- **影响**: 用户以为卡住 (实际后端在跑), 体验差。内测用户会困惑/重复点击
- **workaround**: 刷新页面 hydrate 显示新图
- **修法**: adjust 改异步 (返回 202 + 前端轮询 job 状态), 或前端 loading 加超时提示 "AI 重绘中约需 90s"
- **状态**: 🆕 待记 PENDING (P2)

### 🟢 P3-1: MySQL 2003 transient 中断 (本地开发固有风险)
- **现象**: 21:00:24 / 21:01:28 / 21:02:08 / 21:03:23 共 **4 次** GET /projects/ → 500, `(2003, Can't connect to MySQL server on 101.132.69.232)`
- **根因**: 网络层短暂连不上阿里云 MySQL (非 pool 死连接)。看完成片后隔 2.5h, 本机疑似睡眠唤醒/WiFi切换/IP变化 (出口 IP 140.99.222.167), 触发阿里云安全组白名单拦截
- **自愈**: 21:14 恢复 (pool_pre_ping 重建连接 + 网络恢复), backend (PID 52534) 全程没死
- **影响**: 仅本地开发, **生产 VPS 在阿里云内网不受影响**
- **状态**: 🆕 待记 PENDING — 若反复出现, 查阿里云 MySQL 安全组白名单 (Ben 领域)

### 🟢 P3-2: NETWORK_ERROR elapsed 计时异常 (前端轻微)
- **现象**: client.log 报 `NETWORK_ERROR 5792945ms (96min) / 1091782ms (18min) / 75023ms (1.25min)` — 一个 fetch 不可能 pending 96 分钟
- **根因**: 疑前端 apiFetch 的 elapsed 用了错误起始时间 (tab 后台挂起 2.5h 后累计), 或计时基准 bug
- **影响**: 仅日志数字误导, 不影响功能
- **状态**: 🆕 轻微, 可选修 (前端 elapsed 计时基准)

### 🟢 P3-3: 404 记成 error level (日志分级不一致, 轻微)
- **现象**: chapters/1/status 等 404 共 18 次 (确认前轮询), 其中 12 次在 client.log 记成 `level: error` 而非 routine warn
- **根因**: 前端部分 404 走 error 分支, 部分走 routine pre-confirm 分支, 分级不统一
- **影响**: 监控噪声 (我 Monitor 去噪时已处理 routine, 但 error level 的 404 仍会触发)
- **状态**: 🆕 轻微, 前端统一 404 分级

### 🟢 P3-4: Invalid HTTP request × 5 (良性外部探测)
- **现象**: uvicorn `WARNING: Invalid HTTP request received` × 5 (17:15 + 19:14 等)
- **根因**: 协议层畸形请求 (HTTPS 打 HTTP 端口 / 浏览器预连接 / 端口探测), uvicorn 拒绝, 无 method 记录
- **影响**: 无 (uvicorn 拒绝畸形请求不崩)
- **状态**: 良性, 不需处理

### 🟢 P3-5: Failed to find Server Action "x" (Next.js dev 热重载, 轻微)
- **现象**: frontend.log 1 次 `Error: Failed to find Server Action "x"`
- **根因**: Next.js dev 热重载导致 server action ID 不匹配 (开发环境固有)
- **影响**: 仅 dev, 生产 build 不出现
- **状态**: 良性, 不需处理

---

## 三、正常工作的兜底机制 (健康信号, 非问题)

| 机制 | 触发次数 | 结果 |
|---|---|---|
| IncompleteRead 重试 #1 | 6 | 全自愈 |
| IncompleteRead 重试 #2 | 1 | 自愈 (#3+ = 0, 无彻底失败) |
| LLMFallbackChain (adjust via Haiku) | 8 | 全 SUCCESS |
| BGM duration linter 2-pass + fallback | 2 | 用第1次输出, 不阻塞 |
| ShotValidator 视觉验证 | 24 PASS / 0 FAIL | 零失败 |
| B52-fix v3 reload (确认后从DB重载角色) | 1 | 生效 (用陈明调整版) |
| pool_pre_ping 重建连接 (MySQL 2003 后) | — | 自愈 |
| 单模型 Seedream | 全程 0 切换 | 视觉统一性纪律守住 |
| CONTENT_SAFETY 拒绝 | 0 | 无内容安全拦截 |
| Gemini→Claude fallback | 0 | 角色/剧本/分镜直接用 Claude, 无需 fallback |

**结论**: 兜底体系全程正常工作 (DEC-051 红线保护的 fallback/retry 实战验证有效)。

---

## 四、误报澄清

- **MySQL 2013**: `grep 2013` 匹配的是 SQLAlchemy `[cached since 2013s ago]` 字符串 (SQL 缓存时长), **非 MySQL 2013 错误码**。实际**无 lost connection during query 错误**。

---

## 五、核心验证成果

- **Layer 1 三路统一 ABC 四象限齐**: manga-human(test22) + ink-mythological(test27) + illustration-supernatural(test25) + **cyberpunk-ai_entity(test26)** ✅
- 小七 ai_entity 全程 Layer 1 wire (portrait + fullbody + 24 shots) ✅
- Pipeline Stage 1-6 完整闭环 ✅
- 24/24 shots + BGM, ShotValidator 0 FAIL ✅

---

## 六、待办汇总 (进 PENDING)

| 编号 | 优先级 | 任务 | 负责 | 时机 |
|---|---|---|---|---|
| P1-1 | 🔴 P1 | cyberpunk 等 6 style 补 anti-anime forbidden | AI-ML + Tester | 内测前 |
| P2-1 | 🟡 P2 | ETA/progress Stage 1-4 粒度 | Frontend + Backend | 内测前后 |
| P2-2 | 🟡 P2 | adjust API 异步化 / loading 超时提示 | Backend + Frontend | 内测前 (用户会困惑) |
| P3-1 | 🟢 P3 | MySQL 2003 安全组白名单 (若反复) | Ben | 观察 |
| P3-2 | 🟢 P3 | NETWORK_ERROR elapsed 计时 | Frontend | 可选 |
| P3-3 | 🟢 P3 | 404 日志分级统一 | Frontend | 可选 |
| P3-4/5 | 🟢 | Invalid HTTP / Server Action x | — | 良性不处理 |
