# 待处理交接事项

> 所有 Agent 开工前必查，完成后删除对应条目
> **⚠️ 文档更新协议**: 共享文档由PM统一更新，详见 `.team-brain/TEAM_PROTOCOL.md`

---

## ✅ P1 followup — Backend scene_ref thumbnail URL wire (代码层完成, 已部署 5/28 ~19:21, commit SHA = 20f5b61(Backend)/1450dde(AI-ML)/1b69862(Frontend)/884b6b6(Docs))

**PM 5/28 17:55 地毯式重审 Ben 维度发现** — scene_ref thumbnail 物理落盘了但 API 链路没接通:
- ✅ `pipeline_orchestrator.py:L1004` scene_ref `_thumb.webp` 真生成
- ❌ `scene_reference_manager.py` 数据结构 0 个 thumb 字段
- ❌ `chapters.py` scene-references endpoint L3471-3549 只返 `interior_url + exterior_url`, **0 thumb URL**
- ❌ `chapter.scene_references_json` L3743 写入不含 thumb URL

**结果**: Frontend 拿不到 scene_ref thumb URL, scene_ref 体感优化没真闭环 (与 shot 路径 `image_url_thumb` 写 storyboard_json 不对称)。Frontend agent 已加注释 "无 thumbnail 字段所以不做 progressive", 已知限制, 用 prefetch 兜底。

**派活 Backend Sonnet 4.6 high (~20 min, DevOps 部署前同批做)**:
- `scene_reference_manager.py`: SceneAnchor 数据结构加 `interior_url_thumb` + `exterior_url_thumb` 字段
- `pipeline_orchestrator.py:L1010` thumb 落盘后写 `anchor_data['thumb_url']` 到 in-memory 数据
- `chapters.py:L3471-3549 + L3743` scene-references endpoint + scene_references_json 写入 同步增 `interior_url_thumb` + `exterior_url_thumb`
- `frontend/src/components/create/StageC.tsx:SceneRefsPreview` 拿到字段后加 progressive enhancement (镜像 StageD L40-110 模式)

**Ben 维度**: ✓ 数据流字段对称问题, 不涉契约 (在 chapter.scene_references_json 内), 不需 Alembic 迁移, 不涉公网内网

---

## ✅ 性能 P0 + Portrait 重生 P1 + Plan A++ progressive enhancement — 已部署 5/28 ~19:21, commit SHA = 20f5b61(Backend)/1450dde(AI-ML)/1b69862(Frontend)/884b6b6(Docs)

**3 个 agent 并行完工, PM 地毯式审查通过, 集成验证全过**:

| Agent | 状态 | 改动 | 测试 |
|---|---|---|---|
| **Backend** (Sonnet 4.6 high, Opus 4.7 重派) | ✅ 5 项 (#5/#8/#9/#10/#13) | projects.py L1025+L1852 / pipeline_orchestrator L997+L1395+L1659+L1670+L1714 / 无 Alembic | pytest 205 PASS / 0 退化 |
| **AI-ML** (Sonnet 4.6 high) | ✅ 2 项 (#6 CFP-3 + #7 GROUP COMPOSITION) | storyboard_prompts L1678 + reference_image_manager L354-369 | PM 跑 pytest 22 PASS / 0 退化 (沙箱限制 AI-ML 自己跑不了) |
| **Frontend** (Sonnet 4.6 high) | ✅ 6 项 (Shot type + StageD prefetch + SceneRefs prefetch + fixImageUrl workaround + **Plan A++ progressive** + vitest 5 新 case) | types/create.ts L106 + CreateContent L983 + StageC L394+L378+L2180 + StageD L53-67 + **StageD progressive useEffect L63-108** + StageD.progressive.test.ts (新) | vitest **20/20** PASS + build 0 errors |

**PM 审查 12 维度全 PASS**: 完整调用链路验证 (函数定义→调用点→参数传递→数据流向→消费点) + 越权零 + 文档更新基本到位 (AI-ML progress 三件套沙箱限制 PM 代补完成, Backend completed 补完, Frontend 三件套自动更新, TEAM_CHAT 各方追加完成)。

**待 DevOps 部署 (无 Alembic 迁移, 纯代码)**:
- commit + push GitHub (按 commit message scope 分批: Backend / AI-ML / Frontend / 文档 4 组)
- rsync app/ + frontend/ 到 VPS
- VPS docker compose rebuild api + frontend (有前端代码 + storyboard_json 字段改动)
- 验证: portrait 重生 dry-run refs=1 / shot 落盘三件套 (png + webp + thumb.webp) / 前端 preview 页 thumb 秒切 / regenerate-portrait 萤火群保留群体性

**P2 内测后排期**:
- CDN 国内化 (阿里云 / 腾讯云 + ICP 备案, 等 Ben 讨论)
- ShotValidator chars 群体角色 false positive 优化 (DEC-053 延伸)
- ShotValidator 复杂 prop 描述拆分 (Stage 4 prompt 工程)

---

## (历史) 🚨 性能 P0 + P1 修复批次 (5/28 test30 实测暴露, Founder 批"P0 和 2 个 P1 都要做")

**触发**: VPS 真机 e2e 跑通后, Founder 点 preview 页"下一张" shot_02 加载**10-20s**, shot_03 同样慢, scenes 页 scene_ref 也慢。**用户体验崩溃, 内测前必修**。

**铁证 (curl 实测)**:
```
shot_02.png 真实大小: 2,846,627 bytes (2.85 MB)
Cloudflare 已缓存:    cf-cache-status: HIT, age=1171s
但下载耗时:            total=20.04s (HIT 也 20s)
有效带宽:              ~142 KB/s
TLS appconnect:       2.23s
starttransfer (TTFB): 2.90s
```

**真根因 (5 维度)**:
1. **图大**: Seedream 输出 1664×2218 PNG ~2-3MB, 20 张 shot 总 60MB / 5 张 scene_ref 总 10-15MB
2. **跨海带宽**: Founder 国内 → Cloudflare NRT(东京)边缘 → VPS 国外 = 142KB/s (跨海路由 + 丢包 + 单连接限速)
3. **不是 CDN miss**: cf-cache-status=HIT 也慢, **纯 last-mile 带宽问题**
4. **本地秒切原因**: localhost 直连 + 无 SSL + Next.js dev 内存 cache, 不是性能优化, 是环境差异
5. **场景参考图同病**: scene_ref 也是大 PNG, scenes 页加载同样慢

**Ben 维度**: ✓ CDN 选型 + 大图压缩属 backend/infra 域, 建议 Founder **微信通知 Ben** 一起讨论长期方案 (国内 CDN / 备案 / 图片压缩 pipeline)。Founder 决策本批 P0 + P1 由 PM 派活做, CDN 国内化 (P2) 等 Ben 讨论。

**修复 (三层叠加, 派活清单)**:

### 🚨 P0 #1 — Backend 生成 thumbnail (Sonnet 4.6 high, 1h)
- **文件**: `app/services/pipeline_orchestrator.py` (Stage 5 shot 保存后) + `app/services/seedream_generator.py` (输出 hook) + `app/services/scene_reference_manager.py` (Stage 4.5 同步加)
- **实现**: shot 落盘后立即生成 webp thumbnail (~300KB, 832×1109 半分辨率, quality=80)
  ```python
  from PIL import Image
  shot_pil = Image.open(shot_path)
  thumb_size = (832, 1109)
  shot_pil.thumbnail(thumb_size, Image.Resampling.LANCZOS)
  thumb_path = shot_path.replace(".png", "_thumb.webp")
  shot_pil.save(thumb_path, "WEBP", quality=80, method=6)
  ```
- **DB schema**: `chapter_scene_images` 加 `thumbnail_url` 字段 (Alembic 迁移, 已知字段名: `thumbnail_path`)
- **storyboard_json**: 同时写 `image_url_thumb` 字段供前端读
- **预期效果**: thumb ~300KB / 142KB/s = ~2s 切完, **10x 提升**

### 🚨 P0 #2 — Scene refs 也生成 thumbnail (与 #1 同批, +30 min)
- **文件**: `app/services/scene_reference_manager.py` Stage 4.5 anchor 生成后同样跑 webp thumb
- **前端**: scenes 页 (`frontend/src/components/create/StageBScenes.tsx` 或类似) 同样优先显示 thumb

### 🟡 P1 #3 — Frontend 预加载相邻 shots/scenes (Sonnet 4.6 high, 30 min)
- **文件**: `frontend/src/components/create/StageD.tsx` + scenes 确认页
- **实现**: useEffect 在 currentIndex 变化时悄悄预拉前后 ±2 张
  ```tsx
  useEffect(() => {
    const preload = [currentIndex-2, currentIndex-1, currentIndex+1, currentIndex+2]
      .filter(i => i >= 0 && i < shots.length);
    preload.forEach(i => {
      const url = shots[i]?.imageUrlThumb || shots[i]?.imageUrl;
      if (url) { const img = new Image(); img.src = toAbsoluteUrl(url)!; }
    });
  }, [currentIndex, shots]);
  ```
- **效果**: 切换前已预拉, 体感秒切

### 🟡 P1 #4 — Backend WebP/AVIF 全分辨率压缩 (Sonnet 4.6 high, 1h)
- **文件**: `app/services/seedream_generator.py` 输出保存
- **实现**: PNG 保存外**同时**输出 WebP 全分辨率版本 (quality=85, 约 600KB-1MB), storyboard_json `image_url` 优先返 .webp
- **效果**: 即使用户点放大看原图, 600KB / 142KB/s = ~4s, 比 PNG 2.85MB 20s 快 5x

### 🔵 P2 #5 — CDN 国内化 (等 Ben 讨论, 内测后)
- 替换 Cloudflare → 阿里云 CDN / 腾讯云 CDN / Cloudflare China (后者需付费 + 备案)
- ICP 备案 + 国内 DNS 解析 (~1-2 day + 备案时间)
- Founder 决定时机, 不阻塞内测启动

**派活 (Founder 批准后立即开干, 估总 ~3.5h commit + 部署)**:
| 派 | 任务 | Model | Effort |
|---|---|---|---|
| Backend | #1 + #2 thumbnail + #4 WebP (一并部署) | Sonnet 4.6 | high |
| Frontend | #3 预加载 (StageD + scenes 两处) | Sonnet 4.6 | high |
| Tester | 回归测试: thumbnail 生成 + 预加载 + WebP 输出 + 旧项目兼容 | Sonnet 4.6 | high |
| DevOps | rsync app/ + frontend rebuild + VPS docker rebuild api + Alembic 迁移 thumbnail_path 列 | Sonnet 4.6 | high |

**关联**: DEC-055 (dev/prod parity), `analysis/TEST30_FULL_RETROSPECTIVE_2026-05-28.md` 批次 3 详细深挖。

---

## 🟡 Portrait 重生 + AdjustCharacter LLM 修复批次 (5/28 test30 Explore very-thorough 深审)

**触发**: test30《灯笼与萤火》Founder 改萤火群"黄绿→蓝绿" Adjust 后, 新 portrait 变**单只**萤火虫 (原本群体). Explore agent 5 维度地毯式审查 (前端 UI / 后端 endpoint / LLM prompt / TEAM_CHAT 历史 / Seedream API) 给出真根因 + 4 项修复.

**真根因诊断 (不是 dev/prod parity)**:
- 本地 vs VPS `app/api/projects.py` MD5 完全一致 (`33bc80fd8e3214c4143917d7dfcbe205`), **不是部署差异**
- Adjust endpoint (L1557) **真传** `portrait_ref=_existing_portrait_pil`, VPS log `refs=1` 实证
- 单只问题是 **多层协作产物**:
  1. **AdjustCharacter Haiku LLM** 改写 description 太狠, 把"一群" 数量 token 削弱 (prompt 缺保留数量约束)
  2. **Seedream prompt token 强度 > 单张 portrait_ref 权重**: portrait_ref 锁脸/identity 但不锁群体构图
  3. **代码缺陷副线** (但非本次根因): Regenerate-portrait endpoint (L1852) **没传** portrait_ref, 两 endpoint 行为分裂 (Wave 13 #6 异步化迁移漏修)

**4 项修复 (按优先级)**:

### 🔴 #1 P0 — Regenerate-portrait endpoint 补 portrait_ref wire (Backend, ~15 min)
- **位置**: `app/api/projects.py:1852 _regenerate_portrait_core`
- **问题**: 调用 `_ref_manager.generate_character_reference()` 缺 `portrait_ref` 参数, 与 L1557 Adjust endpoint 行为不一致
- **历史**: Wave 11.1 (5/14) T17-9 P0 修复在 Adjust 端补了 portrait_ref; Wave 13 #6 (5/25) Regenerate 异步化迁移**漏了**这条 wire
- **修复**: 镜像 L1545-1562 模式, 读 existing_portrait_path → PIL.open → 传 portrait_ref=_existing_portrait_pil
- **派**: Backend (Sonnet 4.6 high), commit + rsync app/ + docker rebuild api

### 🟡 #2 P1 — AdjustCharacter LLM prompt 补"保留数量"约束 (AI-ML, ~30 min)
- **位置**: `app/api/projects.py:1390-1426` 附近 (`_adjust_character_core` 的 LLM prompt 构建)
- **问题**: prompt 没显式约束 "保留原 description 中的数量修饰 (群/swarm/multiple/group/herd)"
- **修复 (示例 rule)**:
  ```
  RULE CFP-3 (新增): PRESERVE NUMERICAL CONTEXT
  If 原 description 含 "一群/swarm/multiple/group/herd" 且用户调整指令未明确改数量,
  必须保留原数量修饰. 例:
    原 "一群黄绿色萤火虫" + 调整 "改蓝绿" → "一群蓝绿色萤火虫" ✅ NOT "一只蓝绿色萤火虫" ❌
  ```
- **派**: AI-ML (Opus default), 改 prompt + dry-run 萤火群场景验证 + commit

### 🟡 #3 P1 — Seedream prompt 加强群体 token (AI-ML, ~20 min)
- **位置**: `app/services/reference_image_manager.py:265 _build_portrait_prompt`
- **问题**: 当 character 含 swarm/group 时, prompt 没显式强化 "swarm of dozens"/"a swarm of fireflies, multiple insects in flight"
- **修复**: portrait_prompt builder 检测 description/name 含群体 keyword → 自动 prefix "a swarm of N+ ___, multiple subjects in flight, group composition" 强化 token 权重
- **派**: AI-ML 与 #2 一起做, 同一 commit

### 🔵 #4 P2 — 前端 UI 加"微调 vs 完全重画" 双模式 (Frontend, 本期不做)
- **位置**: `frontend/src/components/create/StageC.tsx:1554-1616`
- **问题**: 当前"调整" + "重新生成"双按钮但用户看不出 portrait_ref 是否传, 设计意图不明
- **修复**: 改成"微调 (传旧 portrait 锁脸 + 改局部)" vs "完全重画 (纯文生图)" 双模式 checkbox, 用户可选
- **派**: Frontend, 本期内测后再做

**当下决策**:
- test30《灯笼与萤火》Pipeline **不中断, 让它跑完看 e2e** (萤火群单只跟下去, shot 阶段可能 cascade 单只, 但完整 e2e 比单角色完美更值得验证)
- #1 P0 修完后立即 patch 部署, **不影响本次 e2e** (e2e 跑完才修, 修复后下一轮 e2e 再验)
- 视觉验证: 若 #1+#2+#3 修完后改萤火群仍单只 → 锁 Seedream API 本身权重限制 → 走 #4 用户选择方案

**Ben 维度核查**: ✅ 全 backend/prompt 工程域, 不涉前后端契约/共享 DB/公网内网/DB-infra, Founder 不通知 Ben.

**关联**: DEC-055 (dev/prod parity) — 本批不是 parity 问题, 是产品功能 bug. memory `feedback_portrait_regen_dual_endpoint_inconsistency` (新增, PM 教训: 两 endpoint 异步化迁移时必须 cross-check 全部参数传递).

---

## ✅ Dev/Prod Parity 全维度根治批次 (5/28, 4 处 P0 全闭环) → DEC-055 + SOP

**主因**: PM 之前 dev/prod parity 工作只盯 DB 栈 (DEC-054), 没扫 **.env keys / Nginx 路由 / 静态文件 serving 链路**。VPS test30 接连暴露 4 只哑雷, Founder 严厉提醒"全维度毫无遗漏要本地一致或对齐"。今晚 PM 派 Explore agent very-thorough 11 维度 audit + 全部修复。

**已闭环 (按时间顺序)**:

### ✅ P0-2 SKIP_IMAGE_GENERATION=true 误开 (5/28 06:20 修)
- **现象**: test30《灯笼与萤火》/characters 三个角色图全失败, Pipeline `generate_images=True` 但 0 portrait/0 shot
- **根因**: VPS `.env.production` L40 显式 `SKIP_IMAGE_GENERATION=true` 覆盖 config.py L54 默认 False, gate `if generate_images and not settings.SKIP_IMAGE_GENERATION` 评估 False 整个 portrait 块 silent skip
- **PM 自查盲区**: test29 后看到 VPS 仅 1 output 目录归因 "local-origin", 没追 "为什么 36 项目只 1 个有图" → 那时该挖到 SKIP 模式
- **修复**: sed true→false + 备份 + `docker compose up -d --force-recreate api`

### ✅ P0-3 ARK_API_KEY 完全缺失 (5/28 06:45 修)
- **现象**: SKIP 修后 Pipeline 进 portrait 块, Layer 1 inject + Seedream dispatch 都进, 但 3 张全 WARNING `ARK_API_KEY not set` fail
- **根因**: VPS `.env.production` **从未配过** `ARK_API_KEY` (火山方舟 Seedream key), 只有 TTS 用的 `VOLCENGINE_*`。本地 `.env` 有, 但 dev/prod parity 工作没扫 API keys, ARK 缺一直被 SKIP=true 掩盖
- **修复**: 本地 cat .env → ssh stdin → append 3 行 (ARK_API_KEY + IMAGE_GEN_PROVIDER + PROMPT_FORMAT) + force-recreate api
- **真调实证**: 容器内 Python 调 Seedream API HTTP 400 InvalidParameter (size 太小) — 鉴权层通过, ARK_API_KEY 真有效

### ✅ P0-4 IMAGE_GEN_PROVIDER + PROMPT_FORMAT parity 显式化 (5/28 06:45 修, 与 P0-3 同批)
- **gap**: VPS `.env.production` 缺这 2 项 (config.py 兜底默认值能 work 但 parity 红线破)
- **修复**: append `IMAGE_GEN_PROVIDER=seedream` / `PROMPT_FORMAT=b_prime` 与 ARK 同次操作

### ✅ P0-5 Nginx 配置缺 `location /static/` proxy (5/28 07:12 Founder sudo 修)
- **现象**: 3 张 portrait 真落盘 (容器内 ls 2-3MB png 真在), 容器内 curl `localhost:8000/static/outputs/...` = 200, 但外部 `https://prefaceai.mov/static/...` = 404 len=27683 (Next.js 错误页 HTML)
- **根因**: VPS host Nginx `prefaceai-mov` 配置只有 `location /api/` + `location /` + `location /_next/static/`, **缺 `location /static/`** → `/static/*` 请求落到 default `location /` 转给 Next.js, Next.js 不识别返 404 HTML
- **为什么 test29 没暴露**: test29 是 Founder 在**本地**测的 e2e, 走 localhost:8000 + uvicorn 直 serve 静态; VPS 一直 SKIP=true 没真生过图, `/static/*` Nginx serving 链路从未被验证过
- **修复**: PM 写新配置到 `/tmp/prefaceai-mov.new` (加 `location /static/ → 127.0.0.1:8000`) → Founder `su -` 切 root → `cp /tmp/prefaceai-mov.new /etc/nginx/sites-enabled/prefaceai-mov` + `nginx -t` (syntax OK) + `systemctl reload nginx`
- **真验实证**: 3 张 portrait `curl -I` 全部 HTTP 200 + Content-Type: image/png

**Ben 维度核查 (4 处全过)**:
- P0-2/P0-3/P0-4: 不涉前后端契约/共享 DB/公网内网/DB-infra (纯 backend env config), Founder 决策暂不通知 Ben
- P0-5: host Nginx 反向代理 (基础设施层偏 Ben 域), Founder 决定 sudo 自己改, Ben 暂不通知

**当下 Pipeline 状态 (5/28 07:15)**:
- 项目 943a4f2d (test30《灯笼与萤火》, ink, 3min) 在 R4-1 等用户确认角色 (~960s/1800s)
- 3 张 portrait 已 200 image/png 真出图, fullbody/scene refs 未生 (R4-1 之后才跑)
- Founder 即将刷新 characters 页 → 看图 → 点"确认角色继续" → Pipeline 进 Stage 3+4+5+BGM+shot 生成

**永不再犯保障**:
- DEC-055 锁 Canonical Dev/Prod Parity 11 维度审计标准 (代码/依赖/DB 栈/.env/Nginx/Docker/静态挂载/启动方式/端口/权限/build-time env)
- **新 deploy SOP** `.team-brain/sops/DEPLOY_PARITY_CHECK.md` 部署前强制 11 维度 checklist, DevOps 必跑通才能上

---

## ✅ P0-1 已根治+部署 — VPS DB ping bug + dev/prod parity (5/27, DEC-054)

**完成**: 升 SQLAlchemy 2.0.50(commit 8cabaec) → VPS rebuild 部署(b219d00) → PM 独立核实 ping TypeError 120/30min→**0** + /api/projects 401(不再500) + 容器 SA2.0.50/asyncmy0.2.11/pymysql1.1.2 + 本地对齐镜像同栈。Canonical DB 栈见 DEC-054。Founder VPS 测试解封。剩: Founder 带 auth 真机抽测登录/工作台真体验确认。

---

## ✅ P0 已根治+部署 — VPS DB ping bug + dev/prod parity (5/27, DEC-054)

**完成**: 升 SQLAlchemy 2.0.50(commit 8cabaec) → VPS rebuild 部署(b219d00) → PM 独立核实 ping TypeError 120/30min→**0** + /api/projects 401(不再500) + 容器 SA2.0.50/asyncmy0.2.11/pymysql1.1.2 + 本地对齐镜像同栈。Canonical DB 栈见 DEC-054。Founder VPS 测试解封。剩: Founder 带 auth 真机抽测登录/工作台真体验确认。

<details><summary>(历史) 原派活记录</summary>

## 🔴 P0 派活中 — VPS DB ping bug 根治(#2) + dev/prod parity(#3) (5/27, Ben已批)

**现象**: VPS prefaceai.mov 登录+工作台(GET /api/projects/)间歇 500, `TypeError: AsyncAdapt_asyncmy_connection.ping() missing 1 required positional argument: 'reconnect'`。Founder VPS 真机测试时炸出。

**真根因(Backend 真阿里云MySQL实证矩阵定案)**: SQLAlchemy 2.0.36 `do_ping`(pymysql.py:105 `_send_false_to_ping` inspect PyMySQL同步ping签名) + **PyMySQL 1.2.0**(VPS, ping默认 reconnect=False)→ 调无参 `ping()` → async适配器 ping(self,reconnect) 无默认 → TypeError。**真凶=PyMySQL版本非async驱动**(asyncmy/aiomysql 同病)。本地安全仅因 PyMySQL 1.1.2。SQLAlchemy官方#13306, 2.0.50修。矩阵: A(SA2.0.36+PyMySQL1.1.2)PASS / B(SA2.0.36+1.2.0)TypeError / C(SA2.0.50+1.2.0)PASS。
**3次诊断纠偏**: ①升asyncmy0.2.11→实测不修 ②换aiomysql→实测同样崩 ③真修=SQLAlchemy≥2.0.50。

**派活(Ben批2+3, 驱动方向=asyncmy尊重Ben既有选择)**:
- 🔴 **#2 P0修复 [Backend]**: `requirements.txt` `sqlalchemy==2.0.36`→`==2.0.50`。修ping bug(两驱动两pymysql都修)。
- 🟡 **#3 dev/prod parity [Backend+DevOps+PM]**: pin `pymysql`精确版本 + 统一async驱动 asyncmy(bump 0.2.10→0.2.11 修_auth_plugin_name) + **对齐本地到asyncmy**(本地现跑aiomysql+pymysql1.1.2=分裂源) + 文档化标准DB栈。让本地真镜像VPS, 根治"本地测不出VPS bug"。
- **执行链**: Backend改requirements+跑回归(确认SA小版本升级0退化) → PM对齐本地(切asyncmy+reinstall+重启standby) → DevOps VPS rebuild+部署+验证(ping bug消失) → PM审查。
- **Ben**: 已批; 阿里云零操作(纯客户端依赖版本)。
- 详见 task #10。

</details>

---

## 🔵 Ben 域安全跟进(P3, 与P0解耦, 内测后): 收紧 root@% 公网账号

Backend 诊断 P0 时实查发现: 阿里云 ECS 自建 MySQL 8.0.35 连接账号 `root@%`(公网通配 + mysql_native_password + 不强制SSL)偏裸奔。建议 Ben(DB域)评估: 建最小权限 app 专用账号 + 限内网/IP白名单 + 评估 SSL。非阻塞, 内测后 Ben 排期。

---

## ✅ test29 非人类专项 + Packet retry — 已修复+审查+部署 (5/26, Founder B 方案) + 剩余持久待办

来源: test29《荷塘渡》e2e (90分) 全维度回溯 `analysis/TEST29_FULL_RETROSPECTIVE_2026-05-26.md` + DEC-053。**核心主题: 数据层 Stage 2 已通用化, 消费层全人类中心**。

**已闭环 (commit 81b5d25, 三方+VPS容器对齐, PM 独立 grep 容器验证真活)**:
- ✅ **#4** Packet sequence — db_retry.py:58 加认 "packet sequence number wrong" + main.py:75 wire (容器实证)
- ✅ **#5** 非人类 type builder + **#5a 锚点层** (identity_anchor_prompts 各非人类 type 列真实色字段 scale_color/leaf_color 等; character_prompt_builder physical fallback)
- ✅ **#7** 多角色 shot 强制分离 (identity_anchor_injector:262 MULTI-SUBJECT SEPARATION) + 自然度检查不洗白融合
- ✅ **#6** ShotValidator 计数通用化 (humans AND non-human)

**剩余持久待办 (跨 session 不丢, agent 开工必查)**:
- 🟡 **#8 [AI-ML, 内测前(Founder 5/27 升级: BGM 用户直接听得到), 派活中]**: BGM 提取器无人类时 `character_dominant_type` 默认 'human' + watercolor 误归 western_realistic。BGM 现状可用(test29 贴合), 增量打磨非救火。**方向已定=路径 B(DEC-053, 别走 A)**: BGM 主吃 universal 信号(mood+setting_period+题材+节奏)+增强 setting_period 文化识别(荷塘/锦鲤=中式被判 generic 是真漏点); character_dominant_type(4桶 vs 19type)&style_category 降软提示+fallback。**禁**给 19type×95style 堆专属规则(无底洞)。依据: test29 character_dominant_type 判错但 BGM 仍贴合→弱信号→深度通用性反指向简化。约 1-2 天代码+一轮跨组合听感测试(主成本, 无法 unit test)。[task #8 + DEC-053]
- ✅ **#9 [完成 5/27]**: `docker-compose.yml` 残留 mysql service 定义已删 — Ben 微信确认可删 → DevOps commit 83a576b + VPS scp 同步 → PM 独立核实 0 mysql + 无悬空引用 + 容器 api/frontend/redis 健康。
- 🔄 **#8 [审查通过, 待部署 5/27]**: BGM 路径B (story_music_extractor.py 文化识别 universal 信号 + character_type 降软提示不默认 human)。PM 审查通过 (395 pytest + dry-run 荷塘渡→chinese_traditional)。**代码在工作区待 DevOps commit+部署 (rsync app/+rebuild api)**, #8 内测前。真听感待 Founder e2e。[task #8 + DEC-053]
- 🟡 **残留验证 gap [低风险, 可关闭]**: `projects` 3 列 (aspect_ratio/raw_outline_json/confirmed_outline_json) 未能独立 SHOW COLUMNS 核实 (生产凭据分类器拦 DB 查询=安全机制正确)。间接佐证强: alembic `006_t21new7_scene_refs (head)` 直接命令输出 + 后端 status 端点正常读 project 字段不报错。下次有 DB 直连机会时补直接证据。
- 📌 **#5/#7 视觉真证 [Founder B 决定不阻塞]**: 代码已上生产, 但"金色真出金色/鱼草不融合/人类故事不退化"待下轮 e2e 或自然使用浮现。若未生效 = 新一轮 finding。
- 📌 **结局 uncast 人类旁观者 [内测后评估]**: 结局 shot 出现剧本未设定的撑船老人+第三人称旁白, 疑 by-design 叙事框架。

**说明**: Wave13+test29 已全部 commit+部署 (81b5d25), 不再"禁 commit"。#5/#7 碰高风险文件 (identity_anchor_injector) 单测已绿 (db_retry 21 + AI-ML 域 499), 视觉真证待 e2e。

---

## 🟢 Wave 13 内测前 FIXBATCH — PM 审查通过, 待 Tester + DevOps (5/25, DEC-052)

代码全部写完仍在工作区未 commit (HEAD=68e4211=Wave12)。**PM 地毯式审查全绿无 blocker** (5+1 Ben 协议 + 完整调用栈):
- Backend #5d (MySQL retry middleware) + #6 (regenerate-portrait 异步) + #5e (clothing 旁路防崩) ✅
- Frontend #4A/#4B (确认流程 UX) + #5 (404 真根因) + #6 (reroll 异步轮询) + #9 (vitest 基建) ✅
- AI-ML #5b (schema 5 type 核实, 0 代码改动) ✅
- 🔑 §9.7.4 regenerate-portrait 三方契约逐字段对齐 (Backend ⟺ Frontend ⟺ 契约 v1.6) ✅
- 详见 DECISIONS DEC-052 + INTERNAL_BETA_READINESS_CHECKLIST_2026-05-25.md 顶部

**下一步**:
1. ⏳ **Tester 第二道** (并行进行中): pytest 30 新 (db_retry 14 + clothing_bypass 12 + regenerate_async 4) + vitest 15 + 全量回归 0 退化 + 独立核对 §9.7.4 字段
2. ⏳ **DevOps Wave 2** (双绿后): commit 分组 (见下) + push GitHub + VPS 第 5 次部署。⚠️ layout.tsx 须 rebuild + 浏览器硬刷新 (root layout inline script HMR 不刷新)
3. 📌 **PM 待办**: 更新 memory `project_schema_humanoid_fallback_remaining` 状态 (physical 维度 Wave 8 已根治, 5 type 不会因 physical 崩 — #5b 核实结论)

**DevOps commit 分组建议** (commit message scope 教训, 覆盖完整范围):
- **commit 1 (Backend, frontend-impact API 变更)**: `app/middleware/db_retry.py`(新) + `app/main.py` + `app/database.py` + `app/api/projects.py` + `app/services/character_designer.py` + `tests/test_wave13_db_retry_middleware.py` + `tests/test_wave13_clothing_bypass.py` + `tests/test_wave13_regenerate_portrait_async.py`
  - msg 覆盖: #5d MySQL retry middleware + pool_recycle 600s / #6 regenerate-portrait 异步化 (202+job) / #5e clothing 旁路防崩 (非穿衣 type 降 warning) + prompt 指引
- **commit 2 (Frontend)**: `frontend/src/app/create/CreateContent.tsx` + `frontend/src/app/layout.tsx` + `frontend/src/components/create/StageC.tsx` + `frontend/src/hooks/useETA.test.ts` + `frontend/vitest.config.ts`(新) + `frontend/vitest.setup.ts`(新) + `frontend/package.json` + `frontend/package-lock.json`
  - msg 覆盖: #4A 确认流程 hydrate 超时守卫 / #4B 后台生成按钮 scenesConfirmed 守卫 / #5 404 分级真根因 (模板字符串吃反斜杠) / #6 reroll 异步轮询 / #9 vitest 基建
- **commit 3 (契约+文档)**: `.team-brain/contracts/STATUS_API_CONTRACT.md` (§9.7.4) + 各 progress 三件套 + PENDING/DECISIONS/checklist/TEAM_CHAT
  - ⚠️ VPS 部署须含 DB 新列 Alembic (#5c, projects 表 3 列) — 与之前部署一致确认

---

## 📊 Wave 11 收尾计划 (5/24 update)

### 阶段 1: 清 P3 代码 ✅ 全完成
- Step 1 ✅ **DEC-051 fallback 红线** — CLAUDE.md 15-A (commit 17b6e28)
- Step 2 ✅ **MySQL pool** (commit 3b8956b, no-op 诊断) — 本地 pool_pre_ping+pool_recycle=1800+pool_size=10 早在 Wave 4 已配。5/23 500 = VPS 部署滞后, 阶段 2 部署修复
- Step 3 ✅ **LP image LCP priority** (commit 648b81c) — Showcase.tsx 1 行精确匹配
### 阶段 2: 🟡 **TASK-WAVE-11-DEPLOY-VPS** — DevOps 第 3 次部署 (3 commit: 3faf585 AI-ML + 28e33a7 Backend + 648b81c Frontend, VPS c570c2d → 648b81c)
### 阶段 3: 🟡 test26 e2e (cyberpunk + ai_entity, ABC 收官) + Founder spot-check + 内测启动

### 🔴 P1 内测前必修 (5/24 test26 新发现)
- **TASK-STYLE-ANTI-ANIME-FORBIDDEN** — 6 个非动漫画风 style 缺 anti-anime forbidden_keywords → 画风分叉
  - 实证: test26 cyberpunk 老周(写实)/陈明(动漫) 同框割裂
  - 🔴 必修: cyberpunk / ink / watercolor / ukiyo_e + 🟡 pixel / pastel_dream / children_book
  - by-design 不动: cartoon/ghibli/manga/korean_webtoon/chibi/illustration (本身动漫插画类)
  - 根因: style_enforcer.py forbidden_keywords 缺 anti-anime (对比 vintage_film L361 有完整防护)
  - 修法: 给缺陷 style 补 forbidden (anime/cartoon/cel-shaded等), AI-ML 逐个甄别不可一刀切 (ink 不能禁 painting)
  - 派: AI-ML (style_enforcer.py) + Tester (test26/27 复测画风统一)
  - 时机: 内测启动**前** (内测用户不会手动调 prompt, 必须系统锁死)
  - 本次 workaround: Founder 手动在调整框加写实关键词 (已用)
  - 详见: `.team-brain/analysis/STYLE_ANTI_ANIME_FORBIDDEN_GAP_2026-05-24.md` (全28 style 扫描表)
- **TASK-ETA-STAGE-LEVEL-GRANULARITY** (P2, 5/24 test26 发现) — ETA 30min 不变 + progress 不动
  - 根因: progress 只在 stage 边界更新, stage 内部(画像/shots 生成耗时步骤)不更新 → 依赖 progress 的 ETA 冻住
  - 关键: Stage 5 生图 ETA 准(按 shot 动态), 问题集中 Stage 1-4
  - 修法: ① 前端 ETA 接 simulatedTimer 时间插值平滑递减 (改动小, 立竿见影) ② 后端 Stage 1-4 加 sub-progress (根治)
  - 派: Frontend (插值) + Backend (sub-progress)
- **TASK-ADJUST-API-ASYNC** (P2, 5/24 test26 发现, 内测前) — adjust API 同步阻塞 90s → 前端 loading 卡死
  - 现象: 陈明"重新生成"点击后一直转圈, 后端图已生成完前端 loading 不解除, POST adjust 出现 3 次(疑超时重试)
  - 根因: /characters/{id}/adjust 同步阻塞 (调整文字+重生 portrait+fullbody 共 90s 才返回 200)
  - 影响: 用户以为卡住/重复点击, 内测用户会困惑
  - 修法: adjust 改异步(返 202 + 前端轮询 job), 或前端 loading 加 "AI 重绘约需 90s" 超时提示
  - 派: Backend (异步化) + Frontend (loading 提示)

### 🟢 P3 观察/轻微 (5/24 test26 回溯发现, 详见 TEST26_FULL_RETROSPECTIVE_2026-05-24.md)
- **MySQL 2003 transient** — 本地连阿里云**已反复 2 轮**(21:00-21:03 + 22:21, 后者含 TimeoutError 连接超时)均自愈。坐实本机网络层到阿里云不稳(IP/网络抖动)。生产VPS内网不受影响。**已反复=不是偶发** → 升级: 查阿里云 MySQL 安全组白名单是否限本机 IP段 / 本机网络稳定性(Ben + Founder)
- **NETWORK_ERROR elapsed 计时异常** — 报 96min/18min 不合理, 疑前端 tab 后台挂起累计计时 bug (Frontend 可选修)
- **404 日志分级不一致** — chapters/1/status 等确认前 404 部分记 error 部分记 routine warn (Frontend 统一)
- **良性不处理**: Invalid HTTP request×5 (uvicorn 拒畸形请求) / Failed to find Server Action x (Next dev 热重载)
- **前端测试框架缺失** (Wave 12 审查发现) — 项目无 vitest/jest/jsdom 依赖, useETA.test.ts (pre-existing) 跑不起来。长期补前端单测基建 (P3, Frontend)
- **regenerate-portrait 未异步化** (Wave 12 Backend 提及) — adjust 已异步, 但 regenerate-portrait 端点仍同步 ~60s, 同类问题。同 pattern 可加 (P2, Backend, 内测前或后)
- **🔴🔴 [根因已修正] 每个确认环节切换前端 10-30s 才显示 — 性能核心 (P2→内测前必修, 5/25 test28 Founder 核心体感)**
  - ⚠️ **根因修正**: 之前"拉全列表 N+1"判断**错误已纠正**。实测真根因: 前端 hydrate 调**单项目** GET /projects/{uuid}, 但 ① **阿里云 MySQL 公网往返 333-684ms/次(TCP实测)** ② hydrate **并发5请求**(project+chapter status/story/storyboard/bgm) ③ chapter **大JSON字段**(storyboard 20shots) → 叠加 10-30s
  - **生产判断**: 本地连公网MySQL特有, **生产VPS内网(<1ms)大幅改善** — 内测前须在VPS实测确认生产速度, 不能用本地公网延迟判断
  - 方案: ①生产VPS内网(最大头) ②合并hydrate为聚合端点(减round-trip) ③chapter status不拉storyboard全文(大字段按需) ④连接池复用
  - 派: Backend(聚合端点+大字段按需) + DevOps(VPS实测生产速度)。详见 TEST28_FULL_RETROSPECTIVE_2026-05-25.md P2-1
- **404 分级 Frontend Wave B 修复实测未生效 (P3, 5/25 test28 深挖)** — layout.tsx L195 正则匹配 status/story/storyboard/bgm→routine-404, 但 test28 实测 0 routine-404 + 18 仍 network level。修复未生效(可能 api.ts 另一路径记 network)。教训: 代码审查通过≠实测生效。派 Frontend 复查+e2e验证
- **[历史误判,作废] 原 "characters/scenes 确认页 hydrate 拉全列表慢" 分析 (下条) — 根因已被上条修正, 保留供对照**
- **🔴 characters/scenes 确认页 hydrate 拉全列表慢 → 超时兜底页 (UX 回归, P2, 5/25 test28, Founder 重点指出)**
  - 现象 1: characters 确认页加载弹"AI 正在努力创作中 + 返回工作台"兜底页 (CreateContent.tsx L1149 setHydrateError + L1621-1656 兜底 UI)
  - 现象 2: 刷新后"正在加载你的故事"~30s 才出角色预览
  - 同根因: **characters 确认页 hydrate 调 GET /api/projects/ 拉全部 44 项目 + chapters JOIN**, 项目累积越多越慢 (>120s 超时弹兜底 / <120s 撑出 30s 慢)
  - **Founder 核心 UX 点**: 确认流程中(角色/场景未确认完, 后面还要确认场景)**不该出现"返回工作台"兜底页** — 会打断流程, 体验割裂。确认中超时应继续等待/重试, 保持流程内
  - **"之前都是好的"判断**: 最可能是项目累积(44测试项目)放大了一直存在的查询性能问题, 但**值得查的回归疑点**: characters 确认页为何拉「全列表」而非「当前单项目」GET /api/projects/{id} — 若某次改动引入全列表拉取 = 真回归点
  - 两层修法: ① 根治 characters 确认页只查当前项目不拉全列表 (Frontend hydrate + 可能 Backend 加单项目端点) ② UX: 确认流程中 hydrate 超时不给"返回工作台"兜底, 改"继续等待/重试" (Frontend CreateContent L1149/L1621)
  - 调查方向: git blame CreateContent hydrate 拉全列表的引入时间 + 对比之前确认页 hydrate 逻辑
  - 派: Frontend (确认页 hydrate 改单项目 + 兜底 UX) + Backend (查询优化, 若需单项目端点)。关联 DASHBOARD-PERF-N1
  - 本地 workaround: 清理累积测试项目可缓解 (但生产多用户同样会遇到, 必须根治)
- **"后台生成去做别的"按钮缺场景确认守卫 (UX, P2, 5/25 test28, Founder 指出)**
  - 现象: storyboard(Stage 4 分镜)阶段就显示"后台生成去做别的"按钮, 但场景(R4-3)还没确认 → 用户点了离开会卡在 R4-3 场景确认没人点(Pipeline 等 1800s 超时)
  - 设计意图(StageC.tsx L110): "user cannot leave until both characters AND scenes are confirmed"
  - 已部分修: 副标题文案 STAGE_SUBTITLE storyboard="AI 正在创作故事，请稍候"(不带"后台生成"字样, RISK-T15-1) + Stage 4.5 文案也不带(T21-NEW-7 v1.4)
  - 🔴 漏修: "后台生成去做别的"**按钮**(handleBackground StageC L951 跳 dashboard)的**显示守卫**没同步 — 文案隐藏了但按钮还显示
  - 修法: 后台生成按钮加 ui_phase/scenes_confirmed 守卫, 只在场景确认后阶段(image_generation/image_preparation/bgm/music)显示, 与 STAGE_SUBTITLE 文案逻辑一致
  - **更新 (Founder 二次指出)**: 实际是按钮"忽有忽无" — storyboard 有 → scene_image_preparation 没(已隐藏) → 场景确认后又有。用户看到按钮闪烁出现/消失 = **比单纯早显示更困惑**。根因: 各 stage 显示守卫不统一 (scene_preparation 隐藏对了 storyboard 漏隐藏)。修法统一: 确认前全程(story_generation/character_design/screenplay/storyboard/scene_image_preparation)隐藏, 场景确认后(image_generation/image_preparation/bgm/music)一致显示
  - 派: Frontend (StageC 按钮显示条件)
  - 关联: 与"确认流程超时不该给返回工作台兜底"同类 UX 原则 — 确认流程中(角色/场景未确认完)不让用户离开

### ✅ Wave 12 FIXBATCH 完成 (5/24, test26 回溯全部问题修复)
- P1 style 画风 (AI-ML): cyberpunk/pastel_dream/gothic 补 anti-anime forbidden[:8]+介质 mandatory[:5]; 实测校准 (pastel🔴/ink·watercolor·ukiyo_e🟢守住)
- P2-1 adjust 异步化 (Backend+Frontend): 202+job轮询, 三方契约对齐 STATUS_API_CONTRACT v1.6 §9.7, 修陈明转圈
- P2-2 ETA 粒度 (Backend sub-progress + Frontend 插值)
- P3 (Frontend): NETWORK_ERROR计时 + 404分级
- 三 agent 地毯式审查全通过 (含 Ben DEC-030 gap PM 代补)
- ⏳ 待: PM 重启 backend + Tester Wave C 跨style画风+adjust端到端复测 → 部署 VPS → 内测

### 长期 (非本计划)
- **单场景故事成片视觉单薄 — 大纲阶段是否引导多场景 (产品考量, 5/25 test28 Founder 提出)**
  - 现象: test28《午夜钟魂》idea 是密闭空间(古董行单场景), LLM 正确识别 1 物理场景, 但 20 shots 全在同一空间 → 视觉丰富度受限
  - 非 bug: Pipeline 忠实按 idea 生成。是 idea 设定 (单场景密闭剧) 的固有取舍
  - 产品考量: 内测用户写单场景 idea 时成片可能单薄。是否在 Stage 1 大纲/Stage 3 剧本阶段检测单场景 → 建议/引导用户加场景 (空间转换提升张力), 或提示"单场景故事"预期
  - 权衡: 单场景剧是合理叙事形式 (独幕剧/密闭惊悚), 不应强制多场景, 但可"提示+建议"非强制
  - 派: PM 产品决策 + 可能 AI-ML (大纲 prompt 引导多场景) — 内测后排期
- ShotValidator chars=N/M Seedream 反复 FAIL — 模型限制, 长期 prompt 迭代
- **ShotValidator 手部畸形判定阈值 — 决定【暂不修】(5/25 test28 Shot 19, Founder+PM 权衡裁决)**
  - 现象: Shot 19 多指/手指畸形, retry 第3次 ShotValidator(Haiku)判 PASS 但人眼看手仍畸形 (判 PASS ≠ 人眼无瑕疵)
  - **决策: 暂不收紧 ShotValidator (Founder 5/25 拍板, PM 同意)**
  - 理由 (核心非"难", 是副作用权衡): 手部畸形是 Seedream 高频问题, 若收紧严判"手指略畸形=FAIL" → 大量 shot 触发 retry(20张可能半数) → Pipeline 时间/成本翻倍 + 模型局限致 retry 后仍畸形 → 陷"判FAIL→retry→还FAIL"循环甚至卡住。**过度 retry 比漏判轻微瑕疵更糟**
  - 当前阈值合理: 抓"明显多手(3+hands)"FAIL + 放过"手指略不自然" = 抓大放小, 是成本-质量正确平衡点
  - 兜底策略: ① 用户层手动重生(按需, 成本可控) ✅ 正解 ② 长期靠 Seedream 模型进步 ③ 不靠验证器严判(全局 retry 成本失控)
  - 教训保留: 不能只信 ShotValidator PASS, 人眼复核仍必要 (手部=LLM 视觉盲区)
  - 重新评估触发: 若 Seedream 手部能力显著退化 / 用户大量反馈手部问题, 再议
- CLAUDE.md untracked — 待 Founder 决定是否 git add (本地生效不影响功能)

---

## 📊 (历史) 当前剩余 task (5/23 17:30 update)

### 🟡 等 Founder (2 项 spot-check + 决策)
- **L-3** 跑 test25 (manga + supernatural 银发狐妖) + test26 (cyberpunk + ai_entity 出租车 AI) e2e
  - 完成 ABC 完整跨题材覆盖 (test22 manga + test27 ink 已跑, 还差 test25+26)
  - Founder 视觉验证 cross-genre Layer 1 一致性
- **L-4** 视觉 spot-check test27 31 shots + ink 古风 BGM
  - 重点: char_001 月老 mythological + char_002 李慕白 棕色长袍 + char_003 苏璃 跨 31 shots Layer 1 一致

### 🟡 可选 (Founder 决定时机)
- **TASK-WAVE-10-DEPLOY-VPS** — DevOps 第 3 次部署 Wave 10 到 VPS
  - Wave 10 commit 3faf585 + 28e33a7 改了 app/ (AI-ML 4 const + Backend wire), 需 VPS rebuild
  - e938eaa 只改 tests/ — VPS 不需 (test 不进 production container)
  - 0204b8c + 0ad9beb + 4e4a4cf + d02e14b 都只是文档/工具 — VPS 不需
  - 实际 VPS 需 push 4 commit 但只 rebuild api (含 3faf585 + 28e33a7)
- **CLAUDE.md L210/L241/L283 同步** — Founder 改 "传入仅 fullbody" → "smart selection" (AI-ML P2-2 verify 发现过时)

### ✅ 已完成 (5/22 + 5/23, 累计 10 commit)

**5/22**:
- TASK-T22-NEW-10-PORTRAIT-LAYER1-WIRE ✅ (89bcfc7, Wave 9 portrait Layer 1)
- TASK-T22-NEW-10-FULLBODY-LAYER1-WIRE (DEC-049-3) ✅ (1629332, Wave 9.1 fullbody Layer 1)
- TASK-WAVE-9-TESTER-INDEPENDENT-BASELINE ✅ (c570c2d, 623/623 PASS)
- TASK-SECRET-LEAK-REMEDIATION ✅ Step 1-5 (filter-repo + force push)
- Wave 7+8 ✅ 6 task 全闭环

**5/23 Wave 10**:
- **TASK-GEMINI-KEY-ROTATE-AFTER-GOOGLE-REVOKE** ✅ PM 自做 5 min (Founder Google Cloud 生成第 3 把 + 私聊 + PM sed .env + verify md5 + API 200)
- **TASK-T22-NEW-1-TEST-ISOLATION-EXTENDED** (P2-1) ✅ Tester e938eaa (44 PASS, 27 errors → 0)
- **Stage 5 portrait/fullbody verify** (P2-2) ✅ AI-ML 3faf585 (= by-design RIM smart selection)
- **TASK-WAVE-10-UNKNOWN-CHARACTER-TYPE-WARN** (P3-1) ✅ AI-ML 3faf585 + Backend 28e33a7 接力 (CHARACTER_FIELD_PRESERVATION_RULES + deep-merge)
- **TASK-WAVE-10-STORYBOARD-ASPECT-RATIO** (P3-2) ✅ AI-ML + Backend (ASPECT_RATIO_FIDELITY_RULES + project_aspect_ratio 透传)
- **TASK-WAVE-10-RIM-LOGGER-UNIFY** (P3-3) ✅ AI-ML (xuhua 统一)
- **TASK-WAVE-10-SEEDREAM-CHARS-COUNT** (P3-4) ✅ AI-ML (CHARACTER_COUNT_FIDELITY_RULES 禁矛盾措辞)
- **TASK-WAVE-10-KEY-PROPS-CONSTRAINT** (P3-5) ✅ AI-ML (KEY_PROPS_CONSTRAINT_RULES MAX 3 × 50 char)
- **L-1 DEC-050 finalize SECRET_HANDLING_PROTOCOL** ✅ PM 0204b8c (5 部分)
- **L-2 mysql memory verify** ✅ PM 0204b8c (memory 标 ✅ 已用阿里云 MySQL)
- **Layer 0 SECRET SCANNER** ✅ PM 0ad9beb (4 模式拦截, 实测 verify)

### 🟢 P3 长期 (Wave 11+ 待修)
- **TASK-WAVE-11-MYSQL-POOL-PRE-PING-RELIABILITY** (5/23 19:48 Founder dashboard 实测发现)
  - 现象: backend idle ~1h 后 Founder GET /api/projects/ → 500 (pymysql.err.OperationalError 2013 'Lost connection during query'), 浏览器 NETWORK_ERROR TypeError Failed to fetch 131s 超时
  - 自动恢复: 第 2 次调用 backend 已 reconnect (SQLAlchemy pool_pre_ping 工作)
  - 影响: 用户 idle 后第 1 次操作可能 500 + 浏览器 131s 卡死 = 极差体验
  - 待查 + 修法:
    1. SQLAlchemy `create_async_engine(pool_pre_ping=True, pool_recycle=3600)` 是否已配 (推测没有)
    2. 加 connection-level retry middleware (FastAPI middleware) 自动 retry 1 次 transient MySQL error
    3. 或/和: 加 frontend retry on NETWORK_ERROR (一次失败重发一次, 比 131s 超时友好)
  - 文件: `app/database.py` (engine 配置) + `app/main.py` (middleware) + `frontend/src/lib/api.ts` (apiFetch retry)
- **TASK-WAVE-11-LP-IMAGE-LCP-PRIORITY** (5/23 17:50 Founder 测试发现, "之后要修别忘了")
  - 现象: Next.js dev console warn `Image with src "/comics/story-a/shot_01.png" was detected as the Largest Contentful Paint (LCP). Please add the "priority" property if this image is above the fold.`
  - URL: localhost:3000/ (LP 主页, above the fold)
  - 不阻塞功能, 但影响首屏加载性能 (LCP 指标)
  - 修法: 找 LP 主页 `<Image>` 组件用 `/comics/story-a/shot_01.png` 的, 加 `priority` prop
  - 文件可能在: `frontend/src/app/page.tsx` 或 `frontend/src/components/landing/*`

### 🔮 长期 (memory + Phase 6+)
- `project_mysql_migration.md` — ✅ 已完成 5/23 17:00 (memory 已 update)
- `project_schema_humanoid_fallback_remaining.md` — Wave 8 T22-NEW-9 已根治, memory 可标 ✅
- `project_confirm_outline_not_wired.md` — Wave 8 T22-NEW-8 验证已实现, memory 可标 ✅
