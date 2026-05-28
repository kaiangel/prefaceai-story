# TEST30《灯笼与萤火》全维度深度回溯

> **日期**: 2026-05-28 凌晨 06:00 - 08:30
> **写作时**: 2026-05-28 08:35
> **作者**: PM (Opus 4.7)
> **测试上下文**: VPS 真机 e2e (prefaceai.mov), 隐身窗口登录, 跨海访问 (Founder 国内 → VPS 107.148.1.199 境外)
> **故事**: 《灯笼与萤火》 — ink 水墨风 / 3min 中篇 / 3 角色 (老灯笼 / 萤火群 / 祠堂)
> **Pipeline 总耗时**: 3840.2s (~64 min, 不含 PM debug 时间)
> **Founder 角色**: 真机用户体验 + bug 挑战
> **本次目的**: 验证 5/27 DEC-054 P0 ping bug 根治 + 5/28 dev/prod parity 全栈对齐

---

## A. 测试结果总览

| 维度 | 状态 |
|---|---|
| Pipeline 5+1 stage e2e 全跑通 | ✅ Stage 1→2→3→4→4.5→5→6 全 ✅ |
| 20 shot 全部生成 + 落盘 | ✅ shot_01.png 到 shot_20.png 全在 |
| 3 角色 portrait + fullbody | ✅ 全生成 (萤火群单只问题除外) |
| BGM (Mureka, ink 风格) | ✅ 176.64s, 切尾水印 + 静音 QA pass |
| DB 写入 (project_chapters + chapter_scene_images) | ✅ storyboard_json 42KB / 20 行 image rows |
| 5/27 P0 ping bug 已根治 | ✅ 全程 0 OperationalError / 0 ping TypeError |
| **新暴露 bug / 问题数量** | **15 个** (按主题分 5 批次) |
| **本轮新建/修复 dev/prod parity gap** | **4 个 P0** (SKIP / ARK / IMAGE_GEN_PROVIDER + PROMPT_FORMAT / Nginx /static/) |

---

## B. 全部 15 个问题总览表 (按主题分组)

| # | 批次 | 问题 | 当前状态 | 优先级 | 修复工作量 |
|---|---|---|---|---|---|
| 1 | dev/prod parity | `.env.production` 误开 `SKIP_IMAGE_GENERATION=true` | ✅ 已修 06:20 | P0 | 5 min (sed + recreate) |
| 2 | dev/prod parity | `.env.production` 完全缺 `ARK_API_KEY` (Seedream 鉴权失败) | ✅ 已修 06:45 | P0 | 5 min (append) |
| 3 | dev/prod parity | `.env.production` 缺 `IMAGE_GEN_PROVIDER` + `PROMPT_FORMAT` (parity 红线) | ✅ 已修 06:45 | P0 | 2 min (append) |
| 4 | dev/prod parity | Nginx 配置缺 `location /static/` proxy | ✅ 已修 07:12 (Founder sudo) | P0 | 10 min |
| 5 | portrait 重生 | Regenerate-portrait endpoint 没传 portrait_ref (Adjust 有传) | 🟡 待修 | P1 | 15 min |
| 6 | portrait 重生 | AdjustCharacter LLM prompt 缺"保留数量"约束 | 🟡 待修 | P1 | 30 min |
| 7 | portrait 重生 | Seedream prompt 群体 token 强化缺失 | 🟡 待修 | P1 | 20 min |
| 8 | 性能 | 🚨 **大图 2.85MB × 20 = 60MB, 跨海 142KB/s, 单张 20s** | 🚨 待修 | **P0** | 1h thumbnail + 30min 预加载 |
| 9 | 性能 | scenes 页场景参考图同样慢 | 🚨 待修 | **P0** | 复用 #8 方案 |
| 10 | 性能 | 大图 WebP 压缩 (PNG 2.85MB → WebP ~600KB) | 🟡 待修 | P1 | 1h |
| 11 | ShotValidator | chars 检测对群体角色 false positive (萤火虫群 chars=9/2 → 4/2 多次 retry) | 🔵 已知限制 | P2 | 2h (DEC-053 延伸) |
| 12 | ShotValidator | 极复杂 prop 描述 SeeDream 出不来 (D3-C lenient force-save) | 🔵 已知限制 | P2 | 2h prompt 工程 |
| 13 | 前端 wire | generating 页 image src 用错路径 `/api/projects/.../images/` (应 `/static/outputs/.../images/`) | 🟡 待修 | P2 | 30 min |
| 14 | PM 自查 | PM 多次误判 "又是 dev/prod parity" — 实际 portrait 重生是产品设计差距 | 📌 教训 | — | — |
| 15 | PM 自查 | PM 多次绕路诊断 (让 Founder F12 / sudo / ssh, 实际可自查) | 📌 教训 | — | — |

**已修 4 项 (全部 dev/prod parity 主修复) + 待修 7 项 (5 个 P0/P1 代码层 + 2 个 PM 自查教训) + 4 项 P2 / 已知限制**

---

## C. 批次 1: Dev/Prod Parity 4 处 P0 连环触发 (已修)

### 共同根因 + 教训

**根因**: 5/27 DEC-054 工作时, PM 只盯 **DB 栈** parity (SQLAlchemy / asyncmy / PyMySQL pin), 没系统扫 **`.env` keys / Nginx 反代 / 静态文件 serving 链路 / 容器化 vs 本地服务启动方式** 等其他 10 维度。**今晚 4 只哑雷连环暴露**:

1. **当 SKIP=true 关掉时, ARK_API_KEY 缺暴露**
2. **当 ARK_API_KEY 修好 portrait 真生成时, Nginx /static/ 缺暴露**
3. 每修一个又看到下一个

**Founder 反应**: 严厉提醒 "全维度毫无遗漏要本地一致或对齐 这点那么难吗" → PM 派 Explore very-thorough 做 11 维度 audit + 锁进 DEC-055 + Deploy SOP。

---

### 问题 #1 — `SKIP_IMAGE_GENERATION=true` 误开

**现象** (06:08-06:20):
- Founder VPS test30《灯笼与萤火》到 /characters 页面**三个角色图全部"图片加载失败"**
- Pipeline 日志显示 `generate_images=True` 但 **0 portrait / 0 Seedream call / 0 png 落盘**
- e48baa8a 这个项目最终废弃, 用户卡 R4-1 等用户确认角色 (但看不到图)

**根因深挖 (5 维度铁律核实)**:

1. **容器内 ACTUAL 代码**: `pipeline_orchestrator.py:598-599` 条件 gate
   ```python
   # UX-1: Stage 2 后立即为每个角色生成 portrait（肖像）
   if generate_images and not settings.SKIP_IMAGE_GENERATION:
       print("\n--- UX-1: 生成角色肖像（portrait）---")
   ```
2. **完整调用链路追踪**:
   ```
   .env.production: SKIP_IMAGE_GENERATION=true
     → settings.SKIP_IMAGE_GENERATION = True (docker exec python3 实证)
     → Pipeline L598 gate: True and not True → False
     → 整个 portrait 代码块 silently skip (0 Layer 1 inject / 0 Seedream call / 0 portrait png)
   ```
3. **历史证据**: VPS `output/a3966a40-*/` 确有旧 portrait/shot png (~3MB 大小) — 说明 SKIP **不是一直** True, 某时点被改了 (推测早期 infra 测试时关图省 API 费, 忘记关回)
4. **PM 盲区透明承认**: test29 e2e 后看到 VPS 仅 1 个 output 目录, PM 归因 "其他 35 个 local-origin", 没追 "为什么 VPS 36 项目里只 1 个有图" → 那时该挖到 SKIP 模式, 漏了, 今天 test30 才暴露
5. **.env.production 其他 kill switch 排查**: TEXT_ONLY/MOCK/DISABLE 排查全空, **SKIP 唯一 boolean 杀手**

**Ben 维度核查**: ✗ 不涉契约/共享DB/公网内网/DB-infra (纯本机 feature toggle), Founder 决策暂不通知 Ben。

**修复 (commit-less, .env 不入 git)**:
```bash
ssh trader@107.148.1.199
cp .env.production .env.production.bak-$(date +%s)
sed -i 's/^SKIP_IMAGE_GENERATION=true$/SKIP_IMAGE_GENERATION=false/' /opt/xuhua-story/.env.production
docker compose up -d --force-recreate api
docker exec docker-api-1 python3 -c 'from app.config import settings; print(settings.SKIP_IMAGE_GENERATION)'
# → False ✅
```

**最佳预防方案**: Deploy SOP 强制 11 维度检查 (DEC-055), 包括 .env 关键 boolean (SKIP_/MOCK_/TEXT_ONLY/DISABLE_) 部署前 grep + 容器内 Python 实证。

---

### 问题 #2 — `ARK_API_KEY` 完全缺失

**现象** (06:45):
- SKIP 修后 Stage 2 完成 → portrait UX-1 块**真进了**
- `[ReferenceImageManager] Layer 1 injected for portrait` ✅
- `[ImageGenerator] generate_image → Seedream dispatch (D.17 单模型) refs=0` ✅
- **但 3 张全部 WARNING `ARK_API_KEY not set` fail**:
  ```
  WARNING [Pipeline] UX-1: 老灯笼 portrait 生成失败: ARK_API_KEY not set
  WARNING [Pipeline] UX-1: 萤火群 portrait 生成失败: ARK_API_KEY not set
  WARNING [Pipeline] UX-1: 最后一萤 portrait 生成失败: ARK_API_KEY not set
  ```
- eb57a524 这个项目也废弃 (R4-1 等用户确认, 但 portrait 没图)

**根因深挖 (4 路实证)**:

1. **.env.production grep**: **0 行 ARK_API_KEY** — 文件里只有 TTS 用的 `VOLCENGINE_*` (API_KEY / ACCESS_KEY 都是 TTS 用的, 不是 Seedream)
2. **容器实际 env**: `docker exec env | grep ARK_` → **0 个 ARK_** — Seedream 调用读不到
3. **5/28 06:20 备份对比**: 备份里也无 — 不是 PM 误删的, 是**一直就没配过**
4. **报错链路**:
   ```python
   # app/services/seedream_generator.py:641
   api_key = os.getenv("ARK_API_KEY", "").strip()
   if not api_key:
       return {"success": False, "error": "ARK_API_KEY not set"}
   
   # app/services/image_generator.py:653
   if settings.IMAGE_GEN_PROVIDER == "seedream":
       # 双路径都依赖 env: os.getenv + settings.ARK_API_KEY
   ```

**为什么本地正常 VPS 炸**:
- ARK_API_KEY 是字节火山**方舟新版** (Seedream API) env, 本地 `.env` 有, VPS `.env.production` 从未加过
- 之前 SKIP=true 掩盖, 今晚 SKIP 修复后第二只哑雷暴露

**Ben 维度核查**: ✗ 不涉契约/共享 DB/公网内网/DB-infra (是第三方 API key), 属 production env 改动, Founder 决策暂不通知 Ben (备注: Ben 可能不知道 VPS .env.production 从未配过 ARK_API_KEY, 建议 deploy SOP 加上 Ben 复核 .env keys 完整性)。

**修复 (本地 cat → ssh stdin 安全注入, value 不出现在 chat)**:
```bash
{
  grep '^ARK_API_KEY=' .env
  echo 'IMAGE_GEN_PROVIDER=seedream'
  echo 'PROMPT_FORMAT=b_prime'
} | ssh trader@107.148.1.199 'cat >> /opt/xuhua-story/.env.production'
docker compose up -d --force-recreate api
```

**真鉴权实证**:
```python
# 容器内 Python 测试
httpx.post("https://ark.cn-beijing.volces.com/api/v3/images/generations", 
           headers={"Authorization": f"Bearer {ark_key}"},
           json={"model": "doubao-seedream-5-0-260128", "prompt": "test", "size": "512x512"})
# → HTTP 400 "InvalidParameter: size must be at least 3686400 pixels"
# 这是参数层错误, 鉴权层已通过 ✅ + Seedream 服务返回 request id ✅
```

**最佳预防方案**:
- **#A Deploy SOP**: 部署前 `diff <(grep '^[A-Z]' .env | cut -d= -f1) <(grep '^[A-Z]' .env.production | cut -d= -f1)` — 任意 key 名差异立即报警
- **#B 容器启动时 sanity check**: 在 `app/main.py` 启动 banner 加 `for key in ['ANTHROPIC_API_KEY','GEMINI_API_KEY','ARK_API_KEY','OPENAI_API_KEY','MUREKA_API_KEY','VOLCENGINE_API_KEY','DATABASE_URL']: assert getenv(key), f"{key} missing"` — 容器启动直接崩, deploy 前发现而不是用户测试时发现

---

### 问题 #3 — `IMAGE_GEN_PROVIDER` + `PROMPT_FORMAT` parity 红线

**现象**: 这两项 config.py 有默认值兜底 (`IMAGE_GEN_PROVIDER='seedream'` / `PROMPT_FORMAT='b_prime'`), 无实质功能影响, 但 `.env.production` 明文不齐 = dev/prod parity 红线破。

**根因**: 同问题 #2 — `.env.production` 从未与本地 `.env` 完全同步, parity 工作只盯 DB 栈。

**修复**: 与 #2 同批 append (3 行一起加)。

**为什么也是 P0**: Founder 明确说 "毫无遗漏且全面具体清晰细致的要和本地一致或者对齐", 即使 config 兜底能 work, parity 红线也必须守。

---

### 问题 #4 — Nginx 配置缺 `location /static/` proxy

**现象** (07:00-07:12):
- ARK_API_KEY 修后, 3 张 portrait 真生成成功 (Seedream Layer 1 inject ✅)
- VPS 容器内 `/app/output/.../character_refs/char_001_portrait.png` 2.96MB 真落盘 ✅
- 容器内 `curl localhost:8000/static/outputs/.../char_001_portrait.png` = **200** ✅
- **但外部 `curl https://prefaceai.mov/static/.../char_001_portrait.png` = 404 HTML (27KB)** ❌
- /characters 页第三次 "图片加载失败" — Founder 严重不满

**根因深挖**:

1. **VPS Nginx 在 host 上** (非容器), 配置 `/etc/nginx/sites-enabled/prefaceai-mov`
2. **完整 location 块**:
   ```nginx
   location /api/    → proxy_pass http://127.0.0.1:8000  (api 容器)
   location /        → proxy_pass http://127.0.0.1:3000  (Next.js 容器, default catch-all)
   location /_next/static/ → proxy_pass http://127.0.0.1:3000  (Next.js 静态)
   # ❌ 没有 location /static/ — 这就是问题
   ```
3. **走向**: `/static/outputs/*` 请求落到 default `location /` 转给 Next.js, Next.js 不认识返 404 HTML (27KB error page)
4. **为什么 test29 没暴露**: test29 是 Founder 在**本地**测的 e2e (走 localhost:8000 + uvicorn 直 serve 静态); **VPS 一直 SKIP=true 没真生过图**, `/static/*` Nginx serving 链路从未被验证过 — 这是个**沉睡哑雷**

**Ben 维度**: ✓ host Nginx 反向代理是基础设施层, 偏 Ben 域。当下 Founder 自己 sudo 改, 没通知 Ben。

**修复 (Founder 用 `su -` 切 root 后操作)**:
```bash
# PM 提前把新配置写到 /tmp/prefaceai-mov.new (trader 权限, 不需要 sudo)
cat > /tmp/prefaceai-mov.new << 'NGXEOF'
# ... 原配置 ...
location /static/ {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    expires 1h;
    add_header Cache-Control "public, max-age=3600";
    client_max_body_size 50m;
}
# ... 其他原配置 ...
NGXEOF

# Founder ssh + su - + 3 行:
sudo cp /tmp/prefaceai-mov.new /etc/nginx/sites-enabled/prefaceai-mov
sudo nginx -t  # → syntax is ok + test is successful ✅
sudo systemctl reload nginx
```

**真验实证**:
```bash
curl -I https://prefaceai.mov/static/outputs/943a4f2d-.../character_refs/char_001_portrait.png
# → HTTP 200, Content-Type: image/png ✅
```

**最佳预防方案**:
- **#A Deploy SOP**: 部署前 `grep 'app.mount' app/main.py` 列出所有 FastAPI StaticFiles mount 路径, 跟 Nginx 配置 location 块比对, 任何 mount path 没对应 nginx location 立即报警
- **#B 静态 mount 文档化**: 加 `docs/STATIC_MOUNTS_AND_NGINX_LOCATIONS.md` 持续维护
- **#C 部署集成测试**: 部署后自动 `curl -I /static/outputs/...test.png` 抽测, 非 200 阻止部署成功

---

## D. 批次 2: Portrait 重生 + AdjustCharacter LLM 缺陷 (待修)

### 共同背景

Founder 测试时改萤火群描述 "黄绿色冷光 → 蓝绿色冷光" 点重新生成, 期望"只改光颜色, 其他保持群体性"。但新 portrait 出来变**单只萤火虫** (不是群)。

PM 派 Explore very-thorough 做 5 维度地毯式审查 (前端 UI / 后端 endpoint / LLM prompt / TEAM_CHAT 历史 / Seedream API), 锁定根因。

---

### 问题 #5 — Regenerate-portrait endpoint 没传 portrait_ref

**铁证**: 同一项目里**两个 endpoint 行为分裂**:

| Endpoint | 文件:行号 | 传 portrait_ref | 行为 |
|---|---|---|---|
| **Adjust endpoint** `POST /characters/{id}/adjust` | `app/api/projects.py:1557` | ✅ **真传** `portrait_ref=_existing_portrait_pil` | Seedream 拿旧 portrait 锁脸 (identity) |
| **Regenerate-portrait endpoint** `POST /characters/{id}/regenerate-portrait` | `app/api/projects.py:1852` | ❌ **没传** | Seedream 纯文生图, identity 漂移 |

**`generate_character_reference` 函数 (`app/services/reference_image_manager.py:82`) 明确支持 portrait_ref 参数**:
```python
async def generate_character_reference(
    self,
    character: Dict[str, Any],
    project_style: ProjectStyleConfig,
    image_generator,
    ref_type: str = 'fullbody',
    portrait_ref: Optional[Image.Image] = None,  # ← 函数签名支持
    aspect_ratio: str = "2:3",
) -> Dict[str, Any]:
    # Wave 10 / RISK-T16-2: portrait regenerate 时也传原 portrait 作 ref,
    # Seedream 把原 portrait 当 ground truth → identity 一致 + 只调整 prompt 改的字段
    reference_images = [portrait_ref] if portrait_ref else None
```

**历史时间线**:
- 5/14 (Wave 11.1, T17-9 P0): Adjust 端点同步版本补 portrait_ref ✅
- 5/24 (Wave 12 P2-1): Adjust 端点异步化, 逐行迁移保留 portrait_ref wire ✅
- 5/25 (Wave 13 #6): **Regenerate 端点异步化, 逐行迁移漏了 portrait_ref wire** ❌

**为什么 Founder 这次走 Adjust 还是变单只**:
- Founder 点的"调整"按钮 → 走 Adjust endpoint (有传 portrait_ref) ✅
- 但 Haiku LLM 改 description 时把"一群"丢了 → 见问题 #6
- 加上 Seedream prompt 缺群体 token 强化 → 见问题 #7
- portrait_ref 锁脸但**不锁群体构图** (Seedream API 行为)

**Ben 维度**: ✗ 纯 backend 代码 + 第三方 API 行为, 不涉契约/共享 DB/公网内网/DB-infra。

**最佳修复方案**:

#### Backend 修复 (P1, 派 Backend Sonnet 4.6 high, ~15 min)

`app/api/projects.py:1852` `_regenerate_portrait_core` 镜像 L1545-1562 模式补 portrait_ref:

```python
# 在 _regenerate_portrait_core 中, await _ref_manager.generate_character_reference 之前加:

# 读 existing portrait 作 reference (镜像 Adjust endpoint L1545-1562)
_outputs_root = os.path.abspath("output")
_char_refs_dir = os.path.join(_outputs_root, str(project.uuid), "character_refs")
_existing_portrait_path = os.path.join(_char_refs_dir, f"{char_id}_portrait.png")
_existing_portrait_pil = None
if os.path.exists(_existing_portrait_path):
    from PIL import Image as _PilImage
    _existing_portrait_pil = _PilImage.open(_existing_portrait_path).convert("RGB")

_portrait_result = await _ref_manager.generate_character_reference(
    character=target_char,
    project_style=_project_style,
    image_generator=_image_gen,
    ref_type="portrait",
    portrait_ref=_existing_portrait_pil,  # ✅ 补 wire
)
```

测试: dry-run 调 regenerate-portrait endpoint, verify VPS log `refs=1` 且新 portrait identity 保持。

---

### 问题 #6 — AdjustCharacter LLM prompt 缺"保留数量"约束

**根因**: `app/api/projects.py:1380-1426` 附近的 `_adjust_character_core` LLM prompt 构建 (Haiku, op="adjust_character"), 没显式约束 "保留原 description 中的数量修饰 (群/swarm/multiple/group/herd 等)"。

**LLM 行为**:
- 用户输入: "黄绿色冷光改成蓝绿色冷光" (5 字小改)
- Haiku 输出: 可能把整段 description 重写, 把"一群"丢失
- 实测: 新 description 中文还含 "一群", 但英文可能丢失数量 → Seedream 看英文 prompt 出单只

**Ben 维度**: ✗ 纯 prompt 工程, 不涉。

**最佳修复方案**:

#### AI-ML 修复 (P1, 派 AI-ML Opus default, ~30 min)

`app/api/projects.py:1426` 附近主 prompt 加 RULE CFP-3:

```
RULE CFP-3 (新增): PRESERVE NUMERICAL CONTEXT

If the original description contains quantity modifiers (e.g., "一群", "swarm of",
"multiple", "group of", "a flock", "herd of", "dozens of") AND the user's
adjustment does NOT explicitly request to change the quantity, you MUST
preserve the original quantity modifier in BOTH Chinese and English.

Example 1:
  Original: "一群夏夜的萤火虫，尾部发出柔和的黄绿色冷光。
             A swarm of summer night fireflies, tails emitting soft yellowish-green cool light."
  User adjustment: "把发色从黄绿改成蓝绿"
  ✅ Correct output: "一群夏夜的萤火虫，尾部发出柔和的蓝绿色冷光。
                      A swarm of summer night fireflies, tails emitting soft blue-green cool light."
  ❌ Wrong output: "一只夏夜的萤火虫，尾部发出柔和的蓝绿色冷光。
                    A single summer night firefly, tail emitting soft blue-green cool light."
  
Example 2:
  Original: "三个学生坐在教室。Three students sitting in classroom."
  User adjustment: "把书包颜色改成红色"
  ✅ Correct output: "三个学生坐在教室，背着红色书包。
                      Three students sitting in classroom with red backpacks."
```

测试: dry-run 萤火群 + 三人小组场景, 验证 Haiku 输出保留"一群" / "Three" 等数量。

---

### 问题 #7 — Seedream prompt 缺群体 token 强化

**根因**: `app/services/reference_image_manager.py:265 _build_portrait_prompt` 当 character 含 swarm/group/multiple 时, 没显式强化 prompt 中的群体 token, 导致 Seedream 文生图时单一角色 token 强度盖过群体描述。

**Ben 维度**: ✗ 纯 prompt 工程。

**最佳修复方案**:

#### AI-ML 修复 (P1, 派 AI-ML Opus default, ~20 min)

`reference_image_manager.py:265` `_build_portrait_prompt` 加群体检测 + token 强化:

```python
def _build_portrait_prompt(self, character, char_type, project_style):
    base_prompt = ...  # 现有逻辑
    
    # 群体角色 token 强化 (新增, 防 Seedream 出单只)
    desc = (character.get("description") or "") + " " + (character.get("description_en") or "")
    GROUP_KEYWORDS = ["一群", "群", "swarm", "group of", "multiple", "flock", "herd", "dozens", "many"]
    if any(kw.lower() in desc.lower() for kw in GROUP_KEYWORDS):
        group_prefix = (
            "GROUP COMPOSITION REQUIREMENT (MANDATORY):\n"
            "This subject is a GROUP/SWARM of multiple individuals, NOT a single one.\n"
            "Image must show 10-30+ individuals in flight/motion, dispersed across composition.\n"
            "DO NOT render as a single isolated subject — render as a collective.\n\n"
        )
        base_prompt = group_prefix + base_prompt
    
    return base_prompt
```

测试: dry-run 萤火群 portrait 重生, 验证 prompt 含 GROUP COMPOSITION 块 + Seedream 输出为群体。

---

## E. 批次 3: 用户体验性能 🚨 P0 (待修)

### 共同背景

Founder 看 preview 页 shot 列表, **点下一张 shot_02 出来要 10-20 秒**, shot_03 同样慢, 体验崩溃。本地 next dev mode 秒切, VPS 跨海慢一个数量级。

---

### 问题 #8 + #9 — 大图 2.85MB × 20 = 60MB / 跨海带宽 142KB/s

**铁证 (curl 实测)**:
```
shot_02.png 真实大小:    2,846,627 bytes (2.85 MB)
Cloudflare 已缓存:       cf-cache-status: HIT, age=1171s (~19min)
但实际下载耗时:           total=20.04s (第一次), 22.6s (第二次缓存)
有效带宽:                 ~142 KB/s
TLS appconnect:          2.23s
starttransfer (TTFB):    2.90s
```

**根因深挖**:

1. **Cloudflare 边缘节点**: cf-ray a02bd4a82cc29802-**NRT** (东京 Tokyo) — Founder 国内访问东京边缘, 跨海路由 + 丢包 + 带宽限制
2. **图大**: PNG 2.85MB 一张, Seedream 输出 1664×2218 高分辨率没压缩
3. **不是 CDN miss**: cf-cache-status: HIT 但仍然 20s → **纯带宽问题**, 不是缓存策略问题
4. **scene refs 同样慢**: 5 张场景参考图也是大 PNG, scenes 页加载也慢 (Founder 反馈)

**Ben 维度**: ✓ CDN 选择 + 大图压缩属 backend/infra 域。**应当通知 Ben** 一起讨论长期方案 (国内 CDN 选型 / 视频/图片 CDN 切换 / 大图压缩 pipeline)。

**最佳修复方案 (三层叠加)**:

#### 🚨 P0 — Backend 生成 thumbnail (派 Backend Sonnet 4.6 high, ~1h)

新增 Pipeline 步骤: shot 生成后立即生成 webp thumbnail (300-500KB), 命名 `shot_XX_thumb.webp`:

**代码位置**: `app/services/pipeline_orchestrator.py` Stage 5 shot 保存逻辑后 + `app/services/seedream_generator.py` 输出 hook

**实现**:
```python
# pipeline_orchestrator.py Stage 5 内, shot.png 保存后立即:
from PIL import Image
shot_pil = Image.open(shot_path)
thumb_size = (832, 1109)  # 半分辨率
shot_pil.thumbnail(thumb_size, Image.Resampling.LANCZOS)
thumb_path = shot_path.replace(".png", "_thumb.webp")
shot_pil.save(thumb_path, "WEBP", quality=80, method=6)
```

**前端**: StageD.tsx 默认显示 thumb, 点击放大才加载原图:
```tsx
<img
  src={toAbsoluteUrl(currentShot.imageUrlThumb || currentShot.imageUrl)}  // ← 优先 thumb
  loading="eager"
  onClick={() => setFullScreen(true)}  // 点击全屏才加载 imageUrl 原图
/>
```

**预期效果**: thumb ~300KB, 跨海 142KB/s → **2 秒以内切完**, 体验从 20s → 2s, **10x 提升**。

#### 🟡 P1 — Frontend 预加载相邻 shots (派 Frontend Sonnet 4.6 high, ~30 min)

`frontend/src/components/create/StageD.tsx` 加 useEffect 在当前 index 变化时悄悄预拉前后 2 张:

```tsx
useEffect(() => {
  // 预加载 currentIndex ± 2 范围内的 shots
  const preloadIndices = [
    currentIndex - 2, currentIndex - 1,
    currentIndex + 1, currentIndex + 2,
  ].filter(i => i >= 0 && i < shots.length);
  
  preloadIndices.forEach(i => {
    const url = shots[i]?.imageUrlThumb || shots[i]?.imageUrl;
    if (url) {
      const img = new Image();
      img.src = toAbsoluteUrl(url)!;  // 浏览器后台缓存
    }
  });
}, [currentIndex, shots]);
```

**预期效果**: 用户切到下一张时, 浏览器已经 prefetch, 显示即时秒切 (即使原图大也无感)。

#### 🟡 P1 — Backend WebP/AVIF 压缩 (派 Backend Sonnet 4.6 high, ~1h)

考虑生产环境同时输出 WebP 全分辨率 (用于点击放大), 而不是 PNG:
- PNG 2.85MB → WebP quality=85 → 约 600KB-1MB (3-5x 压缩)
- 浏览器 99% 支持 WebP

**Pipeline 改动**: Seedream 返回 PNG bytes 后, 同时保存 .png (原始) + .webp (压缩), `image_url` 字段优先返 .webp。

#### 🔵 P2 — CDN 国内化 (派 DevOps + Ben 讨论, 1-2 day)

替换 Cloudflare → 阿里云 CDN / 腾讯云 COS CDN (国内节点更近, 跨海延迟根治), 需要 ICP 备案 / 域名国内解析。**长期方案, 内测后排期, Founder 决定时机**。

---

### 性能问题 #9 — Scenes 页场景参考图同样慢

**根因**: 与 #8 相同, 5 张 scene_ref 也是大 PNG, 走同一条慢链路。

**修复**: 复用 #8 thumb / 预加载 / WebP 三件套, **scene_ref 生成时同样输出 _thumb.webp**, 前端 scenes 页同样预加载。

---

## F. 批次 4: ShotValidator 检测限制 (P2 已知)

### 问题 #10 — chars false positive on 群体角色

**现象**:
- Shot 5 验证 chars=9/2 (期望 2 实际 9, 萤火虫群每只被识别为独立 char)
- Shot 7 chars=7/2 → retry → chars=4/2 → retry → chars=2/2 (D3-C lenient) finally pass
- 多次 retry, 浪费 Seedream cost + 时间

**根因**: ShotValidator chars 检测对**昆虫群/小动物群**不友好 (DEC-053 非人类支持的延伸盲区)。Validator 用 face detection / object detection, 把每只萤火虫当独立 char 数。

**最佳修复方案 (P2 已知限制, 内测后)**:

**派 AI-ML, ~2h**:
`app/services/shot_validator.py` chars 检测加群体角色特殊处理:
```python
# 当 expected character_type 包含 swarm/group/insect 时, chars 计数 collapse 到 1 (整个群算 1)
if any(c.get("character_type") in ["insect_swarm", "fish_school", "bird_flock"] for c in expected_chars):
    # group 视为 1 个 "聚合 character", validation pass 标准放宽
    actual_chars = min(actual_chars, len(expected_chars))  # 群算 1
```

---

### 问题 #11 — 极复杂 prop 描述 Seedream 出不来

**现象**:
- Shot 6: missing prop `"blurred stone floor of the ancestral hall, faint dust motes catching the new golden light"` 3 次 retry 全 FAIL → D3-C lenient force-save
- Shot 5/7: 类似问题

**根因**: prop 描述过于文学性 + 多层修饰 ("blurred stone floor" + "faint dust motes" + "new golden light" 三层叠加), Seedream 视觉化困难。

**最佳修复方案 (P2 已知限制, 内测后)**:

**派 AI-ML, ~2h** — 改 Stage 4 StoryboardDirector prompt:
- 限制 key_props 单条字符数 < 60 chars
- 拆分多层 prop 为多个独立 prop
- 加视觉化提示: "use single concrete visual element per prop"

---

## G. 批次 5: 杂项 & PM 自查 (待修 + 教训)

### 问题 #12 — 前端 generating 页 image src 用错路径

**现象** (07:58 ClientLog):
```
[UNCAUGHT] Resource load error: img src=https://prefaceai.mov/api/projects/.../images/shot_01.png
url=https://prefaceai.mov/create/.../generating
```

**根因**: generating 页面前端用了**错路径** `/api/projects/.../images/shot_01.png` 应该是 `/static/outputs/.../images/shot_01.png`。

**影响**: 只影响 generating 页面的封面预览, **不阻塞 e2e** (result 页用对了路径)。

**最佳修复方案 (派 Frontend, ~30 min)**:
搜 `frontend/src/app/create/[projectUuid]/page.tsx` 或 generating 页面相关组件, grep `/api/projects/.*images/` 找出错误 URL 拼接, 改成 `toAbsoluteUrl(imageUrl)` 走标准 URL 助手。

---

### 教训 #14 — PM 多次误判"又是 dev/prod parity"

**事件链**:
1. portrait 重生看到萤火群变单只
2. PM 第一反应: "又是 dev/prod parity, 类似 SKIP/ARK/Nginx 第 5 只哑雷"
3. PM 派 Explore very-thorough audit 11 维度
4. **结果**: 本地 vs VPS `app/api/projects.py` MD5 **完全一致** (33bc80fd...), 不是 parity 问题
5. **真根因**: Adjust endpoint 真传 portrait_ref 但 Haiku LLM 改 description 改太狠 + Seedream prompt 缺群体 token

**教训**:
- Founder 之前 3 次 parity 失职让 PM 形成**强归因偏见** ("又是 parity"), 但这次不对
- **铁律**: 假设新问题为 dev/prod parity 之前, **先 MD5 / git diff 比对实际代码**, 排除部署差异再深挖产品逻辑
- 透明承认: trust 失分是 PM 责任, 不能因为之前失职就把所有新问题套用同一归因

**memory 新增** (`feedback_carpet_review_first_check_md5.md`):
- 内容: 任何"看起来像 dev/prod 差异"的新 bug, 第一步必须先做 MD5/git diff 比对, 排除部署差异再深挖产品逻辑

---

### 教训 #15 — PM 多次绕路诊断

**事件链**:
1. **Nginx /static/ 修复时**: PM 让 Founder 自己 sudo 改 → Founder 不知道 trader 密码 → 卡 10min → PM 才发现 sudo 需要 root 密码 → 给 Founder 3 种方案最终走 `su -`
2. **shot 加载诊断时**: PM 让 Founder F12 看 Network → Founder 提醒"你不是有 ClientLog 实时通道吗" → PM 才用 docker logs 直接抓
3. **R4-3 confirm-scenes 时**: PM 误判 backend 没收到确认, 让 Founder F12 Network 验证 → 实际后端 30s 后已收到 (PM 监控窗口太早)

**教训**:
- PM 工具箱已有强大监控 (Monitor + Cron + Bash ssh + Explore agent), **不要默认让 Founder 切到 F12 工具**
- ClientLog 通道 (`layout.tsx:26` window.console hook → POST /api/_client_log) 是浏览器 console 的实时镜像, PM 应该第一时间从 docker logs 拉, 不让 Founder 手动 F12
- 监控查询窗口要包含 buffer (查 `--since 5m` 而非 `--since 2m`), 避免 race condition 误判

**memory 新增** (`feedback_pm_use_clientlog_not_f12.md`):
- 内容: 用户报告前端 bug 时, PM 第一时间用 docker logs grep [ClientLog], 不要默认让用户切 F12. ClientLog 通道 = 浏览器 console 实时镜像。

---

## H. 修复 Plan 派活清单

### 立即 (今晚或明天, 内测前必修)

| 优先级 | 项目 | 派 | Model | Effort | 工作量 |
|---|---|---|---|---|---|
| 🚨 P0 | #8 Backend 生成 thumbnail (webp 300KB) | Backend | Sonnet 4.6 | high | 1h |
| 🚨 P0 | #9 同上, scene_ref 也加 thumb | Backend | Sonnet 4.6 | high | (#8 同批) |
| 🟡 P1 | #5 Regenerate-portrait endpoint 补 portrait_ref wire | Backend | Sonnet 4.6 | high | 15 min |
| 🟡 P1 | #6 AdjustCharacter LLM prompt 加 RULE CFP-3 保留数量 | AI-ML | Opus | default | 30 min |
| 🟡 P1 | #7 Seedream portrait prompt 群体 token 强化 | AI-ML | Opus | default | 20 min |
| 🟡 P1 | #8 Frontend 预加载相邻 shots (StageD useEffect) | Frontend | Sonnet 4.6 | high | 30 min |
| 🟡 P1 | #10 Backend WebP 压缩 (PNG → WebP quality 85) | Backend | Sonnet 4.6 | high | 1h |
| 🟡 P2 | #13 前端 generating 页 image src 错路径修 | Frontend | Sonnet 4.6 | high | 30 min |

**总工作量**: ~4.5 hour (P0+P1 全部, 含 commit + 部署), 1 个晚上能搞完。

### 内测后排期 (P2)

| 项目 | 派 | 工作量 |
|---|---|---|
| #4 CDN 国内化 (阿里云 CDN / Cloudflare 中国 / 腾讯 CDN) | DevOps + Ben 讨论 | 1-2 day + ICP 备案 |
| #11 ShotValidator chars 群体角色处理 | AI-ML | 2h |
| #12 ShotValidator 复杂 prop 描述拆分 | AI-ML | 2h |

---

## I. 教训 + SOP 锁定

### DEC-055 落地: Canonical Dev/Prod Parity 11 维度 + Deploy SOP

详见 `.team-brain/decisions/DECISIONS.md` DEC-055 + 新建 `.team-brain/sops/DEPLOY_PARITY_CHECK.md` (含 11 维度强制 checklist)。

### PM 自查改进

1. **新归因优先看代码**: 任何"看起来像 parity"的 bug, 第一步 MD5/git diff 排除部署差异
2. **不要默认让 Founder F12**: ClientLog 通道是浏览器 console 实时镜像, PM 用 docker logs 直接抓
3. **监控窗口加 buffer**: 查 `--since 5m` 而非 `--since 2m`, 避免 race condition 误判
4. **sudo / hostlevel 操作前先验证权限**: trader 用户 sudoers 配置 / 系统密码 / SSH key 等环境因素提前问清, 不让 Founder 卡 10min

---

## J. 最终交付物

| 文档 | 状态 |
|---|---|
| 本回溯报告 `analysis/TEST30_FULL_RETROSPECTIVE_2026-05-28.md` | ✅ 本次写完 |
| `PENDING.md` 顶部 "Dev/Prod Parity 全维度根治批次" | ✅ 已加 |
| `PENDING.md` 顶部 "Portrait 重生 + AdjustCharacter LLM 修复批次" | ✅ 已加 |
| `PENDING.md` 顶部 "🚨 性能 P0 thumb + 预加载 + WebP 批次" | 🟡 本报告后立即加 |
| `DECISIONS.md` DEC-055 Canonical 11 维度 Parity 标准 | ✅ 已加 |
| `.team-brain/sops/DEPLOY_PARITY_CHECK.md` 11 维度 deploy 强制 checklist | 🟡 本报告后立即创建 |
| `pm-progress/current.md` / `completed.md` / `context-for-others.md` 三件套 | ✅ 已加 dev/prod parity 部分, 性能 P0 待补 |
| 4 个 memory 新增 (`feedback_carpet_review_first_check_md5` / `feedback_pm_use_clientlog_not_f12` / `feedback_portrait_regen_dual_endpoint_inconsistency` / `feedback_dev_prod_parity_full_audit`) | 🟡 本报告后立即创建 |
| `TEAM_CHAT.md` 整轮 test30 总结 | 🟡 本报告后立即追加 |

---

## K. 评分自查 (PM 自评)

| 维度 | 评分 | 说明 |
|---|---|---|
| Pipeline 5+1 stage 跑通能力 | 🟢 5/5 | 64min 完整 e2e, 0 ERROR |
| 5/27 P0 ping bug 实战根治验证 | 🟢 5/5 | 全程 0 ping TypeError |
| Dev/prod parity 系统性根治 | 🟡 3/5 | 4 处哑雷连环暴露, 但 DEC-055 + SOP 把根因锁住, 永不再犯 |
| 用户体验性能 | 🔴 2/5 | 大图慢 10-20s 严重影响体验, 内测前必修 (P0 已 plan) |
| Portrait 重生质量 | 🟡 3/5 | Adjust endpoint wire 正确, 但 LLM + Seedream 协作出单只 (内测前必修) |
| PM 工作质量 | 🟡 3/5 | 4 处 parity 失职 + 多次绕路诊断 + 误归因 — 透明承认, memory 锁教训 |

**整体**: 🟡 3.5/5 — Pipeline 真实可用, 但用户体验需打磨。今晚发现的 15 个问题中 4 已修 / 8 待修 / 3 PM 自查教训, 路线图清晰。

---

— PM (Opus 4.7, 2026-05-28 08:35)
